from django.db import models
from grupos.models import Grupo
from perfil.models import Perfil
from artistas.models import Artista
import uuid

class Post(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200)
    thumbnail = models.ImageField(upload_to='posts/thumbnails', blank=True, null=True)
    content = models.TextField(blank=True, null=True)
    grupo = models.ForeignKey(Grupo, on_delete=models.CASCADE, related_name='posts', blank=True, null=True)
    artista = models.ForeignKey(Artista, on_delete=models.CASCADE, related_name='posts', blank=True, null=True)
    author = models.ForeignKey(Perfil, on_delete=models.CASCADE, related_name='posts')
    created_at = models.DateTimeField(auto_now_add=True)
    comments_enabled = models.BooleanField(default=True)

    POST_TYPES = (
        ('NOTICIA', 'Notícia'),
        ('HISTORIA', 'História e Memória'),
        ('RELATO', 'Relato de Morador'),
    )
    category = models.CharField(max_length=20, choices=POST_TYPES, default='NOTICIA')

    MEDIA_TYPES = (
        ('TEXTO', 'Texto'),
        ('IMAGEM', 'Imagem'),
        ('VIDEO', 'Vídeo'),
        ('AUDIO', 'Áudio'),
    )
    media_type = models.CharField(max_length=10, choices=MEDIA_TYPES, default='TEXTO')

    @property
    def thumbnail_url(self):
        if self.thumbnail:
            return self.thumbnail.url
        return '/media/default_group_thumbnail.jpg'
