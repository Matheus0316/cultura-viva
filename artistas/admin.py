from django.contrib import admin
from .models import Artista, SeguidorArtista

from .tasks import send_artist_status_email_task

@admin.register(Artista)
class ArtistaAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'status', 'user', 'created_at')
    list_filter = ('status', 'category')
    search_fields = ('name', 'user__username', 'user__email')

    def save_model(self, request, obj, form, change):
        # Verifica se o status mudou
        if change:
            old_obj = Artista.objects.get(pk=obj.pk)
            if old_obj.status != obj.status:
                # Se mudou para Aprovado ou Rejeitado, envia email
                if obj.status in ['APPROVED', 'REJECTED']:
                    send_artist_status_email_task.delay(obj, obj.status)

        super().save_model(request, obj, form, change)

@admin.register(SeguidorArtista)
class SeguidorArtistaAdmin(admin.ModelAdmin):
    list_display = ('perfil', 'artista', 'followed_at')
    list_filter = ('followed_at',)
    search_fields = ('perfil__user__username', 'artista__name')

