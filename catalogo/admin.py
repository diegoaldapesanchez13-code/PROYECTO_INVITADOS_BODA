from django.contrib import admin

from .models import ServicioCatalogo, ServicioCatalogoArchivo


class ServicioCatalogoArchivoInline(admin.TabularInline):
    model = ServicioCatalogoArchivo
    extra = 0


@admin.register(ServicioCatalogo)
class ServicioCatalogoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'empresa', 'categoria', 'unidad', 'activo', 'updated_at')
    list_filter = ('empresa', 'categoria', 'unidad', 'activo')
    search_fields = ('nombre', 'descripcion', 'empresa__nombre_comercial')
    autocomplete_fields = ('empresa',)
    inlines = [ServicioCatalogoArchivoInline]


@admin.register(ServicioCatalogoArchivo)
class ServicioCatalogoArchivoAdmin(admin.ModelAdmin):
    list_display = ('servicio', 'tipo', 'titulo', 'orden', 'created_at')
    list_filter = ('tipo', 'servicio__empresa')
    search_fields = ('titulo', 'servicio__nombre', 'servicio__empresa__nombre_comercial')
    autocomplete_fields = ('servicio',)
