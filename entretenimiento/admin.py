from django.contrib import admin

from .models import CancionEvento, EntretenimientoEvento


class CancionEventoInline(admin.TabularInline):
    model = CancionEvento
    extra = 4
    fields = ('tipo_momento', 'nombre_cancion', 'artista', 'enlace', 'orden', 'notas')


@admin.register(EntretenimientoEvento)
class EntretenimientoEventoAdmin(admin.ModelAdmin):
    save_on_top = True
    autocomplete_fields = ('evento', 'proveedor')
    inlines = [CancionEventoInline]
    list_display = (
        'nombre_artista',
        'evento',
        'tipo',
        'proveedor',
        'hora_inicio',
        'hora_fin',
        'estado',
        'costo',
        'anticipo',
        'saldo_pendiente',
    )
    list_filter = ('evento', 'tipo', 'estado', 'proveedor')
    search_fields = (
        'nombre_artista',
        'requerimientos_tecnicos',
        'evento__nombre_evento',
        'evento__novio',
        'evento__novia',
        'proveedor__nombre_comercial',
    )
    readonly_fields = ('saldo_pendiente',)
    fieldsets = (
        ('Evento y proveedor', {
            'fields': ('evento', 'tipo', 'proveedor', 'estado')
        }),
        ('Presentacion', {
            'fields': (
                'nombre_artista',
                'hora_inicio',
                'hora_fin',
                'duracion',
                'requerimientos_tecnicos',
            )
        }),
        ('Costos', {
            'fields': ('costo', 'anticipo', 'saldo_pendiente')
        }),
        ('Notas', {
            'fields': ('notas',)
        }),
    )


@admin.register(CancionEvento)
class CancionEventoAdmin(admin.ModelAdmin):
    save_on_top = True
    autocomplete_fields = ('evento', 'entretenimiento')
    list_display = ('nombre_cancion', 'artista', 'evento', 'tipo_momento', 'orden')
    list_filter = ('evento', 'tipo_momento')
    search_fields = (
        'nombre_cancion',
        'artista',
        'evento__nombre_evento',
        'evento__novio',
        'evento__novia',
    )
    fields = (
        'evento',
        'entretenimiento',
        'tipo_momento',
        'nombre_cancion',
        'artista',
        'enlace',
        'orden',
        'notas',
    )

# Register your models here.
