from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.contrib import messages
from .models import AcervoItem
from .forms import AcervoItemForm

class AcervoPermissionMixin(UserPassesTestMixin):
    def test_func(self):
        # Permite se for Superusuário OU se tiver a flag can_add_acervo no perfil
        user = self.request.user
        if not user.is_authenticated:
            return False
        if user.is_superuser:
            return True
        if hasattr(user, 'perfil') and user.perfil.can_add_acervo:
            return True
        return False

    def handle_no_permission(self):
        # Opcional: Adicionar mensagem antes de redirecionar
        messages.error(self.request, "Você não tem permissão para gerenciar itens do acervo.")
        return super().handle_no_permission()

class AcervoListView(ListView):
    model = AcervoItem
    template_name = 'acervo/acervo_list.html'
    context_object_name = 'items'
    paginate_by = 12

    def get_queryset(self):
        queryset = super().get_queryset()
        media_type = self.request.GET.get('type')
        if media_type and media_type != 'all':
            type_map = {
                'foto': 'FOTO',
                'video': 'VIDEO',
                'documento': 'DOCUMENTO',
                'audio': 'AUDIO',
            }
            db_type = type_map.get(media_type)
            if db_type:
                queryset = queryset.filter(media_type=db_type)
        return queryset.order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_type'] = self.request.GET.get('type', 'all')
        # Passa a permissão para o template exibir o botão de criar
        context['can_add'] = self.request.user.is_authenticated and (
            self.request.user.is_superuser or (hasattr(self.request.user, 'perfil') and self.request.user.perfil.can_add_acervo)
        )
        return context

class AcervoDetailView(DetailView):
    model = AcervoItem
    template_name = 'acervo/acervo_detail.html'
    context_object_name = 'item'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['can_edit'] = self.request.user.is_authenticated and (
             self.request.user.is_superuser or (hasattr(self.request.user, 'perfil') and self.request.user.perfil.can_add_acervo)
        )
        return context

class AcervoCreateView(LoginRequiredMixin, AcervoPermissionMixin, CreateView):
    model = AcervoItem
    form_class = AcervoItemForm
    template_name = 'acervo/acervo_form.html'
    success_url = reverse_lazy('acervo:acervo_list')

    def form_valid(self, form):
        messages.success(self.request, "Item adicionado ao acervo com sucesso!")
        return super().form_valid(form)

class AcervoUpdateView(LoginRequiredMixin, AcervoPermissionMixin, UpdateView):
    model = AcervoItem
    form_class = AcervoItemForm
    template_name = 'acervo/acervo_form.html'

    def get_success_url(self):
        return reverse_lazy('acervo:acervo_detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        messages.success(self.request, "Item do acervo atualizado!")
        return super().form_valid(form)

class AcervoDeleteView(LoginRequiredMixin, AcervoPermissionMixin, DeleteView):
    model = AcervoItem
    template_name = 'acervo/acervo_confirm_delete.html'
    success_url = reverse_lazy('acervo:acervo_list')

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, "Item removido do acervo.")
        return super().delete(request, *args, **kwargs)
