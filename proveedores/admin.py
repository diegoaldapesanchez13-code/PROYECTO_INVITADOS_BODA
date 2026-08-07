from django.contrib import admin

from .models import PersonalEvento, Proveedor, ServicioEvento


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


@admin.register(ServicioEvento)
class ServicioEventoAdmin(admin.ModelAdmin):
    save_on_top = True
    autocomplete_fields = ('proveedor', 'evento')
    list_display = (
        'nombre_servicio',
        'evento',
        'proveedor',
        'estado',
        'fecha_servicio',
        'costo_total',
        'anticipo',
        'saldo_pendiente',
    )
    list_filter = ('evento', 'estado', 'fecha_servicio', 'proveedor__tipo_proveedor')
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
            'fields': ('evento', 'proveedor', 'estado')
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
                'anticipo',
                'saldo_pendiente',
                'fecha_limite_pago',
            )
        }),
        ('Documentos', {
            'fields': ('contrato', 'cotizacion', 'comprobante_pago')
        }),
        ('Notas', {
            'fields': ('notas',)
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
            'fields': ('notas',)
        }),
    )

# Register your models here.
