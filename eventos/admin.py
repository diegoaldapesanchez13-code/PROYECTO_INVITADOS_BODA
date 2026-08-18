from django.contrib import admin

from .models import ContratoEvento, ParticipanteEvento


@admin.register(ParticipanteEvento)
class ParticipanteEventoAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'evento', 'rol', 'activo', 'es_contacto_principal')
    list_filter = ('rol', 'activo', 'evento__empresa')
    search_fields = (
        'usuario__username',
        'usuario__first_name',
        'usuario__last_name',
        'evento__nombre_evento',
    )
    autocomplete_fields = ('usuario', 'evento')


@admin.register(ContratoEvento)
class ContratoEventoAdmin(admin.ModelAdmin):
    list_display = (
        'evento',
        'version',
        'numero_contrato',
        'estado',
        'snapshot_version',
        'monto_base',
        'moneda',
        'fecha_firma',
    )
    list_filter = ('estado', 'snapshot_version', 'moneda', 'evento__empresa')
    search_fields = ('numero_contrato', 'evento__nombre_evento', 'evento__novio', 'evento__novia')
    autocomplete_fields = ('evento', 'propuesta_origen', 'creado_por')
    readonly_fields = ('snapshot_comercial', 'snapshot_version', 'propuesta_origen')
