from django.db import models
from uuid import uuid4
from perfil.models import Perfil

from artistas.models import Artista
from grupos.models import Grupo

class Event(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    title = models.CharField(max_length=200)
    icon = models.ImageField(upload_to='events/icons/', blank=True, null=True)
    description = models.TextField()
    date = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    active = models.BooleanField(default=True)
    
    # Autoria
    author_perfil = models.ForeignKey(Perfil, on_delete=models.CASCADE, related_name='events_created', blank=True, null=True)
    artista = models.ForeignKey(Artista, on_delete=models.CASCADE, related_name='events', blank=True, null=True)
    grupo = models.ForeignKey(Grupo, on_delete=models.CASCADE, related_name='events', blank=True, null=True)

    @property
    def icon_url(self):
        if self.icon and hasattr(self.icon, 'url'):
            return self.icon.url
        return '/media/default_group_thumbnail.jpg'

class EventReminder(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='reminders')
    profile = models.ForeignKey(Perfil, on_delete=models.CASCADE, related_name='event_reminders')
    task_id = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('event', 'profile')

    def __str__(self):
        return f"Lembrete para {self.user.username} sobre {self.event.title} (Task: {self.task_id})"
