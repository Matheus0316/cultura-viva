from django.shortcuts import render, redirect
from django.views import View
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from perfil.forms import PerfilForm
from .tasks import send_email_reset_password
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from home.models import ChangePasswordToken
from django.utils import timezone


from django.db.models import Count
from artistas.models import Artista
from grupos.models import Grupo
from utils.recomendacao.recomendador import RecomendadorCultural

class IndexView(View):
    def get(self, request):
        # 1. Buscar candidatos básicos
        top_artistas_pool = list(Artista.objects.filter(status='APPROVED').annotate(
            num_seguidores=Count('seguidores')
        ).order_by('-num_seguidores')[:20])
        
        top_grupos_pool = list(Grupo.objects.filter(status='APPROVED').annotate(
            num_seguidores=Count('seguidores')
        ).order_by('-num_seguidores')[:20])
        
        # Filtros base
        user_id = request.user.id if request.user.is_authenticated else None
        seguindo_artistas_ids = set()
        seguindo_grupos_ids = set()
        
        if request.user.is_authenticated:
            try:
                perfil = request.user.perfil
                # IDs dos artistas e grupos que o usuário já segue
                # Usamos os related_names definidos nos modelos de Seguidor
                # artistas_seguindo vem de SeguidorArtista.perfil (related_name='artistas_seguindo')
                # seguindo vem de SeguidorGrupo.perfil (related_name='seguindo')
                seguindo_artistas_ids = set(perfil.artistas_seguindo.values_list('artista_id', flat=True))
                seguindo_grupos_ids = set(perfil.seguindo.values_list('grupo_id', flat=True))
            except Exception:
                pass

        # 2. Recomendação Personalizada
        artistas_recomendados = []
        grupos_recomendados = []

        if request.user.is_authenticated:
            try:
                perfil = request.user.perfil
                rec = RecomendadorCultural()
                recomendacoes = rec.recomendar(perfil.id)
                
                for item in recomendacoes:
                    obj = item['objeto']
                    if item['tipo'] == 'artista':
                        if obj.user_id != user_id and obj.id not in seguindo_artistas_ids and len(artistas_recomendados) < 4:
                            artistas_recomendados.append(obj)
                    elif item['tipo'] == 'grupo':
                        if obj.updated_by_id != user_id and obj.id not in seguindo_grupos_ids and len(grupos_recomendados) < 4:
                            grupos_recomendados.append(obj)
            except Exception:
                pass
        
        # 3. Aplicar Filtros Gerais (Excluir eu mesmo e quem já sigo)
        if user_id:
            top_artistas_pool = [a for a in top_artistas_pool if a.user_id != user_id and a.id not in seguindo_artistas_ids]
            top_grupos_pool = [g for g in top_grupos_pool if g.updated_by_id != user_id and g.id not in seguindo_grupos_ids]
        
        # 4. Fallback: Se a personalizada falhar ou for pouca, completar com os Tops filtrados
        if len(artistas_recomendados) < 4:
            for a in top_artistas_pool:
                if a not in artistas_recomendados and len(artistas_recomendados) < 4:
                    artistas_recomendados.append(a)
                    
        if len(grupos_recomendados) < 4:
            for g in top_grupos_pool:
                if g not in grupos_recomendados and len(grupos_recomendados) < 4:
                    grupos_recomendados.append(g)

        context = {
            'artistas_recomendados': artistas_recomendados,
            'grupos_recomendados': grupos_recomendados,
            'top_artistas': top_artistas_pool[:4],
            'top_grupos': top_grupos_pool[:4],
        }
        return render(request, 'index.html', context)

    def get_context_data(self, **kwargs):
        # Este método não será mais muito usado devido ao get customizado,
        # mas mantemos por compatibilidade se necessário.
        context = super().get_context_data(**kwargs)
        return context

class LoginView(View):

    def get(self, request):
        return render(request, 'login.html')

    def post(self, request):
        if 'login_attempts' not in request.session:
            request.session['login_attempts'] = 0

        if request.session['login_attempts'] >= 5:
            messages.error(request, ('error', 'Muitas tentativas de login. Por favor, tente novamente mais tarde.'))
            return render(request, 'login.html')

        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request=request, username=username, password=password)

        if user is not None:
            login(request, user)
            request.session['login_attempts'] = 0
            return redirect('home:index')
        else:
            request.session['login_attempts'] += 1
            messages.error(request, ('error', 'Nome de usuário ou senha inválidos.'))
            return render(request, 'login.html')


class LogoutView(View):
    def get(self, request):
        logout(request)
        messages.success(request, ('success', 'Você saiu da sua conta.'))
        return redirect('home:index')


class RegisterView(View):
    def get(self, request):
        form = PerfilForm()
        context = {'form': form}
        return render(request, 'register.html', context)

    def post(self, request):
        form = PerfilForm(request.POST, request.FILES)

        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, ('success', 'Cadastro realizado com sucesso!'))
            return redirect('home:index')

        messages.error(request, ('error', 'Por favor, corrija os erros abaixo.'))
        context = {'form': form}
        return render(request, 'register.html', context)


class SendChangePasswordEmailView(View):
    def post(self, request):
        email = request.POST.get('email')

        if email:
            if User.objects.filter(email=email).exists() is False:
                messages.error(request, ('error', 'Email não cadastrado.'))
                return render(request, 'login.html')
            messages.success(request, ('success', 'O email para alteração de senha foi enviado, verifique sua caixa de entrada.'))
            send_email_reset_password.delay(email)
        else:
            messages.error(request, ('error', 'Nenhum e-mail fornecido.'))

        return render(request, 'login.html')

class ChangePasswordView(View):
    def get(self, request, token):
        try:
            token_entry = ChangePasswordToken.objects.get(token=token)
        except ChangePasswordToken.DoesNotExist:
            messages.error(request, ('error', 'Token de alteração de senha inválido ou não encontrado.'))
            return render(request, 'login.html')

        if token_entry.created_at < timezone.now() - timezone.timedelta(hours=1):
            messages.error(request, ('error', 'Este link de alteração de senha expirou.'))
            return render(request, 'login.html')

        if token_entry.is_used:
            messages.error(request, ('error', 'Este link de alteração de senha já foi usado.'))
            return render(request, 'login.html')

        context = {'token': token}
        return render(request, 'change_password.html', context)

    def post(self, request, token):
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('new_password_confirm')

        if new_password != confirm_password:
            messages.error(request, ('error', 'As senhas não coincidem.'))
            context = {'token': token}
            return render(request, 'change_password.html', context)

        try:
            token_entry = ChangePasswordToken.objects.get(token=token)
            user = User.objects.get(email=token_entry.email)

            user.password = make_password(new_password)
            user.save()

            token_entry.is_used = True
            token_entry.save()

            messages.success(request, ('success', 'Senha alterada com sucesso! Você já pode fazer login.'))
            return redirect('home:login')

        except (ChangePasswordToken.DoesNotExist, User.DoesNotExist):
            messages.error(request, ('error', 'Token inválido ou usuário não encontrado.'))
            return redirect('home:login')


class ParocoView(View):
    def get(self, request):
        return render(request, 'paroco.html')
