from django.db import models
from django.contrib.auth.models import User
import uuid

class Artista(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pendente'),
        ('APPROVED', 'Aprovado'),
        ('REJECTED', 'Rejeitado'),
    ]

    CATEGORY_CHOICES = [
        ('MUSICA', 'Música'),
        ('TEATRO', 'Teatro'),
        ('DANCA', 'Dança'),
        ('ARTESANATO', 'Artesanato'),
        ('LITERATURA', 'Literatura'),
        ('CVISUAIS', 'Artes Visuais'),
        ('CINEMA', 'Cinema/Audiovisual'),
        ('OUTRO', 'Outro'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200, verbose_name="Nome Artístico")
    bio = models.TextField(verbose_name="Biografia")
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='MUSICA', verbose_name="Categoria Principal")
    # Redes Sociais e Contato
    instagram = models.URLField(blank=True, null=True)
    youtube = models.URLField(blank=True, null=True)
    whatsapp = models.CharField(max_length=20, blank=True, null=True, help_text="Apenas números")
    portfolio_link = models.URLField(blank=True, null=True, verbose_name="Link do Portfólio")


    # Vinculo com Usuário
    user = models.OneToOneField(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='artista_profile', verbose_name="Usuário Responsável")
    address = models.OneToOneField('perfil.Address', on_delete=models.SET_NULL, null=True, blank=True, related_name='artista', verbose_name="Endereço Fixo")

    # Status da Requisição
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='APPROVED', verbose_name="Status do Cadastro")
    request_description = models.TextField(blank=True, null=True, verbose_name="Descrição da Solicitação (O que você faz?)")
    
    # Delivery Configurations
    delivery_enabled = models.BooleanField(default=True, verbose_name="Delivery Enabled")
    shipping_cost_per_km = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name="Shipping Cost per KM")
    free_shipping_threshold_km = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name="Free Shipping Threshold (KM)")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    @property
    def photo_url(self):
        if self.user and hasattr(self.user, 'perfil'):
             return self.user.perfil.avatar
        return '/media/default_avatar.jpg'

from perfil.models import Perfil

class SeguidorArtista(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    perfil = models.ForeignKey(Perfil, on_delete=models.CASCADE, related_name='artistas_seguindo')
    artista = models.ForeignKey(Artista, on_delete=models.CASCADE, related_name='seguidores')
    followed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('perfil', 'artista')

    def __str__(self):
        return f"{self.perfil.user.username} segue {self.artista.name}"
