from django.contrib import admin

from .models import CategoriaGasto, GastoEvento, PagoEvento, PagoClienteEvento


class PagoEventoInline(admin.TabularInline):
    model = PagoEvento
    extra = 2
    fields = ('monto', 'fecha_pago', 'metodo_pago', 'referencia', 'comprobante', 'notas')


@admin.register(CategoriaGasto)
class CategoriaGastoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'activo')
    list_filter = ('activo',)
    search_fields = ('nombre',)


@admin.register(GastoEvento)
class GastoEventoAdmin(admin.ModelAdmin):
    save_on_top = True
    autocomplete_fields = ('evento', 'categoria', 'proveedor')
    inlines = [PagoEventoInline]
    list_display = (
        'concepto',
        'evento',
        'categoria',
        'proveedor',
        'monto_objetivo',
        'total_pagado',
        'saldo_pendiente',
        'fecha_limite',
        'estado',
        'esta_vencido',
    )
    list_filter = ('evento', 'categoria', 'estado', 'fecha_limite', 'proveedor')
    search_fields = (
        'concepto',
        'notas',
        'evento__nombre_evento',
        'evento__novio',
        'evento__novia',
        'proveedor__nombre_comercial',
    )
    date_hierarchy = 'fecha_limite'
    readonly_fields = ('total_pagado', 'saldo_pendiente', 'porcentaje_pagado', 'esta_vencido')
    fieldsets = (
        ('Evento y categoria', {
            'fields': ('evento', 'categoria', 'proveedor', 'estado')
        }),
        ('Concepto', {
            'fields': ('concepto', 'notas')
        }),
        ('Montos', {
            'fields': (
                'monto_estimado',
                'monto_real',
                'total_pagado',
                'saldo_pendiente',
                'porcentaje_pagado',
            )
        }),
        ('Vencimiento', {
            'fields': ('fecha_limite', 'esta_vencido')
        }),
    )


@admin.register(PagoEvento)
class PagoEventoAdmin(admin.ModelAdmin):
    save_on_top = True
    autocomplete_fields = ('gasto',)
    list_display = ('gasto', 'monto', 'fecha_pago', 'metodo_pago', 'referencia')
    list_filter = ('gasto__evento', 'metodo_pago', 'fecha_pago')
    search_fields = (
        'gasto__concepto',
        'gasto__evento__nombre_evento',
        'referencia',
        'notas',
    )
    date_hierarchy = 'fecha_pago'

# Register your models here.


@admin.register(PagoClienteEvento)
class PagoClienteEventoAdmin(admin.ModelAdmin):
    list_display = ('evento', 'concepto', 'monto', 'fecha_pago', 'estado', 'registrado_por', 'revisado_por')
    list_filter = ('estado', 'metodo_pago', 'fecha_pago', 'evento')
    search_fields = ('evento__nombre_evento', 'concepto', 'referencia', 'comentario_cliente', 'comentario_equipo')
