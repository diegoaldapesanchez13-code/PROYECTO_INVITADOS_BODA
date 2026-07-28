from django.contrib import admin
from django.utils.html import format_html

from .models import DocumentoEvento


@admin.register(DocumentoEvento)
class DocumentoEventoAdmin(admin.ModelAdmin):
    save_on_top = True
    autocomplete_fields = ('evento', 'proveedor', 'cargado_por')
    list_display = (
        'titulo',
        'evento',
        'tipo_documento',
        'proveedor',
        'visible_cliente',
        'fecha_carga',
        'abrir_archivo',
    )
    list_filter = ('evento', 'tipo_documento', 'visible_cliente', 'proveedor', 'fecha_carga')
    search_fields = (
        'titulo',
        'descripcion',
        'evento__nombre_evento',
        'evento__novio',
        'evento__novia',
        'proveedor__nombre_comercial',
        'cargado_por__username',
    )
    readonly_fields = ('fecha_carga', 'abrir_archivo')
    date_hierarchy = 'fecha_carga'
    fields = (
        'evento',
        'tipo_documento',
        'titulo',
        'archivo',
        'abrir_archivo',
        'proveedor',
        'descripcion',
        'cargado_por',
        'visible_cliente',
        'fecha_carga',
    )

    def abrir_archivo(self, obj):
        if not obj or not obj.archivo:
            return 'Sin archivo'
        return format_html(
            '<a class="admin-action-button small" href="{}" target="_blank" rel="noopener">Abrir</a>',
            obj.archivo.url,
        )

    abrir_archivo.short_description = 'Archivo'

# Register your models here.
