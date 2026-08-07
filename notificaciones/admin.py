from django.contrib import admin

from .models import Notificacion


@admin.register(Notificacion)
class NotificacionAdmin(admin.ModelAdmin):
    save_on_top = True
    autocomplete_fields = ('usuario', 'evento')
    list_display = ('titulo', 'usuario', 'evento', 'tipo', 'leida', 'fecha_creacion')
    list_filter = ('evento', 'tipo', 'leida', 'fecha_creacion')
    search_fields = (
        'titulo',
        'mensaje',
        'usuario__username',
        'usuario__first_name',
        'usuario__last_name',
        'evento__nombre_evento',
        'evento__novio',
        'evento__novia',
    )
    date_hierarchy = 'fecha_creacion'
    actions = ('marcar_como_leidas',)
    fields = ('usuario', 'evento', 'tipo', 'titulo', 'mensaje', 'enlace', 'leida', 'fecha_creacion')
    readonly_fields = ('fecha_creacion',)

    def marcar_como_leidas(self, request, queryset):
        actualizadas = queryset.update(leida=True)
        self.message_user(request, f'{actualizadas} notificacion(es) marcada(s) como leidas.')

    marcar_como_leidas.short_description = 'Marcar como leidas'

# Register your models here.
