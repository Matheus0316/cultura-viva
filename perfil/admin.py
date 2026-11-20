from django.contrib import admin
from .models import Perfil, Position, MembroGrupo, SeguidorGrupo

@admin.register(Perfil)
class PerfilAdmin(admin.ModelAdmin):
    list_display = ('user', 'name', 'can_add_acervo')
    list_filter = ('can_add_acervo', 'sex')
    search_fields = ('user__username', 'name', 'bio')

admin.site.register(Position)
admin.site.register(MembroGrupo)
admin.site.register(SeguidorGrupo)
