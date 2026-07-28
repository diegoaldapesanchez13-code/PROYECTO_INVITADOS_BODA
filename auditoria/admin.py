from django.contrib import admin

from .models import RegistroAuditoria


@admin.register(RegistroAuditoria)
class RegistroAuditoriaAdmin(admin.ModelAdmin):
    list_display = ('fecha', 'usuario', 'empresa', 'evento', 'accion', 'modelo', 'objeto_id', 'direccion_ip')
    list_filter = ('accion', 'modelo', 'empresa')
    search_fields = ('usuario__username', 'empresa__nombre_comercial', 'accion', 'descripcion', 'objeto_id')
    readonly_fields = (
        'usuario',
        'empresa',
        'evento',
        'accion',
        'modelo',
        'objeto_id',
        'descripcion',
        'valores_anteriores',
        'valores_nuevos',
        'direccion_ip',
        'user_agent',
        'fecha',
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
