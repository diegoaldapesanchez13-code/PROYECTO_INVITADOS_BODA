from django.contrib import admin

from .models import PagoSuscripcion, PlanSuscripcion, SuscripcionEmpresa


@admin.register(PlanSuscripcion)
class PlanSuscripcionAdmin(admin.ModelAdmin):
    list_display = (
        'nombre',
        'precio_mensual',
        'precio_anual',
        'limite_usuarios',
        'limite_eventos_activos',
        'permite_api',
        'activo',
    )
    list_filter = ('activo', 'permite_api', 'permite_reportes', 'permite_personalizacion')
    search_fields = ('nombre', 'descripcion')


class PagoSuscripcionInline(admin.TabularInline):
    model = PagoSuscripcion
    extra = 0
    fields = ('monto', 'fecha_vencimiento', 'fecha_pago', 'estado', 'metodo_pago', 'referencia')
    readonly_fields = ('fecha_registro',)


@admin.register(SuscripcionEmpresa)
class SuscripcionEmpresaAdmin(admin.ModelAdmin):
    list_display = (
        'empresa',
        'plan',
        'estado',
        'fecha_inicio',
        'fecha_vencimiento',
        'fecha_periodo_gracia',
        'bloqueada_manualmente',
    )
    list_filter = ('estado', 'plan', 'bloqueada_manualmente', 'renovacion_automatica')
    search_fields = ('empresa__nombre_comercial', 'empresa__razon_social', 'motivo_bloqueo')
    autocomplete_fields = ('empresa', 'plan')
    inlines = [PagoSuscripcionInline]


@admin.register(PagoSuscripcion)
class PagoSuscripcionAdmin(admin.ModelAdmin):
    list_display = ('empresa', 'suscripcion', 'monto', 'fecha_vencimiento', 'fecha_pago', 'estado')
    list_filter = ('estado', 'metodo_pago')
    search_fields = ('empresa__nombre_comercial', 'referencia', 'notas')
    autocomplete_fields = ('empresa', 'suscripcion', 'registrado_por')
    readonly_fields = ('fecha_registro',)
