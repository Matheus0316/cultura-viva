from django import forms
from .models import AcervoItem
from django_summernote.widgets import SummernoteWidget

class AcervoItemForm(forms.ModelForm):
    class Meta:
        model = AcervoItem
        fields = ['title', 'description', 'media_type', 'file', 'external_link', 'date_ref', 'location']
        widgets = {
            'description': SummernoteWidget(),
            'date_ref': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Bota classes do Tailwind
        for field in self.fields.values():
            if not isinstance(field.widget, SummernoteWidget):
                 field.widget.attrs.update({'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-cultura-terracotta'})

    def clean(self):
        cleaned_data = super().clean()
        media_type = cleaned_data.get('media_type')
        external_link = cleaned_data.get('external_link')
        file = cleaned_data.get('file')

        if media_type == 'VIDEO' and not external_link and not file:
            raise forms.ValidationError("Para vídeos, forneça um arquivo ou um link externo (YouTube).")

        if file:
            # Validação de extensão
            import os
            ext = os.path.splitext(file.name)[1].lower()
            valid_extensions = {
                'FOTO': ['.jpg', '.jpeg', '.png', '.gif', '.webp'],
                'VIDEO': ['.mp4', '.mov', '.avi', '.webm'],
                'AUDIO': ['.mp3', '.wav', '.ogg'],
                'DOCUMENTO': ['.pdf', '.doc', '.docx', '.txt'],
            }

            allowed = valid_extensions.get(media_type)
            if allowed and ext not in allowed:
                 raise forms.ValidationError(f"Tipo de arquivo inválido para {media_type}. Extensões permitidas: {', '.join(allowed)}")

        return cleaned_data
