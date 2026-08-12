from django.contrib import admin

from .models import (
    EtiquetaProveedor,
    PersonalEvento,
    Proveedor,
    ServicioCatalogoProveedor,
    ServicioEvento,
)


@admin.register(Proveedor)
class ProveedorAdmin(admin.ModelAdmin):
    save_on_top = True
    list_display = (
        'nombre_comercial',
        'empresa',
        'usuario',
        'tipo_proveedor',
        'nombre_contacto',
        'contacto_operativo',
        'visible_para_wedding_planners',
        'telefono',
        'correo',
        'calificacion',
        'activo',
    )
    list_filter = ('empresa', 'tipo_proveedor', 'visible_para_wedding_planners', 'activo')
    search_fields = (
        'nombre_comercial',
        'razon_social',
        'nombre_contacto',
        'telefono',
        'correo',
        'contacto_operativo',
        'telefono_operativo',
        'correo_operativo',
        'empresa__nombre_comercial',
    )
    fieldsets = (
        ('Datos principales', {
            'fields': (
                'activo',
                'empresa',
                'usuario',
                'nombre_comercial',
                'razon_social',
                'rfc',
                'tipo_proveedor',
                'calificacion',
                'visible_para_wedding_planners',
            )
        }),
        ('Contacto administrativo', {
            'fields': (
                'nombre_contacto',
                'telefono',
                'correo',
                'direccion',
                'sitio_web',
                'redes_sociales',
            )
        }),
        ('Contacto operativo para planners', {
            'fields': (
                'contacto_operativo',
                'telefono_operativo',
                'correo_operativo',
            )
        }),
        ('Notas', {
            'fields': ('descripcion', 'datos_bancarios', 'notas_privadas')
        }),
    )


@admin.register(EtiquetaProveedor)
class EtiquetaProveedorAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'empresa', 'activa')
    list_filter = ('empresa', 'activa')
    search_fields = ('nombre', 'empresa__nombre_comercial')


@admin.register(ServicioCatalogoProveedor)
class ServicioCatalogoProveedorAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'proveedor', 'empresa', 'categoria', 'costo_referencia', 'precio_referencia_cliente', 'activo')
    list_filter = ('empresa', 'activo', 'categoria')
    search_fields = ('nombre', 'descripcion', 'proveedor__nombre_comercial')
    autocomplete_fields = ('proveedor', 'empresa')
    filter_horizontal = ('etiquetas',)


@admin.register(ServicioEvento)
class ServicioEventoAdmin(admin.ModelAdmin):
    save_on_top = True
    autocomplete_fields = ('proveedor', 'evento')
    list_display = (
        'nombre_servicio',
        'evento',
        'proveedor',
        'origen',
        'modalidad',
        'estado_comercial',
        'estado_operativo',
        'fecha_servicio',
        'costo_total',
        'anticipo',
        'saldo_pendiente',
    )
    list_filter = ('evento', 'origen', 'modalidad', 'estado_comercial', 'estado_operativo', 'fecha_servicio', 'proveedor__tipo_proveedor')
    search_fields = (
        'nombre_servicio',
        'descripcion',
        'proveedor__nombre_comercial',
        'evento__nombre_evento',
        'evento__novio',
        'evento__novia',
    )
    date_hierarchy = 'fecha_servicio'
    readonly_fields = ('saldo_pendiente',)
    fieldsets = (
        ('Evento y proveedor', {
            'fields': ('evento', 'proveedor', 'servicio_catalogo', 'origen', 'modalidad', 'estado', 'estado_comercial', 'estado_operativo')
        }),
        ('Servicio', {
            'fields': (
                'nombre_servicio',
                'descripcion',
                'fecha_servicio',
                'hora_inicio',
                'hora_fin',
                'lugar',
            )
        }),
        ('Pagos', {
            'fields': (
                'costo_total',
                'costo_proveedor',
                'precio_cliente',
                'ajuste_cliente',
                'anticipo',
                'saldo_pendiente',
                'fecha_limite_pago',
            )
        }),
        ('Documentos', {
            'fields': ('contrato', 'cotizacion', 'comprobante_pago')
        }),
        ('Notas', {
            'fields': ('notas', 'notas_internas', 'proveedor_nombre_snapshot', 'catalogo_nombre_snapshot', 'catalogo_descripcion_snapshot')
        }),
    )


@admin.register(PersonalEvento)
class PersonalEventoAdmin(admin.ModelAdmin):
    save_on_top = True
    autocomplete_fields = ('evento', 'proveedor')
    list_display = (
        'nombre',
        'evento',
        'tipo_personal',
        'proveedor',
        'hora_entrada',
        'hora_salida',
        'area_asignada',
        'estado',
    )
    list_filter = ('evento', 'tipo_personal', 'estado', 'proveedor')
    search_fields = (
        'nombre',
        'telefono',
        'area_asignada',
        'mesas_asignadas',
        'evento__nombre_evento',
    )
    fieldsets = (
        ('Asignacion', {
            'fields': ('evento', 'proveedor', 'tipo_personal', 'estado')
        }),
        ('Persona', {
            'fields': ('nombre', 'telefono', 'costo')
        }),
        ('Horario y area', {
            'fields': (
                'hora_entrada',
                'hora_salida',
                'area_asignada',
                'mesas_asignadas',
                'uniforme',
            )
        }),
        ('Notas', {
            'fields': ('notas', 'notas_internas', 'proveedor_nombre_snapshot', 'catalogo_nombre_snapshot', 'catalogo_descripcion_snapshot')
        }),
    )

# Register your models here.
