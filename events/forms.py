from django import forms
from django_summernote.widgets import SummernoteWidget
from .models import Event
from artistas.models import Artista
from grupos.models import Grupo
from perfil.models import MembroGrupo

class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = ['title', 'description', 'date', 'icon', 'active', 'grupo']
        widgets = {
            'description': SummernoteWidget(),
            'date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
        }

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
        
        # Filtrar grupos onde o usuário é líder
        if self.request:
            if self.request.user.is_superuser:
                self.fields['grupo'].queryset = Grupo.objects.all()
            else:
                grupos_liderados = Grupo.objects.filter(
                    membros__perfil=self.request.user.perfil,
                    membros__position__position__iexact='Líder'
                )
                self.fields['grupo'].queryset = grupos_liderados
            
            # Sempre oculta o campo grupo para todos os usuários
            self.fields['grupo'].widget = forms.HiddenInput()
            
            # Pré-seleção se houver apenas um grupo ou se vier via query param
            if not self.initial.get('grupo'):
                if not self.request.user.is_superuser:
                    grupos_liderados = self.fields['grupo'].queryset
                    if grupos_liderados.count() == 1:
                        self.initial['grupo'] = grupos_liderados.first()
            
            if not self.request.user.is_superuser and not self.fields['grupo'].queryset.exists():
                self.fields['grupo'].required = False
        
        # Garantir que eventos novos venham como ativos
        if not self.instance.pk:
            self.initial['active'] = True

        tailwind_input = "w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-brand-gold focus:border-brand-gold"
        tailwind_textarea = f"{tailwind_input} h-32"

        self.fields['title'].widget.attrs.update({
            'class': tailwind_input,
            'placeholder': 'Ex: Santa Missa, Festa do Padroeiro'
        })

        self.fields['description'].widget.attrs.update({
            'class': tailwind_textarea,
            'placeholder': 'Descreva os detalhes do evento...'
        })

        self.fields['date'].widget.attrs.update({
            'class': tailwind_input,
            'type': 'datetime-local'
        })

        self.fields['icon'].widget.attrs.update({
            'class': 'w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-brand-cream file:text-brand-brown hover:file:bg-yellow-100'
        })

        self.fields['active'].widget.attrs.update({
            'class': 'h-4 w-4 text-brand-gold border-gray-300 rounded focus:ring-brand-gold'
        })

        if 'grupo' in self.fields:
             self.fields['grupo'].widget.attrs.update({
                'class': tailwind_input,
            })
             self.fields['grupo'].label = "Grupo vinculado (opcional)"
