from django.contrib import admin
from .models import Grupoinvitacion, Invitado, EventoBoda

# Inline para editar invitados desde el formulario del grupo.
class InvitadoInline(admin.TabularInline):
    model = Invitado
    extra = 1

# Registra el modelo EventoBoda en el panel administrativo.
admin.site.register(EventoBoda)


@admin.register(Grupoinvitacion)
class GrupoInvitacionAdmin(admin.ModelAdmin):
    list_display = (
        'nombre_grupo',
        'tipo',
        'cantidad_maxima',
        'total_invitados',
        'total_confirmados',
        'confirmado',
        'fecha_creacion'
    )

    list_filter = ('tipo', 'confirmado')
    search_fields = ('nombre_grupo',)

    inlines = [InvitadoInline]

    readonly_fields = ('codigo', 'fecha_creacion')

    def total_invitados(self, obj):
        return obj.invitados.count()

    def total_confirmados(self, obj):
        return obj.invitados.filter(asistira=True).count()

    def get_readonly_fields(self, request, obj=None):
        if obj:
           return self.readonly_fields + ('confirmado',)
        return self.readonly_fields

    total_invitados.short_description = 'Invitados'
    total_confirmados.short_description = 'Asistirán'


@admin.register(Invitado)
class InvitadoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'grupo', 'asistira')
    list_filter = ('asistira',)
    search_fields = ('nombre',)