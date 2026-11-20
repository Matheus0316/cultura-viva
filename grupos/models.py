from django.db import models
from django.contrib.auth.models import User
import uuid

class Grupo(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    thumbnail = models.ImageField(upload_to='grupos/thumbnails/', blank=True, null=True)
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='updated_grupos')
    address = models.OneToOneField('perfil.Address', on_delete=models.SET_NULL, null=True, blank=True, related_name='grupo', verbose_name="Endereço Fixo")

    CATEGORY_CHOICES = (
        ('PROJETO_SOCIAL', 'Projeto Social'),
        ('COLETIVO', 'Coletivo Cultural'),
        ('OFICINA', 'Oficina/Formação'),
        ('OUTRO', 'Outro'),
    )
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='OUTRO')
    
    STATUS_CHOICES = (
        ('PENDING', 'Pendente'),
        ('APPROVED', 'Aprovado'),
        ('REJECTED', 'Recusado'),
    )
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')

    # Delivery Configurations
    delivery_enabled = models.BooleanField(default=True, verbose_name="Delivery Enabled")
    shipping_cost_per_km = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name="Shipping Cost per KM")
    free_shipping_threshold_km = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name="Free Shipping Threshold (KM)")

    def __str__(self):
        return self.name

    def get_lideres(self):
        return self.membros.filter(position__position__iexact='Líder')

    @property
    def thumbnail_url(self):
        if self.thumbnail and hasattr(self.thumbnail, 'url'):
            return self.thumbnail.url
        return '/media/default_group_thumbnail.jpg'
