from django import forms
from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

from .models import (
    AssetInvitacion,
    DetalleProduccionEvento,
    DisenoInvitacion,
    EnlaceRegalo,
    EventoBoda,
    FotoEvento,
    Grupoinvitacion,
    Invitado,
    ItinerarioEvento,
    MediaSeccionInvitacion,
    MenuBoda,
    PersonaCeremonia,
    PlantillaInvitacion,
    SeccionInvitacion,
    VersionDisenoInvitacion,
)


def preview_imagen(obj, campo, texto='Sin imagen'):
    archivo = getattr(obj, campo, None) if obj else None
    if not archivo:
        return format_html('<span class="admin-empty-preview">{}</span>', texto)
    extension = (archivo.name.rsplit('.', 1)[-1] if '.' in archivo.name else '').lower()
    if extension in {'mp4', 'webm', 'ogg', 'mov', 'm4v'}:
        return format_html(
            '<video class="admin-image-preview" src="{}" muted controls></video>',
            archivo.url,
        )
    return format_html(
        '<a href="{0}" target="_blank" rel="noopener">'
        '<img class="admin-image-preview" src="{0}" alt="{1}"></a>',
        archivo.url,
        campo.replace('_', ' '),
    )


class EventoBodaForm(forms.ModelForm):
    class Meta:
        model = EventoBoda
        fields = '__all__'
        widgets = {
            'color_principal': forms.TextInput(attrs={'type': 'color'}),
            'color_secundario': forms.TextInput(attrs={'type': 'color'}),
            'color_acento': forms.TextInput(attrs={'type': 'color'}),
            'mapa_misa_embed': forms.Textarea(attrs={'rows': 4}),
            'mapa_fiesta_embed': forms.Textarea(attrs={'rows': 4}),
            'mensaje_general': forms.Textarea(attrs={'rows': 3}),
            'texto_invitacion': forms.Textarea(attrs={'rows': 3}),
            'texto_detalles': forms.Textarea(attrs={'rows': 3}),
            'texto_rsvp': forms.Textarea(attrs={'rows': 3}),
            'dress_code_descripcion': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        ayudas = {
            'paleta_colores': 'Elige una paleta lista. Usa Personalizada solo si quieres ajustar colores manualmente.',
            'tipo_evento': 'Define si sera boda, XV, baby shower, bautizo, cumpleanos u otro evento.',
            'nombre_evento': 'Nombre general para dashboard y reportes. Ejemplo: XV de Camila.',
            'nombre_principal': 'Nombre que aparecera como protagonista principal de la invitacion.',
            'nombre_secundario': 'Nombre adicional. En boda suele ser el novio; en XV o baby shower puede quedar vacio.',
            'mostrar_nombre_secundario': 'Desactivalo para eventos con una sola persona protagonista.',
            'estilo_letra': 'Controla el estilo general de titulos y nombres en la invitacion.',
            'imagen_portada': 'Opcional: URL externa. Si subes foto de portada, se usa primero la foto cargada.',
            'foto_portada': 'Imagen principal de fondo para la primera pantalla.',
            'logo_portada': 'Logo, iniciales o imagen decorativa para la portada.',
            'cancion': 'Archivo de audio para la invitacion.',
            'paleta_sobre': 'Controla los colores del sobre de entrada.',
            'sello_sobre': 'Imagen opcional para el sello del sobre. Si no subes una, se usan iniciales.',
            'monograma_sobre': 'Texto corto para el sello cuando no hay imagen. Ejemplo: W&E.',
            'texto_boton_sobre': 'Texto del boton para abrir la invitacion.',
            'mapa_misa_embed': 'Pega aqui el HTML iframe de Google Maps para la ceremonia.',
            'mapa_fiesta_embed': 'Pega aqui el HTML iframe de Google Maps para la fiesta.',
            'dress_code_permitido_imagen': 'Imagen con ejemplos del dress code permitido.',
            'dress_code_prohibido_imagen': 'Imagen con ejemplos de lo que no esta permitido.',
            'fondo_invitacion': 'Fondo para la seccion tipo invitacion impresa.',
            'fondo_cuenta_regresiva': 'Fondo para la cuenta regresiva.',
            'fondo_detalles': 'Fondo para ceremonia, fiesta, mapas y dress code.',
            'fondo_album': 'Fondo para el album de fotos.',
            'fondo_menu': 'Fondo para menus.',
            'fondo_regalos': 'Fondo para regalos.',
            'fondo_rsvp': 'Fondo para confirmar asistencia.',
            'link_album_compartido': 'Link de Google Photos, Drive o formulario donde los invitados subiran fotos y videos.',
        }
        for campo, ayuda in ayudas.items():
            if campo in self.fields:
                self.fields[campo].help_text = ayuda


class GrupoInvitacionForm(forms.ModelForm):
    class Meta:
        model = Grupoinvitacion
        fields = '__all__'
        widgets = {
            'cantidad_maxima': forms.NumberInput(attrs={'min': 1}),
            'cantidad_extra_permitida': forms.NumberInput(attrs={'min': 0}),
            'acompanantes_adultos': forms.NumberInput(attrs={'min': 0}),
            'acompanantes_ninos': forms.NumberInput(attrs={'min': 0}),
            'cantidad_confirmada': forms.NumberInput(attrs={'min': 0}),
            'comentario': forms.Textarea(attrs={'rows': 3}),
            'restricciones_alimentarias': forms.Textarea(attrs={'rows': 3}),
            'alergias': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        ayudas = {
            'tipo': 'Personal: una persona principal con acompanantes permitidos. Familiar: agrega cada invitado por nombre abajo.',
            'cantidad_maxima': 'Para familiar sirve como referencia; el control real son los invitados nombrados.',
            'cantidad_extra_permitida': 'Solo para invitacion personal. Es el numero maximo de acompanantes que podra elegir.',
            'mesa': 'Mesa sugerida para todo el grupo. En familiar tambien puedes ajustar mesa por invitado.',
            'restricciones_alimentarias': 'Usalo para invitaciones personales o para notas generales de una familia.',
            'alergias': 'Ayuda a coordinar buffet y cocina.',
        }
        for campo, ayuda in ayudas.items():
            if campo in self.fields:
                self.fields[campo].help_text = ayuda


class FotoEventoInline(admin.TabularInline):
    model = FotoEvento
    extra = 3
    fields = ('preview', 'titulo', 'imagen', 'orden', 'visible')
    readonly_fields = ('preview',)
    show_change_link = True

    def preview(self, obj):
        return preview_imagen(obj, 'imagen', 'Guarda la foto para verla aqui')

    preview.short_description = 'Vista'


class EnlaceRegaloInline(admin.TabularInline):
    model = EnlaceRegalo
    extra = 2
    fields = ('tipo', 'nombre', 'url', 'banco', 'titular', 'numero_cuenta', 'clabe', 'instrucciones', 'visible')
    show_change_link = True


class ItinerarioEventoInline(admin.TabularInline):
    model = ItinerarioEvento
    extra = 3
    fields = ('hora', 'titulo', 'descripcion', 'icono', 'orden', 'visible')
    show_change_link = True


class MenuBodaInline(admin.TabularInline):
    model = MenuBoda
    extra = 2
    fields = ('nombre', 'tipo', 'descripcion', 'visible')
    show_change_link = True


class DetalleProduccionEventoInline(admin.StackedInline):
    model = DetalleProduccionEvento
    extra = 0
    max_num = 1
    fieldsets = (
        ('Contrato', {
            'fields': (
                'folio_contrato',
                'cliente_contrato',
                'arrendador',
                'lugar_contrato',
                ('adultos_contratados', 'ninos_contratados'),
                ('horas_evento', 'recepcion_hora', 'inicio_evento', 'fin_evento'),
                ('minutos_desalojo', 'costo_hora_extra'),
            )
        }),
        ('Pagos', {
            'fields': (
                ('precio_renta_salon', 'deposito_apartado'),
                ('anticipo_recibido', 'saldo_contrato', 'dias_antes_liquidacion'),
                ('banco', 'numero_cuenta', 'clabe', 'tarjeta'),
            )
        }),
        ('Montaje', {
            'fields': (
                ('color_mantel', 'color_servilleta'),
                ('tipo_mesa', 'tamano_mesa'),
                'mobiliario',
                'tipo_loza_cristaleria',
                ('diseno_carpa', 'tamano_carpa', 'color_carpa'),
                'montaje_carpa',
            )
        }),
        ('Menu y servicios', {
            'fields': (
                'menu_entrada',
                'menu_plato_fuerte',
                'menu_postre',
                'menu_trasnochado',
                'menu_infantil',
                'bebidas',
                'servicios_incluidos',
            )
        }),
        ('Notas', {
            'fields': (
                'notas_puntualidad',
                'politica_cancelacion',
                'notas_contrato',
            )
        }),
    )


class PersonaCeremoniaInline(admin.TabularInline):
    model = PersonaCeremonia
    extra = 4
    fields = ('seccion', 'etiqueta', 'nombre', 'orden', 'visible')
    show_change_link = True


class VersionDisenoInvitacionInline(admin.TabularInline):
    model = VersionDisenoInvitacion
    extra = 0
    fields = ('nombre', 'publicado', 'creado_por', 'fecha_creacion')
    readonly_fields = ('fecha_creacion',)
    show_change_link = True


@admin.register(DisenoInvitacion)
class DisenoInvitacionAdmin(admin.ModelAdmin):
    list_display = ('evento', 'nombre', 'estado', 'publicado_en', 'actualizado_por')
    list_filter = ('estado', 'evento__tipo_evento')
    search_fields = ('nombre', 'evento__novia', 'evento__novio', 'evento__nombre_evento')
    readonly_fields = ('fecha_creacion', 'fecha_actualizacion', 'publicado_en')
    inlines = [VersionDisenoInvitacionInline]


@admin.register(AssetInvitacion)
class AssetInvitacionAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'evento', 'tipo', 'visible', 'fecha_creacion')
    list_filter = ('tipo', 'visible', 'evento__tipo_evento')
    search_fields = ('titulo', 'evento__novia', 'evento__novio', 'evento__nombre_evento')
    readonly_fields = ('preview', 'fecha_creacion')

    def preview(self, obj):
        return preview_imagen(obj, 'archivo', 'Sin archivo')

    preview.short_description = 'Vista'


@admin.register(EventoBoda)
class EventoBodaAdmin(admin.ModelAdmin):
    form = EventoBodaForm
    save_on_top = True
    list_display = (
        '__str__',
        'empresa',
        'sede',
        'activo',
        'tipo_evento',
        'estado',
        'fecha_fiesta',
        'lugar_fiesta',
        'paleta_colores',
        'estilo_letra',
        'vista_previa_evento',
    )
    list_filter = (
        'activo',
        'empresa',
        'sede',
        'tipo_evento',
        'estado',
        'paleta_colores',
        'estilo_letra',
        'mostrar_album',
        'mostrar_mapa',
        'mostrar_regalos',
        'mostrar_menu',
    )
    search_fields = ('novio', 'novia', 'lugar_fiesta', 'empresa__nombre_comercial', 'sede__nombre')
    inlines = [
        DetalleProduccionEventoInline,
        PersonaCeremoniaInline,
        FotoEventoInline,
        ItinerarioEventoInline,
        EnlaceRegaloInline,
        MenuBodaInline,
    ]
    readonly_fields = (
        'vista_previa_evento',
        'muestra_paleta',
        'muestra_paleta_sobre',
        'preview_foto_portada',
        'preview_foto_ceremonia',
        'preview_foto_recepcion',
        'preview_logo_portada',
        'preview_cancion',
        'preview_sello_sobre',
        'preview_dress_permitido',
        'preview_dress_prohibido',
        'preview_fondo_invitacion',
        'preview_fondo_cuenta_regresiva',
        'preview_fondo_detalles',
        'preview_fondo_album',
        'preview_fondo_menu',
        'preview_fondo_regalos',
        'preview_fondo_rsvp',
        'fecha_creacion',
        'fecha_actualizacion',
    )

    fieldsets = (
        ('1. Tipo de evento, estado y nombres', {
            'fields': (
                'activo',
                'empresa',
                'sede',
                'tipo_evento',
                'estado',
                'nombre_evento',
                'novio',
                'novia',
                'nombre_principal',
                'nombre_secundario',
                'etiqueta_principal',
                'etiqueta_secundario',
                'mostrar_nombre_secundario',
                'frase_portada',
                'mensaje_general',
            )
        }),
        ('2. Vista rapida', {
            'description': 'Guarda el evento y crea al menos un grupo para poder abrir una invitacion de prueba.',
            'fields': (
                'vista_previa_evento',
                'muestra_paleta',
                'muestra_paleta_sobre',
            )
        }),
        ('3. Sobre de entrada', {
            'description': 'Configura el inicio tipo sobre con sello, monograma y colores.',
            'fields': (
                'paleta_sobre',
                ('sello_sobre', 'preview_sello_sobre'),
                'monograma_sobre',
                'texto_boton_sobre',
            )
        }),
        ('4. Portada, estilo y musica', {
            'description': 'Aqui controlas la primera impresion despues de abrir el sobre.',
            'fields': (
                'paleta_colores',
                'estilo_letra',
                'imagen_portada',
                ('foto_portada', 'preview_foto_portada'),
                ('logo_portada', 'preview_logo_portada'),
                ('cancion', 'preview_cancion'),
                'color_principal',
                'color_secundario',
                'color_acento',
            )
        }),
        ('5. Ceremonia, fiesta y mapas', {
            'description': 'Manten juntos lugar, fecha, link y mapa embebido de cada parte del evento.',
            'fields': (
                'fecha_misa',
                'lugar_misa',
                'direccion_ceremonia',
                ('foto_ceremonia', 'preview_foto_ceremonia'),
                'link_mapa_misa',
                'mapa_misa_embed',
                'fecha_fiesta',
                'lugar_fiesta',
                'direccion_recepcion',
                ('foto_recepcion', 'preview_foto_recepcion'),
                'hora_inicio',
                'hora_fin',
                'link_mapa_fiesta',
                'mapa_fiesta_embed',
            )
        }),
        ('6. Dress code', {
            'description': 'Usa dos imagenes: una para lo permitido y otra para lo prohibido.',
            'fields': (
                'dress_code',
                'dress_code_descripcion',
                ('dress_code_permitido_imagen', 'preview_dress_permitido'),
                ('dress_code_prohibido_imagen', 'preview_dress_prohibido'),
            )
        }),
        ('7. Links generales', {
            'description': 'El mapa general se conserva por compatibilidad; usa preferentemente mapa de ceremonia y mapa de fiesta.',
            'fields': (
                'link_mapa',
                'link_whatsapp',
                'link_mesa_regalos',
            )
        }),
        ('8. Administracion general', {
            'classes': ('collapse',),
            'fields': (
                'numero_invitados_estimado',
                'capacidad_contratada',
                'precio_por_persona',
                'tema',
                'descripcion',
                'presupuesto_total',
                'monto_pagado',
                'wedding_planner',
                'clientes',
                'fecha_creacion',
                'fecha_actualizacion',
            )
        }),
        ('9. Fondos por seccion', {
            'classes': ('collapse',),
            'description': 'Carga imagenes opcionales para personalizar el fondo de cada bloque de la invitacion.',
            'fields': (
                ('fondo_invitacion', 'preview_fondo_invitacion'),
                ('fondo_cuenta_regresiva', 'preview_fondo_cuenta_regresiva'),
                ('fondo_detalles', 'preview_fondo_detalles'),
                ('fondo_album', 'preview_fondo_album'),
                ('fondo_menu', 'preview_fondo_menu'),
                ('fondo_regalos', 'preview_fondo_regalos'),
                ('fondo_rsvp', 'preview_fondo_rsvp'),
            )
        }),
        ('10. Secciones visibles', {
            'fields': (
                'mostrar_album',
                'mostrar_mapa',
                'mostrar_regalos',
                'mostrar_menu',
                'mostrar_album_compartido',
            )
        }),
        ('11. Titulos, textos y orden', {
            'classes': ('collapse',),
            'description': 'Usa numeros pequenos para mostrar primero. Ejemplo: 10, 20, 30.',
            'fields': (
                ('titulo_invitacion', 'orden_invitacion'),
                'texto_invitacion',
                ('titulo_cuenta_regresiva', 'orden_cuenta_regresiva'),
                ('titulo_detalles', 'orden_detalles'),
                'texto_detalles',
                ('titulo_album', 'orden_album'),
                ('titulo_menu', 'orden_menu'),
                ('titulo_regalos', 'orden_regalos'),
                'titulo_album_compartido',
                'texto_album_compartido',
                'link_album_compartido',
                ('titulo_rsvp', 'orden_rsvp'),
                'texto_rsvp',
            )
        }),
    )

    def vista_previa_evento(self, obj):
        if not obj or not obj.pk:
            return 'Guarda el evento para generar una vista previa.'

        grupo = obj.grupos.order_by('fecha_creacion').first()
        if not grupo:
            url = reverse('admin:invitaciones_grupoinvitacion_add')
            return format_html(
                '<a class="admin-action-button" href="{}?evento={}">Crear grupo de prueba</a>',
                url,
                obj.pk,
            )

        url = reverse('ver_invitacion', args=[grupo.codigo])
        return format_html(
            '<a class="admin-action-button" href="{}" target="_blank" rel="noopener">Abrir invitacion</a>',
            url,
        )

    vista_previa_evento.short_description = 'Vista previa'

    def muestra_paleta(self, obj):
        if not obj:
            return 'Guarda para ver la paleta.'

        paleta = obj.obtener_paleta()
        return format_html(
            '<div class="admin-palette-preview">'
            '<span style="background:{}"></span>'
            '<span style="background:{}"></span>'
            '<span style="background:{}"></span>'
            '<span style="background:{}"></span>'
            '</div>',
            paleta['primary'],
            paleta['secondary'],
            paleta['accent'],
            paleta['bg'],
        )

    muestra_paleta.short_description = 'Paleta aplicada'

    def muestra_paleta_sobre(self, obj):
        if not obj:
            return 'Guarda para ver la paleta del sobre.'

        paleta = obj.obtener_paleta(obj.paleta_sobre)
        return format_html(
            '<div class="admin-palette-preview">'
            '<span style="background:{}"></span>'
            '<span style="background:{}"></span>'
            '<span style="background:{}"></span>'
            '</div>',
            paleta['envelope'],
            paleta['envelope_inner'],
            paleta['seal'],
        )

    muestra_paleta_sobre.short_description = 'Paleta del sobre'

    def preview_foto_portada(self, obj):
        return preview_imagen(obj, 'foto_portada', 'Sin foto de portada')

    preview_foto_portada.short_description = 'Vista'

    def preview_foto_ceremonia(self, obj):
        return preview_imagen(obj, 'foto_ceremonia', 'Sin foto de ceremonia')

    preview_foto_ceremonia.short_description = 'Ceremonia'

    def preview_foto_recepcion(self, obj):
        return preview_imagen(obj, 'foto_recepcion', 'Sin foto de fiesta')

    preview_foto_recepcion.short_description = 'Fiesta'

    def preview_logo_portada(self, obj):
        return preview_imagen(obj, 'logo_portada', 'Sin logo de portada')

    preview_logo_portada.short_description = 'Logo'

    def preview_cancion(self, obj):
        if not obj or not obj.cancion:
            return format_html('<span class="admin-empty-preview">Sin cancion</span>')
        return format_html('<audio controls src="{}"></audio>', obj.cancion.url)

    preview_cancion.short_description = 'Audio'

    def preview_sello_sobre(self, obj):
        return preview_imagen(obj, 'sello_sobre', 'Sin sello cargado')

    preview_sello_sobre.short_description = 'Sello'

    def preview_dress_permitido(self, obj):
        return preview_imagen(obj, 'dress_code_permitido_imagen', 'Sin imagen permitida')

    preview_dress_permitido.short_description = 'Vista permitido'

    def preview_dress_prohibido(self, obj):
        return preview_imagen(obj, 'dress_code_prohibido_imagen', 'Sin imagen prohibida')

    preview_dress_prohibido.short_description = 'Vista prohibido'

    def preview_fondo_invitacion(self, obj):
        return preview_imagen(obj, 'fondo_invitacion')

    def preview_fondo_cuenta_regresiva(self, obj):
        return preview_imagen(obj, 'fondo_cuenta_regresiva')

    def preview_fondo_detalles(self, obj):
        return preview_imagen(obj, 'fondo_detalles')

    def preview_fondo_album(self, obj):
        return preview_imagen(obj, 'fondo_album')

    def preview_fondo_menu(self, obj):
        return preview_imagen(obj, 'fondo_menu')

    def preview_fondo_regalos(self, obj):
        return preview_imagen(obj, 'fondo_regalos')

    def preview_fondo_rsvp(self, obj):
        return preview_imagen(obj, 'fondo_rsvp')

    class Media:
        css = {'all': ('invitaciones/css/admin.css',)}
        js = ('invitaciones/js/admin_evento.js',)


class InvitadoInline(admin.TabularInline):
    model = Invitado
    extra = 4
    fields = (
        'nombre',
        'apellidos',
        'tipo_persona',
        'menu_infantil',
        'asistira',
        'mesa',
        'restricciones_alimentarias',
        'alergias',
        'comentario',
        'orden',
    )


@admin.register(Grupoinvitacion)
class GrupoInvitacionAdmin(admin.ModelAdmin):
    form = GrupoInvitacionForm
    save_on_top = True
    list_display = (
        'nombre_grupo',
        'evento',
        'tipo',
        'total_lugares',
        'adultos_confirmados',
        'ninos_confirmados',
        'mesa',
        'estado_asistencia',
        'confirmado',
        'vista_previa_invitacion',
        'fecha_creacion',
    )
    list_filter = ('evento', 'tipo', 'confirmado', 'asistira')
    search_fields = ('nombre_grupo', 'telefono_contacto', 'mesa')
    readonly_fields = ('codigo', 'fecha_creacion', 'vista_previa_invitacion')
    inlines = [InvitadoInline]

    fieldsets = (
        ('1. Invitacion', {
            'fields': (
                'evento',
                'nombre_grupo',
                'tipo',
                'cantidad_maxima',
                'cantidad_extra_permitida',
                'telefono_contacto',
                'correo_contacto',
                'mesa',
                'codigo',
                'fecha_creacion',
            )
        }),
        ('2. Vista previa y link', {
            'fields': (
                'vista_previa_invitacion',
            )
        }),
        ('3. Confirmacion personal', {
            'description': 'Estos campos se usan principalmente cuando el tipo es PERSONAL.',
            'fields': (
                'confirmado',
                'asistira',
                'acompanantes_adultos',
                'acompanantes_ninos',
                'cantidad_confirmada',
                'requiere_menu_infantil',
                'restricciones_alimentarias',
                'alergias',
                'comentario',
                'fecha_confirmacion',
            )
        }),
        ('4. Envios', {
            'fields': (
                'estado_envio',
                'fecha_ultimo_envio',
                'fecha_ultimo_recordatorio',
            )
        }),
    )

    def get_inline_instances(self, request, obj=None):
        if obj and obj.es_personal:
            return []
        return super().get_inline_instances(request, obj)

    def estado_asistencia(self, obj):
        if obj.lugares_asistiran:
            return f'{obj.lugares_asistiran} asistiran'
        if obj.lugares_no_asistiran:
            return 'No asistiran'
        return 'Pendiente'

    estado_asistencia.short_description = 'Asistencia'

    def vista_previa_invitacion(self, obj):
        if not obj or not obj.pk:
            return 'Guarda el grupo para generar su link.'

        url = reverse('ver_invitacion', args=[obj.codigo])
        return format_html(
            '<a class="admin-action-button" href="{}" target="_blank" rel="noopener">Abrir invitacion</a>',
            url,
        )

    vista_previa_invitacion.short_description = 'Invitacion'

    class Media:
        css = {'all': ('invitaciones/css/admin.css',)}
        js = ('invitaciones/js/admin_grupo.js',)


@admin.register(FotoEvento)
class FotoEventoAdmin(admin.ModelAdmin):
    list_display = ('preview', 'titulo', 'evento', 'orden', 'visible')
    list_filter = ('evento', 'visible')
    search_fields = ('titulo', 'evento__novio', 'evento__novia')
    fields = ('evento', 'preview', 'titulo', 'imagen', 'orden', 'visible')
    readonly_fields = ('preview',)
    save_on_top = True

    def preview(self, obj):
        return preview_imagen(obj, 'imagen', 'Guarda la foto para verla aqui')

    preview.short_description = 'Vista'

    class Media:
        css = {'all': ('invitaciones/css/admin.css',)}


@admin.register(PersonaCeremonia)
class PersonaCeremoniaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'etiqueta', 'seccion', 'evento', 'orden', 'visible')
    list_filter = ('evento', 'seccion', 'visible')
    search_fields = ('nombre', 'etiqueta', 'evento__novio', 'evento__novia')
    fields = ('evento', 'seccion', 'etiqueta', 'nombre', 'orden', 'visible')
    save_on_top = True


class MediaSeccionInvitacionInline(admin.TabularInline):
    model = MediaSeccionInvitacion
    extra = 1
    fields = ('titulo', 'archivo', 'orden', 'visible')


@admin.register(PlantillaInvitacion)
class PlantillaInvitacionAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'codigo', 'tipo_evento', 'paleta_colores', 'estilo_letra', 'activa')
    list_filter = ('tipo_evento', 'paleta_colores', 'estilo_letra', 'activa')
    search_fields = ('nombre', 'codigo', 'descripcion')
    prepopulated_fields = {'codigo': ('nombre',)}
    save_on_top = True


@admin.register(SeccionInvitacion)
class SeccionInvitacionAdmin(admin.ModelAdmin):
    list_display = ('tipo', 'evento', 'titulo', 'orden', 'activa')
    list_filter = ('tipo', 'activa', 'evento')
    search_fields = ('titulo', 'descripcion', 'evento__nombre_evento', 'evento__novio', 'evento__novia')
    fields = (
        'evento',
        'plantilla',
        'tipo',
        'titulo',
        'descripcion',
        'orden',
        'activa',
        'mostrar_titulo_texto',
        'imagen_titulo',
        'fondo',
        'posicion_fondo',
        'opacidad_fondo',
        'color_texto',
    )
    inlines = (MediaSeccionInvitacionInline,)
    save_on_top = True


@admin.register(EnlaceRegalo)
class EnlaceRegaloAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'tipo', 'evento', 'visible', 'abrir_link')
    list_filter = ('evento', 'tipo', 'visible')
    search_fields = ('nombre', 'banco', 'titular', 'evento__novio', 'evento__novia')
    fields = (
        'evento',
        'tipo',
        'nombre',
        'url',
        'banco',
        'titular',
        'numero_cuenta',
        'clabe',
        'instrucciones',
        'visible',
    )
    save_on_top = True

    def abrir_link(self, obj):
        if obj.es_deposito or not obj.url:
            return 'Deposito'
        return format_html(
            '<a class="admin-action-button small" href="{}" target="_blank" rel="noopener">Abrir</a>',
            obj.url,
        )

    abrir_link.short_description = 'Link'


@admin.register(ItinerarioEvento)
class ItinerarioEventoAdmin(admin.ModelAdmin):
    list_display = ('hora', 'titulo', 'icono', 'evento', 'orden', 'visible')
    list_filter = ('evento', 'icono', 'visible')
    search_fields = ('titulo', 'descripcion', 'evento__novio', 'evento__novia')
    fields = ('evento', 'hora', 'titulo', 'descripcion', 'icono', 'orden', 'visible')
    save_on_top = True


@admin.register(MenuBoda)
class MenuBodaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'tipo', 'evento', 'visible')
    list_filter = ('evento', 'tipo', 'visible')
    search_fields = ('nombre', 'descripcion', 'evento__novio', 'evento__novia')
    fields = ('evento', 'nombre', 'tipo', 'descripcion', 'visible')
    save_on_top = True


@admin.register(Invitado)
class InvitadoAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'grupo', 'tipo_persona', 'menu_infantil', 'asistira', 'mesa', 'fecha_confirmacion')
    list_filter = ('grupo__evento', 'tipo_persona', 'menu_infantil', 'asistira')
    search_fields = ('nombre', 'apellidos', 'telefono', 'correo', 'grupo__nombre_grupo', 'mesa')
    readonly_fields = ('fecha_confirmacion',)
    fields = (
        'grupo',
        'nombre',
        'apellidos',
        'telefono',
        'correo',
        'tipo_persona',
        'menu_infantil',
        'asistira',
        'fecha_confirmacion',
        'mesa',
        'restricciones_alimentarias',
        'alergias',
        'comentario',
        'notas',
        'orden',
    )
