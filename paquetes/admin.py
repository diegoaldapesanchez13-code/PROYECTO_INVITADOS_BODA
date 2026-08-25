from django.contrib import admin, messages
from django.core.exceptions import ValidationError

from .models import (
    PaqueteBoda,
    PaqueteMediaComercial,
    PaqueteServicio,
    PropuestaEvento,
    PropuestaLinea,
)


class PaqueteServicioInline(admin.TabularInline):
    model = PaqueteServicio
    extra = 1
    autocomplete_fields = ('servicio_catalogo',)


class PaqueteMediaComercialInline(admin.TabularInline):
    model = PaqueteMediaComercial
    extra = 1


@admin.register(PaqueteBoda)
class PaqueteBodaAdmin(admin.ModelAdmin):
    save_on_top = True
    inlines = [PaqueteServicioInline, PaqueteMediaComercialInline]
    list_display = (
        'nombre',
        'empresa',
        'numero_personas_incluidas',
        'precio_base',
        'precio_adulto',
        'precio_nino',
        'cargo_fijo',
        'activo',
    )
    list_filter = ('empresa', 'activo')
    search_fields = ('nombre', 'descripcion', 'empresa__nombre_comercial')
    fieldsets = (
        ('Paquete', {
            'fields': (
                'activo',
                'empresa',
                'nombre',
                'descripcion',
                'numero_personas_incluidas',
                'precio_base',
                'precio_adulto',
                'precio_nino',
                'cargo_fijo',
                'capacidad_minima_recomendada',
                'capacidad_maxima_recomendada',
                'duracion_evento',
                'portada',
                'pdf_comercial',
            )
        }),
    )


@admin.register(PaqueteServicio)
class PaqueteServicioAdmin(admin.ModelAdmin):
    autocomplete_fields = ('paquete', 'servicio_catalogo')
    list_display = ('paquete', 'servicio_catalogo', 'cantidad', 'orden', 'incluido', 'obligatorio')
    list_filter = ('paquete', 'incluido', 'obligatorio')
    search_fields = ('paquete__nombre', 'servicio_catalogo__nombre', 'notas')


@admin.register(PaqueteMediaComercial)
class PaqueteMediaComercialAdmin(admin.ModelAdmin):
    autocomplete_fields = ('paquete',)
    list_display = ('paquete', 'tipo', 'titulo', 'orden')
    list_filter = ('tipo', 'paquete')
    search_fields = ('paquete__nombre', 'titulo')


class PropuestaLineaInline(admin.TabularInline):
    model = PropuestaLinea
    extra = 0
    autocomplete_fields = ('servicio_catalogo',)
    readonly_fields = ('subtotal', 'snapshot_linea')


@admin.register(PropuestaEvento)
class PropuestaEventoAdmin(admin.ModelAdmin):
    save_on_top = True
    autocomplete_fields = ('empresa', 'evento', 'sede', 'paquete', 'created_by', 'updated_by')
    inlines = [PropuestaLineaInline]
    readonly_fields = ('subtotal_base', 'subtotal', 'total', 'version_calculo', 'desglose_calculado')
    list_display = ('evento', 'paquete', 'estado', 'adultos', 'ninos', 'descuento', 'total', 'updated_at')
    list_filter = ('empresa', 'estado', 'paquete')
    search_fields = ('evento__nombre_evento', 'evento__novio', 'evento__novia', 'paquete__nombre', 'notas_comerciales')


@admin.register(PropuestaLinea)
class PropuestaLineaAdmin(admin.ModelAdmin):
    autocomplete_fields = ('propuesta', 'servicio_catalogo')
    readonly_fields = ('subtotal', 'snapshot_linea')
    list_display = ('propuesta', 'tipo', 'nombre', 'modo_precio', 'tarifa', 'cantidad', 'subtotal', 'activo')
    list_filter = ('tipo', 'modo_precio', 'activo')
    search_fields = ('propuesta__evento__nombre_evento', 'nombre', 'descripcion')
