from django import forms
from .models import Post
from django_summernote.widgets import SummernoteWidget

class PostForm(forms.ModelForm):

    class Meta:
        model = Post
        fields = ['title', 'thumbnail', 'content', 'comments_enabled']
        labels = {
            'title': 'Título da Publicação',
            'thumbnail': 'Imagem de Destaque',
            'content': 'Conteúdo',
            'comments_enabled': 'Permitir comentários nesta publicação',
        }
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 bg-gray-50 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-brand-gold focus:border-transparent transition duration-300',
                'placeholder': 'Um título claro e objetivo'
            }),
            'thumbnail': forms.ClearableFileInput(attrs={
                'class': 'block w-full text-sm text-slate-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-brand-cream file:text-brand-brown hover:file:bg-yellow-200 cursor-pointer'
            }),
            'content': SummernoteWidget(),
            'comments_enabled': forms.CheckboxInput(attrs={
                'class': 'h-4 w-4 rounded border-gray-300 text-brand-gold focus:ring-brand-gold'
            })
        }
