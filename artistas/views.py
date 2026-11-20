from django.views.generic import ListView, DetailView, CreateView, UpdateView, TemplateView
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.mixins import UserPassesTestMixin
from django.views import View
from django.template.loader import render_to_string
from .models import Artista, SeguidorArtista
from .forms import ArtistaRequestForm, ArtistaUpdateForm
from post.models import Post
from post.forms import PostForm
from events.models import Event
from events.forms import EventForm
from django.db.models import Q, Case, When, IntegerField, Count
from grupos.models import Grupo
from utils.recomendacao.recomendador import RecomendadorCultural
from .tasks import send_artist_status_email_task
from shop.models import Product, Service
from django.contrib.contenttypes.models import ContentType
from perfil.models import Address
from perfil.forms import AddressForm

class ArtistaAddressUpdateView(LoginRequiredMixin, View):
    def get(self, request):
        artista = get_object_or_404(Artista, user=request.user)
        address = artista.address or Address()
        form = AddressForm(instance=address)
        return render(request, 'artistas/partials/address_form.html', {'form': form, 'artista': artista})

    def post(self, request):
        artista = get_object_or_404(Artista, user=request.user)
        address = artista.address or Address()
        form = AddressForm(request.POST, instance=address)
        if form.is_valid():
            address = form.save()
            if not artista.address:
                artista.address = address
                artista.save()
            messages.success(request, "Endereço do artista atualizado!")
            if request.headers.get('HX-Request'):
                response = HttpResponse()
                response['HX-Refresh'] = 'true'
                return response
            return redirect('artistas:artista_dashboard')
        return render(request, 'artistas/partials/address_form.html', {'form': form, 'artista': artista})

class ArtistaListView(ListView):
    model = Artista
    template_name = 'artistas/artista_list.html'
    context_object_name = 'artistas'
    paginate_by = 12

    def get_queryset(self):
        # Apenas artistas Aprovados
        queryset = Artista.objects.filter(status='APPROVED').annotate(
            num_seguidores=Count('seguidores')
        )
        
        # Filtros de Categoria
        category = self.request.GET.get('category')
        if category:
            queryset = queryset.filter(category=category)
            
        # Busca por Nome
        search_query = self.request.GET.get('q')
        if search_query:
            queryset = queryset.filter(Q(name__icontains=search_query) | Q(bio__icontains=search_query))
            
        # Filtros de Seguimento (Apenas se logado)
        if self.request.user.is_authenticated:
            follow_filter = self.request.GET.get('follow_status')
            perfil = self.request.user.perfil
            seguindo_ids = perfil.artistas_seguindo.values_list('artista_id', flat=True)
            
            if follow_filter == 'seguindo':
                queryset = queryset.filter(id__in=seguindo_ids)
            elif follow_filter == 'nao_segue':
                queryset = queryset.exclude(id__in=seguindo_ids)
                # Também não recomendar a si mesmo na lista se possível, 
                # mas o usuário pediu "não segue", o que tecnicamente inclui ele mesmo.
                # Vamos excluir o próprio se ele for um artista.
                if hasattr(self.request.user, 'artista_profile'):
                    queryset = queryset.exclude(id=self.request.user.artista_profile.id)

        # ORDENAÇÃO POR RECOMENDAÇÃO
        # IDs recomendados em ordem
        recommended_ids = []
        if self.request.user.is_authenticated:
            try:
                rec = RecomendadorCultural()
                recomendacoes = rec.recomendar(self.request.user.perfil.id)
                recommended_ids = [item['objeto'].id for item in recomendacoes if item['tipo'] == 'artista']
            except Exception:
                pass
        
        if recommended_ids:
            # Preservar ordem da recomendação e depois por seguidores
            preserved_order = Case(*[When(id=pk, then=pos) for pos, pk in enumerate(recommended_ids)],
                                 output_field=IntegerField())
            queryset = queryset.order_by(preserved_order, '-num_seguidores')
        else:
            queryset = queryset.order_by('-num_seguidores', 'name')
            
        return queryset

    def get(self, request, *args, **kwargs):
        # Sobrescreve o GET para lidar com paginação e busca AJAX
        self.object_list = self.get_queryset()
        
        # Paginação manual necessária para controlar o contexto
        page = request.GET.get('page', 1)
        paginator = Paginator(self.object_list, self.paginate_by)
        page_obj = paginator.get_page(page)

        context = {
            'artistas': page_obj,
            'current_category': request.GET.get('category', ''),
            'search_query': request.GET.get('q', ''),
            'follow_status': request.GET.get('follow_status', ''),
            'categories': Artista.CATEGORY_CHOICES,
        }

        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            html = render_to_string('artistas/partials/artistas.html', context, request=request)
            return JsonResponse({'html': html})

        return render(request, self.template_name, context)

class ArtistaDetailView(DetailView):
    model = Artista
    template_name = 'artistas/artista_detail.html'
    context_object_name = 'artista'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        artista = self.object
        context['posts'] = Post.objects.filter(artista=artista).order_by('-created_at')
        context['events'] = Event.objects.filter(artista=artista, active=True).order_by('date')
        
        if self.request.user.is_authenticated:
            context['is_following'] = SeguidorArtista.objects.filter(perfil=self.request.user.perfil, artista=artista).exists()
        else:
            context['is_following'] = False
            
        context['followers_count'] = artista.seguidores.count()
        
        # Produtos e Serviços da Loja
        content_type = ContentType.objects.get_for_model(artista)
        context['products'] = Product.objects.filter(content_type=content_type, object_id=artista.id, is_active=True)
        
        service_qs = Service.objects.filter(content_type=content_type, object_id=artista.id)
        if not (self.request.user.is_authenticated and self.request.user == artista.user):
            service_qs = service_qs.filter(is_active=True)
        context['services'] = service_qs
        context['is_owner'] = self.request.user == artista.user
        
        return context

class FollowArtistaView(LoginRequiredMixin, View):
    def post(self, request, pk):
        artista = get_object_or_404(Artista, pk=pk)
        perfil = request.user.perfil
        
        seguidor_qs = SeguidorArtista.objects.filter(perfil=perfil, artista=artista)
        
        if seguidor_qs.exists():
            seguidor_qs.delete()
            is_following = False
        else:
            SeguidorArtista.objects.create(perfil=perfil, artista=artista)
            is_following = True
            
        if request.headers.get('HX-Request'):
             context = {
                 'is_following': is_following,
                 'artista': artista,
                 'followers_count': artista.seguidores.count()
             }
             return render(request, 'artistas/partials/follow_button.html', context)
             
        return redirect('artistas:artista_detail', pk=pk)

class ArtistaRequestView(LoginRequiredMixin, CreateView):
    model = Artista
    form_class = ArtistaRequestForm
    template_name = 'artistas/artista_request.html'
    success_url = reverse_lazy('home:index')

    def form_valid(self, form):
        if hasattr(self.request.user, 'artista_profile'):
            messages.warning(self.request, 'Você já possui uma solicitação ou perfil de artista.')
            return redirect('home:index')

        artista = form.save(commit=False)
        artista.user = self.request.user
        artista.status = 'PENDING'
        artista.save()
        messages.success(self.request, 'Solicitação enviada com sucesso! Aguarde a aprovação da administração.')
        return super().form_valid(form)

class ArtistaUpdateView(LoginRequiredMixin, UpdateView):
    model = Artista
    form_class = ArtistaUpdateForm
    template_name = 'artistas/partials/artista_edit.html'

    def get_queryset(self):
        return super().get_queryset().filter(user=self.request.user)

    def form_valid(self, form):
        form.save()
        if self.request.headers.get('HX-Request'):
             from django.http import HttpResponse
             response = HttpResponse()
             response['HX-Refresh'] = 'true'
             return response
        return redirect('artistas:artista_detail', pk=self.object.pk)

class ArtistaDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'artistas/artista_dashboard.html'

    def get(self, request, *args, **kwargs):
        if not hasattr(request.user, 'artista_profile') or request.user.artista_profile.status != 'APPROVED':
            messages.error(request, 'Você não tem permissão para acessar o painel de artista.')
            return redirect('artistas:artista_request')

        artista = request.user.artista_profile
        posts = artista.posts.all().order_by('-created_at')
        return render(request, self.template_name, {'artista': artista, 'posts': posts})

class ArtistaPostCreateView(LoginRequiredMixin, CreateView):
    model = Post
    form_class = PostForm
    template_name = 'post/post_create.html' # Reusando template de post

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_artist_post'] = True # Flag para o template saber que é post de artista
        return context

    def form_valid(self, form):
        if not hasattr(self.request.user, 'artista_profile') or self.request.user.artista_profile.status != 'APPROVED':
             return redirect('home:index')

        post = form.save(commit=False)
        post.author = self.request.user.perfil
        post.artista = self.request.user.artista_profile
        post.save()
        messages.success(self.request, 'Postagem criada com sucesso!')
        return redirect('artistas:artista_detail', pk=self.request.user.artista_profile.pk)

class ArtistaEventCreateView(LoginRequiredMixin, CreateView):
    model = Event
    form_class = EventForm
    template_name = 'events/event_create.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_artist_event'] = True
        return context

    def form_valid(self, form):
        if not hasattr(self.request.user, 'artista_profile') or self.request.user.artista_profile.status != 'APPROVED':
             return redirect('home:index')

        event = form.save(commit=False)
        event.author_perfil = self.request.user.perfil
        event.artista = self.request.user.artista_profile
        event.active = True # Forçar ativo na criação
        event.save()
        messages.success(self.request, 'Evento criado com sucesso e aparecerá na agenda cultural!')
        return redirect('artistas:artista_detail', pk=self.request.user.artista_profile.pk)


class AdminArtistRequestListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = Artista
    template_name = 'artistas/admin_request_list.html'
    context_object_name = 'requests'

    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser

    def get_queryset(self):
        return Artista.objects.filter(status='PENDING').order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['group_requests'] = Grupo.objects.filter(status='PENDING').order_by('-created_at')
        return context

class AdminApproveRequestView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser

    def post(self, request, pk):
        artista = get_object_or_404(Artista, pk=pk)
        artista.status = 'APPROVED'
        artista.save()

        # Send Email
        try:
            send_artist_status_email_task.delay(artista, 'APPROVED')
            messages.success(request, f'Solicitação de {artista.name} aprovada e e-mail enviado.')
        except Exception as e:
            messages.success(request, f'Solicitação aprovada. (Erro ao enviar e-mail: {e})')

        return redirect('artistas:admin_request_list')

class AdminRejectRequestView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser

    def post(self, request, pk):
        artista = get_object_or_404(Artista, pk=pk)
        artista_name = artista.name
        recipient_email = artista.user.email
        
        # Deletar ao invés de apenas marcar como rejeitado
        artista.delete()

         # Send Email
        try:
            send_artist_status_email_task.delay(artista, 'REJECTED')
            messages.success(request, f'Solicitação de {artista_name} recusada e dados removidos.')
        except Exception as e:
            messages.success(request, f'Solicitação recusada e dados removidos. (Erro ao enviar e-mail: {e})')

        return redirect('artistas:admin_request_list')

class ArtistaDeliveryUpdateView(LoginRequiredMixin, View):
    def get(self, request):
        artista = get_object_or_404(Artista, user=request.user)
        from .forms import ArtistaDeliveryForm
        form = ArtistaDeliveryForm(instance=artista)
        return render(request, 'artistas/partials/delivery_form.html', {'form': form, 'artista': artista})

    def post(self, request):
        artista = get_object_or_404(Artista, user=request.user)
        from .forms import ArtistaDeliveryForm
        form = ArtistaDeliveryForm(request.POST, instance=artista)
        if form.is_valid():
            form.save()
            messages.success(request, "Configurações de frete atualizadas!")
            if request.headers.get('HX-Request'):
                response = HttpResponse()
                response['HX-Refresh'] = 'true'
                return response
            return redirect('artistas:artista_detail', pk=artista.pk)
        return render(request, 'artistas/partials/delivery_form.html', {'form': form, 'artista': artista})
