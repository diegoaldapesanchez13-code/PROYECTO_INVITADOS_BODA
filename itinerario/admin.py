from django.contrib import admin

from .models import ActividadItinerario, ParticipanteActividad


class ParticipanteActividadInline(admin.TabularInline):
    model = ParticipanteActividad
    extra = 0
    autocomplete_fields = ('usuario', 'proveedor')
    fields = ('rol', 'usuario', 'proveedor', 'nombre_snapshot', 'requerido', 'estado', 'comentario')


@admin.register(ActividadItinerario)
class ActividadItinerarioAdmin(admin.ModelAdmin):
    save_on_top = True
    autocomplete_fields = ('evento', 'servicio_evento', 'responsable', 'proveedor')
    inlines = (ParticipanteActividadInline,)
    list_display = (
        'fecha',
        'hora_inicio',
        'tipo',
        'titulo',
        'evento',
        'categoria',
        'responsable',
        'proveedor',
        'estado',
    )
    list_filter = ('tipo', 'evento', 'fecha', 'categoria', 'prioridad', 'estado', 'responsable')
    search_fields = (
        'titulo',
        'descripcion',
        'ubicacion',
        'evento__nombre_evento',
        'evento__novio',
        'evento__novia',
        'proveedor__nombre_comercial',
        'responsable__username',
        'responsable__first_name',
        'responsable__last_name',
    )
    date_hierarchy = 'fecha'
    fieldsets = (
        ('Evento', {
            'fields': ('evento', 'servicio_evento', 'tipo', 'categoria', 'estado', 'prioridad')
        }),
        ('Agenda', {
            'fields': (
                'titulo',
                'descripcion',
                'fecha',
                'hora_inicio',
                'hora_fin',
                'ubicacion',
                'orden',
            )
        }),
        ('Responsables', {
            'fields': ('responsable', 'proveedor')
        }),
        ('Notas', {
            'fields': ('notas',)
        }),
    )


@admin.register(ParticipanteActividad)
class ParticipanteActividadAdmin(admin.ModelAdmin):
    list_display = ('actividad', 'rol', 'nombre_visible', 'estado', 'requerido', 'respondido_en')
    list_filter = ('rol', 'estado', 'requerido')
    autocomplete_fields = ('actividad', 'usuario', 'proveedor')
    search_fields = ('actividad__titulo', 'usuario__username', 'proveedor__nombre_comercial', 'nombre_snapshot')
