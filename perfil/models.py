from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
import uuid
from grupos.models import Grupo

choises = [
    ('M', 'Masculino'),
    ('F', 'Feminino')
]

class Address(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='addresses', null=True, blank=True)
    
    street = models.CharField(max_length=255, verbose_name="Rua")
    number = models.CharField(max_length=20, verbose_name="Número")
    neighborhood = models.CharField(max_length=100, verbose_name="Bairro")
    city = models.CharField(max_length=100, verbose_name="Cidade")
    state = models.CharField(max_length=2, verbose_name="UF")
    zip_code = models.CharField(max_length=10, verbose_name="CEP")
    
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    
    is_main = models.BooleanField(default=False, verbose_name="Principal")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.street}, {self.number} - {self.city}"

    class Meta:
        verbose_name = "Endereço"
        verbose_name_plural = "Endereços"

class Perfil(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil')
    name = models.CharField(max_length=150)
    age = models.PositiveIntegerField(null=True, blank=True)
    sex = models.CharField(max_length=1, choices=choises, blank=True)
    bio = models.TextField(blank=True)
    cpf = models.CharField(max_length=14, blank=True, null=True, verbose_name="CPF")
    icon = models.ImageField(upload_to='icons/', blank=True, null=True)
    can_add_acervo = models.BooleanField(default=False, verbose_name="Pode adicionar ao Acervo?")

    def __str__(self):
        return self.user.username

    @property
    def avatar(self):
        if self.icon:
            return self.icon.url
        return f'{settings.MEDIA_URL}default_avatar.jpg'

class Position(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    grupo = models.ForeignKey(Grupo, on_delete=models.CASCADE, related_name='positions', null=True, blank=True)
    position = models.CharField(max_length=50)

    class Meta:
        unique_together = ('grupo', 'position')

    def __str__(self):
        return self.position

class MembroGrupo(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    perfil = models.ForeignKey(Perfil, on_delete=models.CASCADE, related_name='grupos')
    grupo = models.ForeignKey(Grupo, on_delete=models.CASCADE, related_name='membros')
    joined_at = models.DateTimeField(auto_now_add=True)
    position = models.ForeignKey(Position, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        unique_together = ('perfil', 'grupo')

    def __str__(self):
        return f"{self.perfil.user.username}"

class SeguidorGrupo(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    perfil = models.ForeignKey(Perfil, on_delete=models.CASCADE, related_name='seguindo')
    grupo = models.ForeignKey(Grupo, on_delete=models.CASCADE, related_name='seguidores')
    followed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('perfil', 'grupo')

    def __str__(self):
        return f"{self.perfil.user.username} segue {self.grupo.name}"
