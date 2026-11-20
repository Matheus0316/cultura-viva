from django import forms
from .models import Artista

class ArtistaRequestForm(forms.ModelForm):
    class Meta:
        model = Artista
        fields = ['name', 'bio', 'category', 'request_description', 'portfolio_link', 'instagram', 'whatsapp']
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 4}),
            'request_description': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Explique seu trabalho e por que gostaria de se cadastrar como artista.'}),
        }

class ArtistaUpdateForm(forms.ModelForm):
    class Meta:
        model = Artista
        fields = ['name', 'bio', 'category', 'portfolio_link', 'instagram', 'youtube', 'whatsapp']
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 5, 'class': 'w-full px-4 py-3 bg-gray-50 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-cultura-terracotta focus:border-transparent'}),
            'name': forms.TextInput(attrs={'class': 'w-full px-4 py-2 border rounded-lg'}),
            'category': forms.Select(attrs={'class': 'w-full px-4 py-2 border rounded-lg'}),
            'portfolio_link': forms.URLInput(attrs={'class': 'w-full px-4 py-2 border rounded-lg', 'placeholder': 'https://...'}),
            'instagram': forms.URLInput(attrs={'class': 'w-full px-4 py-2 border rounded-lg', 'placeholder': 'https://instagram.com/...'}),
            'youtube': forms.URLInput(attrs={'class': 'w-full px-4 py-2 border rounded-lg', 'placeholder': 'https://youtube.com/...'}),
            'whatsapp': forms.TextInput(attrs={'class': 'w-full px-4 py-2 border rounded-lg', 'placeholder': '83999999999'}),
        }

class ArtistaDeliveryForm(forms.ModelForm):
    class Meta:
        model = Artista
        fields = ['delivery_enabled', 'shipping_cost_per_km', 'free_shipping_threshold_km']
        widgets = {
            'delivery_enabled': forms.CheckboxInput(attrs={'class': 'rounded text-cultura-green focus:ring-cultura-green'}),
            'shipping_cost_per_km': forms.NumberInput(attrs={'class': 'w-full pl-14 pr-4 py-3 bg-gray-50 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-cultura-terracotta', 'step': '0.01'}),
            'free_shipping_threshold_km': forms.NumberInput(attrs={'class': 'w-full pl-14 pr-4 py-3 bg-gray-50 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-cultura-terracotta', 'step': '0.1'}),
        }
