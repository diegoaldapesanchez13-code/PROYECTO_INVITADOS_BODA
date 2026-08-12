from django.contrib import admin

from .models import AsignacionMesa, Mesa


class AsignacionMesaInline(admin.TabularInline):
    model = AsignacionMesa
    extra = 4
    autocomplete_fields = ('invitado',)
    fields = ('invitado', 'numero_asiento', 'notas')


@admin.register(Mesa)
class MesaAdmin(admin.ModelAdmin):
    save_on_top = True
    autocomplete_fields = ('evento', 'mesero')
    inlines = [AsignacionMesaInline]
    list_display = (
        'nombre',
        'evento',
        'numero',
        'tipo',
        'zona',
        'capacidad',
        'lugares_ocupados',
        'lugares_disponibles',
        'excedida',
        'mesero',
    )
    list_filter = ('evento', 'tipo', 'zona', 'mesero')
    search_fields = (
        'nombre',
        'zona',
        'evento__nombre_evento',
        'evento__novio',
        'evento__novia',
        'mesero__nombre',
    )
    readonly_fields = ('lugares_ocupados', 'lugares_disponibles', 'excedida')
    fieldsets = (
        ('Evento y mesa', {
            'fields': (
                'evento',
                'nombre',
                'numero',
                'tipo',
                'capacidad',
                'zona',
                'mesero',
            )
        }),
        ('Plano visual', {
            'description': 'Posición y tamaño de la mesa dentro del plano visual.',
            'fields': (
                'posicion_x',
                'posicion_y',
                'ancho',
                'alto',
                'rotacion',
            )
        }),
        ('Estado', {
            'fields': ('lugares_ocupados', 'lugares_disponibles', 'excedida')
        }),
        ('Notas', {
            'fields': ('notas',)
        }),
    )


@admin.register(AsignacionMesa)
class AsignacionMesaAdmin(admin.ModelAdmin):
    save_on_top = True
    autocomplete_fields = ('mesa', 'invitado')
    list_display = ('mesa', 'invitado', 'grupo', 'numero_asiento')
    list_filter = ('mesa__evento', 'mesa')
    search_fields = (
        'mesa__nombre',
        'invitado__nombre',
        'invitado__apellidos',
        'invitado__grupo__nombre_grupo',
    )
    fields = ('mesa', 'invitado', 'numero_asiento', 'notas')

    @admin.display(description='Invitación')
    def grupo(self, obj):
        return obj.invitado.grupo
