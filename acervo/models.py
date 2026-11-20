from django.db import models
import uuid

class AcervoItem(models.Model):
    MEDIA_TYPE_CHOICES = [
        ('FOTO', 'Fotografia'),
        ('VIDEO', 'Vídeo'),
        ('DOCUMENTO', 'Documento Histórico'),
        ('AUDIO', 'Áudio/Relato'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200, verbose_name="Título")
    description = models.TextField(verbose_name="Descrição Detalhada")

    media_type = models.CharField(max_length=20, choices=MEDIA_TYPE_CHOICES, default='FOTO', verbose_name="Tipo de Mídia")

    # Arquivo principal (pode ser imagem, pdf, audio)
    file = models.FileField(upload_to='acervo/files/', blank=True, null=True, verbose_name="Arquivo Digital")

    # Link externo (ex: vídeo do Youtube)
    external_link = models.URLField(blank=True, null=True, verbose_name="Link Externo (Youtube/Drive)")

    date_ref = models.DateField(blank=True, null=True, verbose_name="Data do Fato (Aproximada)")
    location = models.CharField(max_length=200, blank=True, null=True, verbose_name="Local de Referência")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_to = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title
