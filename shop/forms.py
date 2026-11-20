from django import forms
from .models import Product, Service

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'description', 'price', 'image', 'stock', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'glass-input', 'placeholder': 'Nome do produto'}),
            'description': forms.Textarea(attrs={'class': 'glass-input', 'placeholder': 'Descreva seu produto...', 'rows': 4}),
            'price': forms.NumberInput(attrs={'class': 'glass-input', 'step': '0.01', 'min': '0.01'}),
            'image': forms.FileInput(attrs={'class': 'glass-input'}),
            'stock': forms.NumberInput(attrs={'class': 'glass-input', 'min': '0'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'glass-checkbox'}),
        }

class ServiceForm(forms.ModelForm):
    days_selection = forms.MultipleChoiceField(
        choices=[(str(k), v) for k, v in Service.DAY_CHOICES],
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'day-selector-grid'}),
        label="Dias da Semana",
        required=False
    )

    class Meta:
        model = Service
        fields = ['name', 'description', 'price', 'start_time', 'end_time', 'duration_hours', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'glass-input', 'placeholder': 'Ex: Consultoria, Aula de Pintura...'}),
            'description': forms.Textarea(attrs={'class': 'glass-input', 'placeholder': 'Descreva o que está incluso no serviço...', 'rows': 4}),
            'price': forms.NumberInput(attrs={'class': 'glass-input', 'step': '0.01', 'min': '0.01'}),
            'start_time': forms.TimeInput(attrs={'class': 'glass-input', 'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'class': 'glass-input', 'type': 'time'}),
            'duration_hours': forms.NumberInput(attrs={'class': 'glass-input', 'step': '0.5', 'min': '0.5'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'glass-checkbox'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.available_days:
            # Popula o campo de seleção com a lista de strings vinda da string do banco
            self.fields['days_selection'].initial = self.instance.available_days.split(',')

    def save(self, commit=True):
        instance = super().save(commit=False)
        # Converte a lista de seleção de volta para string para o banco
        days_list = self.cleaned_data.get('days_selection', [])
        instance.available_days = ",".join(days_list)
        if commit:
            instance.save()
        return instance
