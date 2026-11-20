from django import forms
from .models import BankAccount

class BankAccountForm(forms.ModelForm):
    class Meta:
        model = BankAccount
        fields = [
            'bank_name', 'bank_code', 'agency', 'account_number', 
            'account_type', 'pix_key', 'document_name', 'document_number', 'birth_date', 'phone',
            'email', 'income_value', 'company_type'
        ]
        widgets = {
            'bank_name': forms.TextInput(attrs={'class': 'w-full px-6 py-4 rounded-xl bg-gray-50 border-none focus:ring-2 focus:ring-cultura-green', 'placeholder': 'Nome do Banco'}),
            'bank_code': forms.TextInput(attrs={'class': 'w-full px-6 py-4 rounded-xl bg-gray-50 border-none focus:ring-2 focus:ring-cultura-green', 'placeholder': 'Código (ex: 001)'}),
            'agency': forms.TextInput(attrs={'class': 'w-full px-6 py-4 rounded-xl bg-gray-50 border-none focus:ring-2 focus:ring-cultura-green', 'placeholder': 'Agência'}),
            'account_number': forms.TextInput(attrs={'class': 'w-full px-6 py-4 rounded-xl bg-gray-50 border-none focus:ring-2 focus:ring-cultura-green', 'placeholder': 'Número da Conta (com dígito)'}),
            'account_type': forms.Select(attrs={'class': 'w-full px-6 py-4 rounded-xl bg-gray-50 border-none focus:ring-2 focus:ring-cultura-green'}),
            'pix_key': forms.TextInput(attrs={'class': 'w-full px-6 py-4 rounded-xl bg-gray-50 border-none focus:ring-2 focus:ring-cultura-green', 'placeholder': 'Chave Pix (opcional)'}),
            'document_name': forms.TextInput(attrs={'class': 'w-full px-6 py-4 rounded-xl bg-gray-50 border-none focus:ring-2 focus:ring-cultura-green', 'placeholder': 'Nome completo do titular'}),
            'document_number': forms.TextInput(attrs={'class': 'w-full px-6 py-4 rounded-xl bg-gray-50 border-none focus:ring-2 focus:ring-cultura-green', 'id': 'document_number', 'placeholder': 'CPF ou CNPJ'}),
            'birth_date': forms.DateInput(attrs={'class': 'w-full px-6 py-4 rounded-xl bg-gray-50 border-none focus:ring-2 focus:ring-cultura-green', 'type': 'date'}, format='%Y-%m-%d'),
            'phone': forms.TextInput(attrs={'class': 'w-full px-6 py-4 rounded-xl bg-gray-50 border-none focus:ring-2 focus:ring-cultura-green', 'placeholder': 'Celular (com DDD)'}),
            'email': forms.EmailInput(attrs={'class': 'w-full px-6 py-4 rounded-xl bg-gray-50 border-none focus:ring-2 focus:ring-cultura-green', 'placeholder': 'E-mail da Conta (Não use e-mail pessoal)'}),
            'income_value': forms.NumberInput(attrs={'class': 'w-full px-6 py-4 rounded-xl bg-gray-50 border-none focus:ring-2 focus:ring-cultura-green', 'placeholder': 'Faturamento Mensal'}),
            'address': forms.TextInput(attrs={'class': 'w-full px-6 py-4 rounded-xl bg-gray-50 border-none focus:ring-2 focus:ring-cultura-green', 'placeholder': 'Endereço'}),
            'address_number': forms.TextInput(attrs={'class': 'w-full px-6 py-4 rounded-xl bg-gray-50 border-none focus:ring-2 focus:ring-cultura-green', 'placeholder': 'Número'}),
            'complement': forms.TextInput(attrs={'class': 'w-full px-6 py-4 rounded-xl bg-gray-50 border-none focus:ring-2 focus:ring-cultura-green', 'placeholder': 'Complemento (opcional)'}),
            'province': forms.TextInput(attrs={'class': 'w-full px-6 py-4 rounded-xl bg-gray-50 border-none focus:ring-2 focus:ring-cultura-green', 'placeholder': 'Bairro'}),
            'postal_code': forms.TextInput(attrs={'class': 'w-full px-6 py-4 rounded-xl bg-gray-50 border-none focus:ring-2 focus:ring-cultura-green', 'id': 'postal_code', 'placeholder': 'CEP'}),
            'company_type': forms.Select(attrs={'class': 'w-full px-6 py-4 rounded-xl bg-gray-50 border-none focus:ring-2 focus:ring-cultura-green'}),
        }
