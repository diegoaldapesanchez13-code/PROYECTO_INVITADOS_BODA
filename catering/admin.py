from django.contrib import admin

from .models import (
    Alimento,
    CateringEvento,
    CategoriaAlimento,
    PaqueteBuffet,
    PaqueteBuffetAlimento,
)


class PaqueteBuffetAlimentoInline(admin.TabularInline):
    model = PaqueteBuffetAlimento
    extra = 3
    autocomplete_fields = ('alimento',)


@admin.register(CategoriaAlimento)
class CategoriaAlimentoAdmin(admin.ModelAdmin):
    list_display = ('nombre',)
    search_fields = ('nombre',)


@admin.register(Alimento)
class AlimentoAdmin(admin.ModelAdmin):
    save_on_top = True
    list_display = (
        'nombre',
        'categoria',
        'vegetariano',
        'vegano',
        'sin_gluten',
        'contiene_alergenos',
        'activo',
    )
    list_filter = (
        'categoria',
        'vegetariano',
        'vegano',
        'sin_gluten',
        'contiene_alergenos',
        'activo',
    )
    search_fields = ('nombre', 'descripcion', 'categoria__nombre')


@admin.register(PaqueteBuffet)
class PaqueteBuffetAdmin(admin.ModelAdmin):
    save_on_top = True
    autocomplete_fields = ('proveedor',)
    inlines = [PaqueteBuffetAlimentoInline]
    list_display = (
        'nombre',
        'proveedor',
        'personas_incluidas',
        'precio_base',
        'precio_por_persona_extra',
        'precio_por_nino',
        'activo',
    )
    list_filter = ('activo', 'proveedor')
    search_fields = ('nombre', 'descripcion', 'proveedor__nombre_comercial')


@admin.register(PaqueteBuffetAlimento)
class PaqueteBuffetAlimentoAdmin(admin.ModelAdmin):
    autocomplete_fields = ('paquete', 'alimento')
    list_display = ('paquete', 'alimento', 'cantidad_incluida')
    list_filter = ('paquete', 'alimento__categoria')
    search_fields = ('paquete__nombre', 'alimento__nombre')


@admin.register(CateringEvento)
class CateringEventoAdmin(admin.ModelAdmin):
    save_on_top = True
    autocomplete_fields = ('evento', 'proveedor', 'paquete_buffet')
    filter_horizontal = ('alimentos_seleccionados',)
    list_display = (
        'evento',
        'proveedor',
        'paquete_buffet',
        'total_personas',
        'precio_total',
        'fecha_degustacion',
        'hora_servicio',
    )
    list_filter = ('evento', 'proveedor', 'paquete_buffet', 'fecha_degustacion')
    search_fields = (
        'evento__nombre_evento',
        'evento__novio',
        'evento__novia',
        'proveedor__nombre_comercial',
        'paquete_buffet__nombre',
        'observaciones',
    )
    date_hierarchy = 'fecha_degustacion'
    readonly_fields = ('total_personas',)
    fieldsets = (
        ('Evento y proveedor', {
            'fields': ('evento', 'proveedor', 'paquete_buffet')
        }),
        ('Personas y precio', {
            'fields': (
                'cantidad_adultos',
                'cantidad_ninos',
                'cantidad_proveedores',
                'total_personas',
                'precio_total',
            )
        }),
        ('Menu seleccionado', {
            'fields': ('alimentos_seleccionados',)
        }),
        ('Horarios', {
            'fields': (
                'fecha_degustacion',
                'horario_montaje',
                'hora_servicio',
                'duracion_servicio',
            )
        }),
        ('Observaciones', {
            'fields': ('observaciones',)
        }),
    )

# Register your models here.
