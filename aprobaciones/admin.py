from django.contrib import admin

from .models import AprobacionEvento


@admin.register(AprobacionEvento)
class AprobacionEventoAdmin(admin.ModelAdmin):
    save_on_top = True
    autocomplete_fields = ('evento', 'solicitado_por', 'aprobado_por')
    list_display = (
        'titulo',
        'evento',
        'tipo',
        'estado',
        'solicitado_por',
        'aprobado_por',
        'fecha_solicitud',
        'fecha_respuesta',
    )
    list_filter = ('evento', 'tipo', 'estado', 'fecha_solicitud', 'fecha_respuesta')
    search_fields = (
        'titulo',
        'descripcion',
        'comentario',
        'modelo',
        'evento__nombre_evento',
        'evento__novio',
        'evento__novia',
        'solicitado_por__username',
        'aprobado_por__username',
    )
    readonly_fields = ('fecha_solicitud', 'fecha_respuesta')
    date_hierarchy = 'fecha_solicitud'
    fieldsets = (
        ('Evento y solicitud', {
            'fields': ('evento', 'tipo', 'titulo', 'descripcion', 'estado')
        }),
        ('Referencia interna', {
            'classes': ('collapse',),
            'fields': ('modelo', 'objeto_id')
        }),
        ('Usuarios', {
            'fields': ('solicitado_por', 'aprobado_por')
        }),
        ('Respuesta', {
            'fields': ('comentario', 'fecha_solicitud', 'fecha_respuesta')
        }),
    )

# Register your models here.
