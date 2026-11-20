from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django import forms
from django.db import transaction
from .models import Perfil, Address

tailwind_input = 'w-full px-4 py-2 border rounded-lg ...'
tailwind_select = 'w-full px-4 py-2 border rounded-lg ...'
tailwind_textarea = 'w-full px-4 py-2 border rounded-lg ...'
tailwind_file = 'w-full file:mr-4 file:py-2 ...'

class PerfilForm(UserCreationForm):
    username = forms.CharField(
        label="Usuário",
        max_length=150,
        help_text='',
        widget=forms.TextInput(attrs={'class': tailwind_input, 'placeholder': 'Nome de usuario'})
    )
    email = forms.EmailField(
        label='Email',
        required=True,
        widget=forms.EmailInput(attrs={'class': tailwind_input, 'placeholder': 'seu@email.com'})
    )
    name = forms.CharField(
        label="Nome Completo",
        max_length=150,
        widget=forms.TextInput(attrs={'class': tailwind_input, 'placeholder': 'Nome'})
    )

    password1 = forms.CharField(
        label="Senha",
        help_text='',
        widget=forms.PasswordInput(attrs={'class': tailwind_input, 'placeholder': 'Crie uma senha forte'})
    )
    password2 = forms.CharField(
        label="Confirmação de Senha",
        help_text='',
        widget=forms.PasswordInput(attrs={'class': tailwind_input, 'placeholder': 'Confirme sua senha'})
    )

    age = forms.IntegerField(
        label="Idade",
        required=False,
        widget=forms.NumberInput(attrs={'class': tailwind_input})
    )
    sex = forms.ChoiceField(
        label="Sexo",
        choices=[('', 'Selecione'), ('M', 'Masculino'), ('F', 'Feminino')],
        required=False,
        widget=forms.Select(attrs={'class': tailwind_select})
    )
    bio = forms.CharField(
        label="Biografia",
        required=False,
        widget=forms.Textarea(attrs={'class': tailwind_textarea, 'rows': 4, 'placeholder': 'Fale um pouco sobre você...'})
    )
    icon = forms.ImageField(
        label="Foto de Perfil",
        required=False,
        widget=forms.FileInput(attrs={'class': tailwind_file})
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ['username']

    def clean_age(self):
        age = self.cleaned_data.get('age')
        if age is not None and (age < 0 or age > 120):
            raise forms.ValidationError("Idade deve estar entre 0 e 120 anos.")
        return age

    @transaction.atomic
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data.get('email')

        if commit:
            user.save()
            perfil = Perfil.objects.create(
                user=user,
                name=self.cleaned_data.get('name'),
                age=self.cleaned_data.get('age') if self.cleaned_data.get('age') else None,
                sex=self.cleaned_data.get('sex') if self.cleaned_data.get('sex') else '',
                bio=self.cleaned_data.get('bio') if self.cleaned_data.get('bio') else '',
                cpf=self.cleaned_data.get('cpf') if self.cleaned_data.get('cpf') else '',
                icon=self.cleaned_data.get('icon') if self.cleaned_data.get('icon') else None
            )
        return user

class PerfilUpdateForm(forms.ModelForm):
    name = forms.CharField(
        label="Nome Completo",
        max_length=150,
        widget=forms.TextInput(attrs={'class': tailwind_input, 'placeholder': 'Nome'})
    )
    email = forms.EmailField(
        label='Email',
        required=True,
        widget=forms.EmailInput(attrs={'class': tailwind_input, 'placeholder': 'seu@email.com'})
    )
    age = forms.IntegerField(
        label="Idade",
        required=False,
        widget=forms.NumberInput(attrs={'class': tailwind_input})
    )
    sex = forms.ChoiceField(
        label="Sexo",
        choices=[('', 'Selecione'), ('M', 'Masculino'), ('F', 'Feminino')],
        required=False,
        widget=forms.Select(attrs={'class': tailwind_select})
    )
    bio = forms.CharField(
        label="Biografia",
        required=False,
        widget=forms.Textarea(attrs={'class': tailwind_textarea, 'rows': 4, 'placeholder': 'Fale um pouco sobre você...'})
    )
    icon = forms.ImageField(
        label="Foto de Perfil",
        required=False,
        widget=forms.FileInput(attrs={'class': tailwind_file})
    )

    class Meta:
        model = Perfil
        fields = ['name', 'age', 'sex', 'bio', 'icon', 'cpf']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.user:
            self.fields['email'].initial = self.instance.user.email

    @transaction.atomic
    def save(self, commit=True):
        perfil = super().save(commit=False)
        if commit:
            perfil.save()
            user = perfil.user
            user.email = self.cleaned_data.get('email')
            user.save()
        return perfil

class AddressForm(forms.ModelForm):
    latitude = forms.DecimalField(widget=forms.HiddenInput(), required=False, max_digits=20, decimal_places=15)
    longitude = forms.DecimalField(widget=forms.HiddenInput(), required=False, max_digits=20, decimal_places=15)

    class Meta:
        model = Address
        fields = ['zip_code', 'street', 'number', 'neighborhood', 'city', 'state', 'latitude', 'longitude', 'is_main']
        widgets = {
            'zip_code': forms.TextInput(attrs={'class': 'glass-input', 'placeholder': '00000-000', 'onblur': 'lookupZip(this.value)'}),
            'street': forms.TextInput(attrs={'class': 'glass-input', 'placeholder': 'Rua / Avenida'}),
            'number': forms.TextInput(attrs={'class': 'glass-input', 'placeholder': 'Nº'}),
            'neighborhood': forms.TextInput(attrs={'class': 'glass-input', 'placeholder': 'Bairro'}),
            'city': forms.TextInput(attrs={'class': 'glass-input', 'placeholder': 'Cidade'}),
            'state': forms.TextInput(attrs={'class': 'glass-input', 'placeholder': 'UF', 'maxlength': '2'}),
            'is_main': forms.CheckboxInput(attrs={'class': 'glass-checkbox'}),
        }
