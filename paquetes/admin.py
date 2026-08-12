from django.contrib import admin, messages
from django.core.exceptions import ValidationError

from .models import PaqueteBoda, PaqueteEvento, ServicioPaquete
from .services import capturar_snapshot_paquete, materializar_servicios_paquete


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
    readonly_fields = (
        'snapshot_paquete',
        'snapshot_generado_en',
        'materializado_en',
        'materializacion_version',
    )
    actions = ('capturar_snapshot', 'materializar_servicios')
    list_display = (
        'evento',
        'paquete',
        'estado',
        'precio_acordado',
        'descuento',
        'total',
        'tiene_snapshot',
        'esta_materializado',
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
        ('K.8.3 - Snapshot y materializacion', {
            'classes': ('collapse',),
            'fields': (
                'snapshot_generado_en',
                'materializado_en',
                'materializacion_version',
                'snapshot_paquete',
            ),
        }),
    )

    @admin.display(boolean=True, description='Snapshot')
    def tiene_snapshot(self, obj):
        return obj.tiene_snapshot

    @admin.display(boolean=True, description='Materializado')
    def esta_materializado(self, obj):
        return obj.esta_materializado

    @admin.action(description='K.8.3 - Capturar snapshot contractual')
    def capturar_snapshot(self, request, queryset):
        ok = 0
        errores = 0
        for paquete_evento in queryset:
            try:
                capturar_snapshot_paquete(paquete_evento)
                ok += 1
            except ValidationError as exc:
                errores += 1
                self.message_user(request, str(exc), level=messages.ERROR)
        if ok:
            self.message_user(request, f'Snapshot capturado en {ok} paquete(s).', level=messages.SUCCESS)
        if errores:
            self.message_user(request, f'{errores} paquete(s) no pudieron procesarse.', level=messages.WARNING)

    @admin.action(description='K.8.3 - Materializar servicios del paquete')
    def materializar_servicios(self, request, queryset):
        paquetes = 0
        creados = 0
        actualizados = 0
        errores = 0
        for paquete_evento in queryset:
            try:
                resultado = materializar_servicios_paquete(paquete_evento)
                paquetes += 1
                creados += resultado['creados']
                actualizados += resultado['actualizados']
            except ValidationError as exc:
                errores += 1
                self.message_user(request, str(exc), level=messages.ERROR)
        if paquetes:
            self.message_user(
                request,
                f'{paquetes} paquete(s) materializados: {creados} servicios creados y {actualizados} actualizados.',
                level=messages.SUCCESS,
            )
        if errores:
            self.message_user(request, f'{errores} paquete(s) no pudieron procesarse.', level=messages.WARNING)
