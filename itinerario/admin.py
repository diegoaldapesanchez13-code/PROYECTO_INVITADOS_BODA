from django.contrib import admin

from .models import ActividadItinerario


@admin.register(ActividadItinerario)
class ActividadItinerarioAdmin(admin.ModelAdmin):
    save_on_top = True
    autocomplete_fields = ('evento', 'responsable', 'proveedor')
    list_display = (
        'hora_inicio',
        'titulo',
        'evento',
        'categoria',
        'responsable',
        'proveedor',
        'prioridad',
        'estado',
    )
    list_filter = ('evento', 'fecha', 'categoria', 'prioridad', 'estado', 'responsable')
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
            'fields': ('evento', 'categoria', 'estado', 'prioridad')
        }),
        ('Actividad', {
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

# Register your models here.
