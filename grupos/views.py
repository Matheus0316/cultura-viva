from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views.generic import ListView, View
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.template.loader import render_to_string
from django.http import JsonResponse, HttpResponse
from grupos.models import Grupo
from grupos.forms import GrupoForm
from perfil.models import Perfil, Position, MembroGrupo
from django.db.models import Q, Case, When, IntegerField, Count
from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse
from utils.recomendacao.recomendador import RecomendadorCultural
from .tasks import send_group_status_email_task
from shop.models import Product, Service
from django.contrib.contenttypes.models import ContentType
from perfil.models import Address
from perfil.forms import AddressForm
from events.models import Event

class GrupoAddressUpdateView(LoginRequiredMixin, View):
    def get(self, request, id):
        grupo = get_object_or_404(Grupo, id=id)
        # Permissão: Superuser ou Líder
        membro = grupo.membros.filter(perfil=request.user.perfil).first()
        if not (request.user.is_superuser or (membro and membro.position and membro.position.position.lower() == 'líder')):
             messages.error(request, "Sem permissão.")
             return redirect('grupos:grupo_detail', id=id)
             
        address = grupo.address or Address()
        form = AddressForm(instance=address)
        return render(request, 'grupos/partials/address_form.html', {'form': form, 'grupo': grupo})

    def post(self, request, id):
        grupo = get_object_or_404(Grupo, id=id)
        membro = grupo.membros.filter(perfil=request.user.perfil).first()
        if not (request.user.is_superuser or (membro and membro.position and membro.position.position.lower() == 'líder')):
             return redirect('grupos:grupo_detail', id=id)

        address = grupo.address or Address()
        form = AddressForm(request.POST, instance=address)
        if form.is_valid():
            address = form.save()
            if not grupo.address:
                grupo.address = address
                grupo.save()
            messages.success(request, "Endereço do grupo atualizado!")
            if request.headers.get('HX-Request'):
                response = HttpResponse()
                response['HX-Refresh'] = 'true'
                return response
            return redirect('grupos:grupo_detail', id=id)
        return render(request, 'grupos/partials/address_form.html', {'form': form, 'grupo': grupo})

class GrupoListView(View):
    def get(self, request):
        page = request.GET.get('page', 1)
        # 1. Base Queryset com contagem de seguidores - Apenas Grupos Aprovados
        queryset = Grupo.objects.filter(status='APPROVED').annotate(num_seguidores=Count('seguidores'))

        # 2. Busca e Filtros
        search_query = request.GET.get('search', '')
        if search_query:
            queryset = queryset.filter(Q(name__icontains=search_query) | Q(description__icontains=search_query))

        category_filter = request.GET.get('category')
        if category_filter:
            queryset = queryset.filter(category=category_filter)

        # 3. Lógica de Título
        page_title = "Todos os Grupos"
        titles = {
            'PROJETO_SOCIAL': "Projetos Sociais",
            'COLETIVO': "Coletivos Culturais",
            'OFICINA': "Oficinas e Formação",
            'OUTRO': "Outras Iniciativas"
        }
        page_title = titles.get(category_filter, page_title)

        # 4. ORDENAÇÃO POR RECOMENDAÇÃO
        recommended_ids = []
        if request.user.is_authenticated:
            try:
                rec = RecomendadorCultural()
                recomendacoes = rec.recomendar(request.user.perfil.id)
                recommended_ids = [item['objeto'].id for item in recomendacoes if item['tipo'] == 'grupo']
            except Exception:
                pass

        if recommended_ids:
            preserved_order = Case(*[When(id=pk, then=pos) for pos, pk in enumerate(recommended_ids)],
                                 output_field=IntegerField())
            queryset = queryset.order_by(preserved_order, '-num_seguidores')
        else:
            queryset = queryset.order_by('-num_seguidores')

        # 5. Paginação
        paginator = Paginator(queryset, 12)
        page_obj = paginator.get_page(page)

        context = {
            'grupos' : page_obj,
            'page_title': page_title,
            'current_category': category_filter,
            'search_query': search_query,
        }

        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            html = render_to_string('grupos/partials/grupos.html', context)
            return JsonResponse({'html': html})

        return render(request, 'grupos/grupo_list.html', context)

class GrupoCreateView(View):
    def get(self, request):
        form = GrupoForm()
        context ={'form': form}
        return render(request, 'grupos/grupo_create.html', context)

    def post(self, request):
        form = GrupoForm(request.POST, request.FILES)

        if form.is_valid():
            grupo = form.save(commit=False)
            grupo.updated_by = request.user
            grupo.status = 'PENDING' # Novo grupo sempre pendente
            grupo.save()
            
            # Atribuição automática de Liderança
            position, _ = Position.objects.get_or_create(grupo=grupo, position='Líder')
            MembroGrupo.objects.create(
                perfil=request.user.perfil,
                grupo=grupo,
                position=position
            )
            
            messages.success(request, 'Solicitação de cadastro de grupo enviada com sucesso! Aguarde a aprovação da administração.')
            return redirect('grupos:grupo_list')
        else:
            messages.error(request, 'Erro ao criar o grupo. Verifique os dados e tente novamente.')
            return render(request, 'grupos/grupo_create.html', {'form': form})

class AdminApproveGrupoRequestView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser

    def post(self, request, pk):
        grupo = get_object_or_404(Grupo, pk=pk)
        grupo.status = 'APPROVED'
        grupo.save()

        # Enviar Email de Notificação (Celery Task)
        try:
            send_group_status_email_task.delay(grupo, 'APPROVED')
            messages.success(request, f'Grupo "{grupo.name}" aprovado e notificação enviada.')
        except Exception as e:
            messages.success(request, f'Grupo aprovado. (Erro ao notificar: {e})')

        return redirect('artistas:admin_request_list')

class AdminRejectGrupoRequestView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser

    def post(self, request, pk):
        grupo = get_object_or_404(Grupo, pk=pk)
        grupo_name = grupo.name
        try:
            send_group_status_email_task.delay(grupo, 'REJECTED')
        except Exception as e:
            messages.success(request, f'Grupo rejeitado. (Erro ao notificar: {e})')
        # Deletar ao invés de apenas marcar como rejeitado
        grupo.delete()

        messages.warning(request, f'A solicitação do grupo "{grupo_name}" foi recusada e os dados foram excluídos.')
        return redirect('artistas:admin_request_list')

class GrupoDetailView(View):
    def get(self, request, id):
        grupo = Grupo.objects.prefetch_related(
            'membros__perfil__user',
            'membros__position',
            'seguidores'
        ).get(id=id)

        seguidores = Perfil.objects.filter(seguindo__grupo=grupo)

        posts = grupo.posts.all().order_by('-created_at')

        is_following = False
        is_member = False
        is_leader = False

        if request.user.is_authenticated:
            perfil = request.user.perfil

            membro_info = grupo.membros.filter(perfil=perfil).first()
            if membro_info:
                is_member = True
                if membro_info.position and membro_info.position.position.lower() == 'líder':
                    is_leader = True

            if request.user.perfil in seguidores:
                is_following = True

        # Produtos e Serviços da Loja
        content_type = ContentType.objects.get_for_model(grupo)
        products = Product.objects.filter(content_type=content_type, object_id=grupo.id, is_active=True)
        
        service_qs = Service.objects.filter(content_type=content_type, object_id=grupo.id)
        if not (request.user.is_authenticated and (is_leader or request.user.is_superuser)):
            service_qs = service_qs.filter(is_active=True)
        services = service_qs

        context = {
            'grupo': grupo,
            'posts': posts,
            'is_following': is_following,
            'is_member': is_member,
            'is_leader': is_leader,
            'products': products,
            'services': services,
        }

        # Eventos do Grupo
        context['events'] = Event.objects.filter(grupo=grupo, active=True).order_by('date')

        return render(request, 'grupos/grupo_detail.html', context)


class GrupoEditView(View):
    def get(self, request, id):
        grupo = Grupo.objects.get(id=id)
        form = GrupoForm(instance=grupo)
        context = {'form': form, 'grupo': grupo}
        return render(request, 'grupos/grupo_edit.html', context)

    def post(self, request, id):
        grupo = Grupo.objects.get(id=id)
        form = GrupoForm(request.POST, request.FILES, instance=grupo)

        if form.is_valid():
            grupo = form.save(commit=False)
            grupo.updated_by = request.user
            grupo.save()
            return redirect('grupos:grupo_list')
        else:
            context = {'message': ['error', f'Erro ao editar o grupo. Verifique os dados e tente novamente. {form.errors}']}
            return render(request, 'grupos/grupo_edit.html', context)

class GrupoDeleteView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        grupo = get_object_or_404(Grupo, id=self.kwargs.get('id'))
        # Permitir se for Superusuário ou se for o Líder do grupo
        if self.request.user.is_superuser:
            return True
        
        membro = grupo.membros.filter(perfil=self.request.user.perfil).first()
        return membro and membro.position and membro.position.position.lower() == 'líder'

    def post(self, request, id):
        grupo = get_object_or_404(Grupo, id=id)
        try:
            grupo.delete()
            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

from post.forms import PostForm

class GrupoPostCreateView(View):
    def get(self, request, id):
        grupo = Grupo.objects.get(id=id)

        # Permission Check
        if not request.user.is_authenticated:
             return redirect('home:login')

        is_member = grupo.membros.filter(perfil__user=request.user).exists()
        if not (request.user.is_superuser or is_member):
             # Message or just redirect
             return redirect('grupos:grupo_detail', id=id)

        form = PostForm()
        context = {'form': form, 'grupo': grupo}
        return render(request, 'grupos/grupo_post_create.html', context)

    def post(self, request, id):
        grupo = Grupo.objects.get(id=id)

        if not request.user.is_authenticated:
             return redirect('home:login')

        is_member = grupo.membros.filter(perfil__user=request.user).exists()
        if not (request.user.is_superuser or is_member):
             return redirect('grupos:grupo_detail', id=id)

        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.grupo = grupo
            post.author = request.user.perfil
            post.save()
            return redirect('grupos:grupo_detail', id=id)
        else:
            context = {'form': form, 'grupo': grupo, 'message': ['error', f'Erro ao criar publicação. {form.errors}']}
            return render(request, 'grupos/grupo_post_create.html', context)

class GrupoDeliveryUpdateView(LoginRequiredMixin, View):
    def get(self, request, id):
        grupo = get_object_or_404(Grupo, id=id)
        membro = grupo.membros.filter(perfil=request.user.perfil).first()
        if not (request.user.is_superuser or (membro and membro.position and membro.position.position.lower() == 'líder')):
             messages.error(request, "Sem permissão.")
             return redirect('grupos:grupo_detail', id=id)
             
        from .forms import GrupoDeliveryForm
        form = GrupoDeliveryForm(instance=grupo)
        return render(request, 'grupos/partials/delivery_form.html', {'form': form, 'grupo': grupo})

    def post(self, request, id):
        grupo = get_object_or_404(Grupo, id=id)
        membro = grupo.membros.filter(perfil=request.user.perfil).first()
        if not (request.user.is_superuser or (membro and membro.position and membro.position.position.lower() == 'líder')):
             return redirect('grupos:grupo_detail', id=id)

        from .forms import GrupoDeliveryForm
        form = GrupoDeliveryForm(request.POST, instance=grupo)
        if form.is_valid():
            form.save()
            messages.success(request, "Configurações de frete do grupo atualizadas!")
            if request.headers.get('HX-Request'):
                response = HttpResponse()
                response['HX-Refresh'] = 'true'
                return response
            return redirect('grupos:grupo_detail', id=id)
        return render(request, 'grupos/partials/delivery_form.html', {'form': form, 'grupo': grupo})
