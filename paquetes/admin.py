from django.contrib import admin

from .models import PaqueteBoda, PaqueteEvento, ServicioPaquete


class ServicioPaqueteInline(admin.TabularInline):
    model = ServicioPaquete
    extra = 5


@admin.register(PaqueteBoda)
class PaqueteBodaAdmin(admin.ModelAdmin):
    save_on_top = True
    inlines = [ServicioPaqueteInline]
    list_display = (
        'nombre',
        'empresa',
        'numero_personas_incluidas',
        'precio_base',
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
            )
        }),
    )


@admin.register(ServicioPaquete)
class ServicioPaqueteAdmin(admin.ModelAdmin):
    autocomplete_fields = ('paquete',)
    list_display = (
        'paquete',
        'tipo_servicio',
        'descripcion',
        'cantidad',
        'precio_incluido',
    )
    list_filter = ('paquete', 'tipo_servicio')
    search_fields = ('paquete__nombre', 'descripcion')


@admin.register(PaqueteEvento)
class PaqueteEventoAdmin(admin.ModelAdmin):
    save_on_top = True
    autocomplete_fields = ('evento', 'paquete')
    list_display = (
        'evento',
        'paquete',
        'estado',
        'precio_acordado',
        'descuento',
        'total',
    )
    list_filter = ('evento', 'estado', 'paquete')
    search_fields = (
        'evento__nombre_evento',
        'evento__novio',
        'evento__novia',
        'paquete__nombre',
        'servicios_adicionales',
    )
    fieldsets = (
        ('Evento y paquete', {
            'fields': ('evento', 'paquete', 'estado')
        }),
        ('Precio', {
            'fields': (
                'precio_acordado',
                'descuento',
                'total',
            )
        }),
        ('Personalizacion', {
            'fields': ('servicios_adicionales', 'notas')
        }),
    )

# Register your models here.
