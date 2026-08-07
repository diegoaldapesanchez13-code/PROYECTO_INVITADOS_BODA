from django.contrib import admin
from django.utils.html import format_html

from .models import ElementoDecoracion


def preview_archivo(obj, campo):
    archivo = getattr(obj, campo, None)
    if not archivo:
        return 'Sin archivo'
    return format_html(
        '<a href="{0}" target="_blank" rel="noopener">'
        '<img src="{0}" alt="" style="width:88px;height:64px;object-fit:cover;border-radius:6px;border:1px solid #ddd;">'
        '</a>',
        archivo.url,
    )


@admin.register(ElementoDecoracion)
class ElementoDecoracionAdmin(admin.ModelAdmin):
    save_on_top = True
    autocomplete_fields = ('evento', 'proveedor')
    list_display = (
        'nombre',
        'evento',
        'categoria',
        'proveedor',
        'cantidad',
        'costo',
        'estado',
        'aprobado_cliente',
    )
    list_filter = ('evento', 'categoria', 'estado', 'aprobado_cliente', 'proveedor')
    search_fields = (
        'nombre',
        'descripcion',
        'color',
        'material',
        'evento__nombre_evento',
        'evento__novio',
        'evento__novia',
        'proveedor__nombre_comercial',
    )
    readonly_fields = ('preview_referencia', 'preview_final', 'fecha_actualizacion')
    fieldsets = (
        ('Evento y categoria', {
            'fields': ('evento', 'categoria', 'estado', 'aprobado_cliente')
        }),
        ('Elemento', {
            'fields': (
                'nombre',
                'descripcion',
                'cantidad',
                'color',
                'material',
                'proveedor',
                'costo',
            )
        }),
        ('Imagenes', {
            'fields': (
                ('imagen_referencia', 'preview_referencia'),
                ('imagen_final', 'preview_final'),
            )
        }),
        ('Notas', {
            'fields': ('notas', 'fecha_actualizacion')
        }),
    )

    def preview_referencia(self, obj):
        return preview_archivo(obj, 'imagen_referencia')

    preview_referencia.short_description = 'Referencia'

    def preview_final(self, obj):
        return preview_archivo(obj, 'imagen_final')

    preview_final.short_description = 'Final'

# Register your models here.
