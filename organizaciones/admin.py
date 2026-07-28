from django.contrib import admin

from .models import EmpresaSuscriptora, MembresiaEmpresa, SedeEvento


class SedeEventoInline(admin.TabularInline):
    model = SedeEvento
    extra = 0


class MembresiaEmpresaInline(admin.TabularInline):
    model = MembresiaEmpresa
    extra = 0
    autocomplete_fields = ('usuario',)


@admin.register(EmpresaSuscriptora)
class EmpresaSuscriptoraAdmin(admin.ModelAdmin):
    list_display = ('nombre_comercial', 'estado', 'plan', 'activo', 'contacto_email', 'max_eventos_activos', 'max_usuarios')
    list_filter = ('estado', 'activo', 'plan')
    search_fields = ('nombre_comercial', 'razon_social', 'rfc', 'contacto_email')
    prepopulated_fields = {'slug': ('nombre_comercial',)}
    inlines = [SedeEventoInline, MembresiaEmpresaInline]


@admin.register(SedeEvento)
class SedeEventoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'empresa', 'tipo', 'capacidad_maxima', 'precio_base', 'activa')
    list_filter = ('empresa', 'tipo', 'activa')
    search_fields = ('nombre', 'empresa__nombre_comercial', 'direccion')


@admin.register(MembresiaEmpresa)
class MembresiaEmpresaAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'empresa', 'rol', 'activo', 'puede_gestionar_catalogos')
    list_filter = ('empresa', 'rol', 'activo', 'puede_gestionar_catalogos')
    search_fields = ('usuario__username', 'usuario__first_name', 'usuario__last_name', 'empresa__nombre_comercial')
    autocomplete_fields = ('usuario', 'empresa')
