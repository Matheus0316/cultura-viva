from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.core.paginator import Paginator
from django.db.models import Q
from django.template.loader import render_to_string
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse
from artistas.models import Artista
from .models import SeguidorGrupo, MembroGrupo, Perfil, Position, Address
from .forms import PerfilUpdateForm, AddressForm
from grupos.models import Grupo
from .tasks import send_custom_notification_email_task

class AddressListView(LoginRequiredMixin, View):
    def get(self, request):
        addresses = request.user.addresses.all().order_by('-is_main', '-created_at')
        return render(request, 'perfil/partials/address_list.html', {'addresses': addresses})

class AddressCreateView(LoginRequiredMixin, View):
    def get(self, request):
        form = AddressForm()
        return render(request, 'perfil/partials/address_form.html', {'form': form})
    
    def post(self, request):
        form = AddressForm(request.POST)
        if form.is_valid():
            address = form.save(commit=False)
            address.user = request.user
            
            if address.is_main:
                request.user.addresses.update(is_main=False)
            
            address.save()
            messages.success(request, "Endereço adicionado!")
            
            if request.headers.get('HX-Request'):
                response = HttpResponse()
                response['HX-Refresh'] = 'true'
                return response
                
            return redirect('perfil:profile_detail', id=request.user.perfil.id)
        return render(request, 'perfil/partials/address_form.html', {'form': form, 'errors': form.errors})

class AddressUpdateView(LoginRequiredMixin, View):
    def get(self, request, pk):
        address = get_object_or_404(Address, pk=pk, user=request.user)
        form = AddressForm(instance=address)
        return render(request, 'perfil/partials/address_form.html', {'form': form, 'address': address})
    
    def post(self, request, pk):
        address = get_object_or_404(Address, pk=pk, user=request.user)
        form = AddressForm(request.POST, instance=address)
        if form.is_valid():
            address = form.save(commit=False)
            
            if address.is_main:
                request.user.addresses.exclude(pk=pk).update(is_main=False)
                
            address.save()
            messages.success(request, "Endereço atualizado!")
            
            if request.headers.get('HX-Request'):
                response = HttpResponse()
                response['HX-Refresh'] = 'true'
                return response
                
            return redirect('perfil:profile_detail', id=request.user.perfil.id)
        return render(request, 'perfil/partials/address_form.html', {'form': form, 'address': address})

class AddressDeleteView(LoginRequiredMixin, View):
    def post(self, request, pk):
        address = get_object_or_404(Address, pk=pk, user=request.user)
        address.delete()
        messages.success(request, "Endereço removido.")
        return redirect('perfil:profile_detail', id=request.user.perfil.id)


class SeguirGrupoView(View):
    def get(self, request, grupo_id):
        grupo = Grupo.objects.filter(id=grupo_id).first()
        perfil = request.user.perfil
        if not grupo or not perfil:
            return redirect('grupos:grupo_list')

        seguindo, criado = SeguidorGrupo.objects.get_or_create(perfil=perfil, grupo=grupo)
        return redirect('grupos:grupo_detail', id=grupo_id)

class DeixarDeSeguirGrupoView(View):
    def get(self, request, grupo_id):
        grupo = Grupo.objects.filter(id=grupo_id).first()
        perfil = request.user.perfil
        if not grupo or not perfil:
            return redirect('grupos:grupo_list')

        SeguidorGrupo.objects.filter(perfil=perfil, grupo=grupo).delete()
        return redirect('grupos:grupo_detail', id=grupo_id)

class ProfileListView(View):
    def get(self, request, grupo_id=None):

        request.session['group_id'] = str(grupo_id)

        grupo = get_object_or_404(Grupo, id=grupo_id)
        is_lider = False
        if request.user.is_authenticated:
            try:
                membro_grupo = MembroGrupo.objects.get(perfil=request.user.perfil, grupo=grupo)
                if membro_grupo.position and membro_grupo.position.position.lower() == 'líder':
                    is_lider = True
            except MembroGrupo.DoesNotExist:
                if request.user.is_superuser:
                    is_lider = True
        # Se não for líder, não pode ver esta página de gerenciamento
        if not is_lider:
            return redirect('grupos:grupo_detail', id=grupo_id)

        # 2. Query Base (Membros OU Seguidores)
        profiles = Perfil.objects.filter(
            Q(grupos__grupo__id=grupo_id) | Q(seguindo__grupo__id=grupo_id)
        ).distinct().exclude(user=request.user).select_related('user')

        # 3. Aplicar Filtros
        filter_user = request.GET.get('filter', '')
        if filter_user == 'seguidor':
            profiles = profiles.filter(seguindo__grupo__id=grupo_id).exclude(grupos__grupo__id=grupo_id)
        elif filter_user == 'membro':
            profiles = profiles.filter(grupos__grupo__id=grupo_id).exclude(seguindo__grupo__id=grupo_id)

        # 4. Aplicar Busca
        search = request.GET.get('search', '')
        if search:
            profiles = profiles.filter(
                Q(user__username__icontains=search) |
                Q(name__icontains=search)
            ).distinct()

        # 5. Criar Mapa de Membros
        membros_do_grupo = MembroGrupo.objects.filter(grupo=grupo).select_related('position')
        membership_map = {membro.perfil_id: membro.position for membro in membros_do_grupo}
        # 6. Paginação
        page = request.GET.get('page', 1)
        paginator = Paginator(profiles, 10)
        page_obj = paginator.get_page(page)

        # 7. Anotar perfis da página com seu status de membro
        for profile in page_obj:
            profile.membership = membership_map.get(profile.id)

        # 8. Montar Contexto
        title = 'Membros e seguidores'
        subtitle = f'Gerenciando membros e seguidores do grupo {grupo.name}'

        context = {
            'profiles': page_obj,
            'title': title,
            'subtitle': subtitle,
            'is_lider': is_lider,
            'grupo': grupo,

            'filter_user': filter_user,
            'search': search,
        }
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            html = render_to_string('perfil/partials/profiles.html', context, request=request)
            return JsonResponse({'html': html})
        return render(request, 'perfil/profile_list.html', context)

class ProfileDetailVeiw(View):
    def get(self, request, id):
        perfil = get_object_or_404(Perfil, id=id)
        member_of = MembroGrupo.objects.filter(perfil=perfil)
        seguindo = SeguidorGrupo.objects.filter(perfil=perfil)
        context = {
            'perfil': perfil,
            'member_of': member_of,
            'seguindo': seguindo
        }

        # Endereços do usuário
        context['addresses'] = perfil.user.addresses.all().order_by('-is_main', '-created_at')
        
        return render(request, 'perfil/profile_detail.html', context)

class ProfileEditView(LoginRequiredMixin, View):
    def get(self, request, id):
        perfil = get_object_or_404(Perfil, id=id)
        if request.user != perfil.user and not request.user.is_superuser:
            return JsonResponse({'error': 'Não autorizado'}, status=403)
        
        form = PerfilUpdateForm(instance=perfil)
        context = {
            'perfil': perfil,
            'form': form,
        }
        return render(request, 'perfil/partials/profile_edit.html', context)
    
    def post(self, request, id):
        perfil = get_object_or_404(Perfil, id=id)
        if request.user != perfil.user and not request.user.is_superuser:
            return JsonResponse({'error': 'Não autorizado'}, status=403)
        
        form = PerfilUpdateForm(request.POST, request.FILES, instance=perfil)
        if form.is_valid():
            form.save()
            from django.http import HttpResponse
            response = HttpResponse()
            response['HX-Refresh'] = 'true'
            return response
        
        context = {
            'perfil': perfil,
            'form': form,
        }
        return render(request, 'perfil/partials/profile_edit.html', context)

class UpdateMembershipView(View):
    def get(self, request, perfil_id):
        if request.user.is_superuser or MembroGrupo.objects.filter(perfil=request.user.perfil, grupo=grupo).exist() and MembroGrupo.objects.filter(perfil=request.user.perfil, grupo=grupo).position.position.lower() == 'líder':
            perfil = get_object_or_404(Perfil, id=perfil_id)
            grupo_id = request.session.get('group_id')
            grupo = get_object_or_404(Grupo, id=grupo_id)

            membro_grupo, criado = MembroGrupo.objects.get_or_create(perfil=perfil, grupo=grupo)

            if criado:
                membro_grupo.position = Position.objects.get_or_create(grupo=grupo, position='Membro')[0]
                seguindo = get_object_or_404(SeguidorGrupo, perfil=perfil, grupo=grupo)
                seguindo.delete()
                membro_grupo.save()
            elif membro_grupo.position.position.lower() == 'líder':
                membro_grupo.position = Position.objects.get_or_create(grupo=grupo, position='Membro')[0]
                membro_grupo.save()
            elif membro_grupo.position.position.lower() == 'membro':
                membro_grupo.position = Position.objects.get_or_create(grupo=grupo, position='Líder')[0]
                membro_grupo.save()

            return redirect('perfil:profile_list', grupo_id=grupo_id)
        else:
            return redirect('grupos:grupo_detail', id=grupo_id)

class RemoverMembroView(View):
    def get(self, request, perfil_id):
        if request.user.is_superuser or MembroGrupo.objects.filter(perfil=request.user.perfil, grupo=grupo).exist() and MembroGrupo.objects.filter(perfil=request.user.perfil, grupo=grupo).position.position.lower() == 'líder':
            perfil = get_object_or_404(Perfil, id=perfil_id)
            grupo_id = request.session.get('group_id')
            grupo = get_object_or_404(Grupo, id=grupo_id)

            MembroGrupo.objects.filter(perfil=perfil, grupo=grupo).delete()
            SeguidorGrupo.objects.get_or_create(perfil=perfil, grupo=grupo)

            return redirect('perfil:profile_list', grupo_id=grupo_id)
        else:
            return redirect('grupos:grupo_detail', id=grupo_id)


class UserListView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser

    def get(self, request):
        users = User.objects.all().select_related('perfil', 'artista_profile').order_by('-date_joined')

        q = request.GET.get('q')
        if q:
            users = users.filter(
                Q(username__icontains=q) |
                Q(email__icontains=q) |
                Q(first_name__icontains=q) |
                Q(last_name__icontains=q)
            )

        paginator = Paginator(users, 20)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        context = {'users': page_obj}

        if request.headers.get('HX-Request'):
            return render(request, 'perfil/partials/user_list_results.html', context)

        return render(request, 'perfil/user_list.html', context)


class PromoteSuperuserView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser

    def post(self, request, user_id):
        target_user = get_object_or_404(User, id=user_id)

        if target_user == request.user:
             messages.error(request, "Você não pode alterar seu próprio status.")
             return redirect('perfil:user_list')

        target_user.is_superuser = not target_user.is_superuser
        if target_user.is_superuser:
            target_user.is_staff = True
            action = "promovido a Administrador"
        else:
            target_user.is_staff = False # Remove staff access as well
            action = "removido da Administração"

        target_user.save()

        # Email Notification (Celery Task)
        try:
            subject_title = 'Atualização de Status'
            message_text = f'Olá {target_user.username},\n\nSeu status na plataforma foi atualizado. Você foi {action}.'
            action_url = request.build_absolute_uri(reverse('home:index'))

            send_custom_notification_email_task.delay(
                target_user,
                subject_title,
                message_text,
                action_url,
                'Acessar Painel'
            )
        except Exception as e:
            print(f"Erro ao agendar email de status: {e}")

        messages.success(request, f"Usuário {target_user.username} {action}.")
        return redirect('perfil:user_list')


class CreateArtistFromAdminView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser

    def post(self, request, user_id):
        target_user = get_object_or_404(User, id=user_id)

        if hasattr(target_user, 'artista_profile'):
             messages.warning(request, "Este usuário já possui um perfil de artista.")
             return redirect('perfil:user_list')

        artist_name = target_user.get_full_name() or target_user.username

        Artista.objects.create(
            user=target_user,
            name=artist_name,
            status='APPROVED',
            category='MUSICA',
            bio=f"Perfil criado administrativamente."
        )

        # Email Notification (Celery Task)
        try:
            subject_title = 'Perfil de Artista Criado'
            message_text = f'Olá {target_user.username},\n\nUm perfil de artista foi criado e aprovado para sua conta pela administração.'
            action_url = request.build_absolute_uri(reverse('artistas:artista_dashboard'))

            send_custom_notification_email_task.delay(
                target_user,
                subject_title,
                message_text,
                action_url,
                'Acessar Painel do Artista'
            )
        except Exception as e:
             print(f"Erro ao agendar email de criação de artista: {e}")

        messages.success(request, f"Perfil de artista criado para {target_user.username}.")
        return redirect('perfil:user_list')

class RemoveArtistView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser

    def post(self, request, user_id):
        target_user = get_object_or_404(User, id=user_id)

        if not hasattr(target_user, 'artista_profile'):
             messages.warning(request, "Este usuário não possui um perfil de artista.")
             return redirect('perfil:user_list')

        target_user.artista_profile.delete()

        # Email Notification (Celery Task)
        try:
            subject_title = 'Perfil de Artista Removido'
            message_text = f'Olá {target_user.username},\n\nSeu perfil de artista foi removido pela administração.'
            action_url = request.build_absolute_uri(reverse('home:index'))

            send_custom_notification_email_task.delay(
                target_user,
                subject_title,
                message_text,
                action_url,
                'Ir para Início'
            )
        except Exception as e:
            print(f"Erro ao agendar email de remoção de artista: {e}")

        messages.success(request, f"Perfil de artista de {target_user.username} removido com sucesso.")
        return redirect('perfil:user_list')

class ToggleAcervoPermissionView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser

    def post(self, request, user_id):
        target_user = get_object_or_404(User, id=user_id)

        perfil = target_user.perfil
        perfil.can_add_acervo = not perfil.can_add_acervo
        perfil.save()

        status = "permitido" if perfil.can_add_acervo else "bloqueado"

        # Email Notification (Celery Task)
        try:
            subject_title = 'Permissão de Acervo'
            message_text = f'Olá {target_user.username},\n\nSua permissão para gerenciar itens do Acervo foi atualizada. Agora seu acesso está: {status.upper()}.'
            action_url = request.build_absolute_uri(reverse('post:acervo_list'))

            send_custom_notification_email_task.delay(
                target_user,
                subject_title,
                message_text,
                action_url,
                'Acessar Acervo'
            )
        except Exception as e:
            print(f"Erro ao agendar email de permissão de acervo: {e}")

        messages.success(request, f"Permissão de acervo de {target_user.username} agora está definida como: {status}.")
        return redirect('perfil:user_list')
