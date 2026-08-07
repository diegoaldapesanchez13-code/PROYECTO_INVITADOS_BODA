from django.contrib import admin

from .models import TareaEvento


@admin.register(TareaEvento)
class TareaEventoAdmin(admin.ModelAdmin):
    save_on_top = True
    autocomplete_fields = ('evento', 'responsable')
    list_display = (
        'titulo',
        'evento',
        'categoria',
        'responsable',
        'prioridad',
        'estado',
        'porcentaje_avance',
        'fecha_limite',
        'esta_vencida',
    )
    list_filter = ('evento', 'categoria', 'prioridad', 'estado', 'fecha_limite', 'responsable')
    search_fields = (
        'titulo',
        'descripcion',
        'notas',
        'evento__nombre_evento',
        'evento__novio',
        'evento__novia',
        'responsable__username',
        'responsable__first_name',
        'responsable__last_name',
    )
    date_hierarchy = 'fecha_limite'
    readonly_fields = ('esta_vencida', 'fecha_creacion', 'fecha_actualizacion')
    fieldsets = (
        ('Evento y estado', {
            'fields': ('evento', 'categoria', 'responsable', 'prioridad', 'estado', 'porcentaje_avance')
        }),
        ('Tarea', {
            'fields': ('titulo', 'descripcion', 'fecha_inicio', 'fecha_limite', 'esta_vencida')
        }),
        ('Evidencia y notas', {
            'fields': ('evidencia', 'notas')
        }),
        ('Auditoria', {
            'classes': ('collapse',),
            'fields': ('fecha_creacion', 'fecha_actualizacion')
        }),
    )

# Register your models here.
