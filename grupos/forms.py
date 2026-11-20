from django import forms
from .models import Grupo

class GrupoForm(forms.ModelForm):
    class Meta:
        model = Grupo
        fields = ['name', 'description', 'thumbnail', 'category']
        widgets = {
            'category': forms.Select(attrs={
                'class': 'w-full px-4 py-3 bg-gray-50 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-brand-gold focus:border-transparent appearance-none'
            }),
        }

class GrupoDeliveryForm(forms.ModelForm):
    class Meta:
        model = Grupo
        fields = ['delivery_enabled', 'shipping_cost_per_km', 'free_shipping_threshold_km']
        widgets = {
            'delivery_enabled': forms.CheckboxInput(attrs={'class': 'rounded text-brand-gold focus:ring-brand-gold'}),
            'shipping_cost_per_km': forms.NumberInput(attrs={'class': 'w-full pl-14 pr-4 py-3 bg-gray-50 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-brand-gold', 'step': '0.01'}),
            'free_shipping_threshold_km': forms.NumberInput(attrs={'class': 'w-full pl-14 pr-4 py-3 bg-gray-50 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-brand-gold', 'step': '0.1'}),
        }
