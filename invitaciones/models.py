from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.html import format_html
from django.utils import timezone
from urllib.parse import urlparse
import uuid
import re


MAX_IMAGE_SIZE_MB = 8
MAX_VIDEO_SIZE_MB = 80
MAX_AUDIO_SIZE_MB = 20
MAX_DOCUMENT_SIZE_MB = 25
IMAGE_EXTENSIONS = {'jpg', 'jpeg', 'png', 'webp', 'gif'}
VIDEO_EXTENSIONS = {'mp4', 'webm', 'ogg', 'mov', 'm4v'}
AUDIO_EXTENSIONS = {'mp3', 'wav', 'ogg', 'm4a'}
DOCUMENT_EXTENSIONS = {'pdf', 'doc', 'docx', 'xls', 'xlsx', 'txt', 'jpg', 'jpeg', 'png', 'webp'}
GOOGLE_MAPS_HOSTS = {
    'google.com',
    'www.google.com',
    'maps.google.com',
    'maps.app.goo.gl',
    'goo.gl',
}


def extension_archivo(archivo):
    if not archivo:
        return ''
    nombre = getattr(archivo, 'name', '') or ''
    return nombre.rsplit('.', 1)[-1].lower() if '.' in nombre else ''


def es_video_archivo(archivo):
    return extension_archivo(archivo) in {'mp4', 'webm', 'ogg', 'mov', 'm4v'}


def validar_archivo_por_extension_y_tamano(archivo, extensiones, max_mb, etiqueta):
    extension = extension_archivo(archivo)
    if extension not in extensiones:
        permitidas = ', '.join(sorted(extensiones))
        raise ValidationError(f'{etiqueta}: formato no permitido. Usa: {permitidas}.')
    if getattr(archivo, 'size', 0) > max_mb * 1024 * 1024:
        raise ValidationError(f'{etiqueta}: el archivo no debe exceder {max_mb} MB.')


def validar_imagen(archivo):
    validar_archivo_por_extension_y_tamano(archivo, IMAGE_EXTENSIONS, MAX_IMAGE_SIZE_MB, 'Imagen')


def validar_media_visual(archivo):
    extensiones = IMAGE_EXTENSIONS | VIDEO_EXTENSIONS | AUDIO_EXTENSIONS
    extension = extension_archivo(archivo)
    if extension in VIDEO_EXTENSIONS:
        max_mb = MAX_VIDEO_SIZE_MB
    elif extension in AUDIO_EXTENSIONS:
        max_mb = MAX_AUDIO_SIZE_MB
    else:
        max_mb = MAX_IMAGE_SIZE_MB
    validar_archivo_por_extension_y_tamano(archivo, extensiones, max_mb, 'Media')


def validar_audio(archivo):
    validar_archivo_por_extension_y_tamano(archivo, AUDIO_EXTENSIONS, MAX_AUDIO_SIZE_MB, 'Audio')


def validar_documento(archivo):
    validar_archivo_por_extension_y_tamano(archivo, DOCUMENT_EXTENSIONS, MAX_DOCUMENT_SIZE_MB, 'Documento')


def google_maps_src(valor):
    valor = (valor or '').strip()
    if not valor:
        return ''

    match = re.search(r'<iframe[^>]+src=["\']([^"\']+)["\']', valor, flags=re.IGNORECASE)
    src = match.group(1).strip() if match else valor
    parsed = urlparse(src)
    host = parsed.netloc.lower()

    if parsed.scheme != 'https':
        return ''
    if not any(host == allowed or host.endswith(f'.{allowed}') for allowed in GOOGLE_MAPS_HOSTS):
        return ''
    if 'map' not in parsed.path.lower() and 'map' not in host:
        return ''
    return src


def iframe_google_maps(valor):
    src = google_maps_src(valor)
    if not src:
        return ''
    return format_html(
        '<iframe src="{}" loading="lazy" allowfullscreen referrerpolicy="no-referrer-when-downgrade"></iframe>',
        src,
    )


class EventoBoda(models.Model):
    TIPOS_EVENTO = [
        ('BODA', 'Boda'),
        ('XV', 'XV anos'),
        ('BABY_SHOWER', 'Baby shower'),
        ('BAUTIZO', 'Bautizo'),
        ('CUMPLEANOS', 'Cumpleanos'),
        ('ANIVERSARIO', 'Aniversario'),
        ('CORPORATIVO', 'Corporativo'),
        ('OTRO', 'Otro'),
    ]
    ESTADOS_EVENTO = [
        ('PLANEACION', 'Planeacion'),
        ('PREPARACION', 'En preparacion'),
        ('CONFIRMADO', 'Confirmado'),
        ('EN_CURSO', 'En curso'),
        ('FINALIZADO', 'Finalizado'),
        ('CANCELADO', 'Cancelado'),
    ]
    PALETAS = [
        ('BOSQUE', 'Verde bosque y dorado'),
        ('ROSA', 'Rosa romántico'),
        ('TERRACOTA', 'Terracota elegante'),
        ('AZUL', 'Azul noche'),
        ('LAVANDA', 'Lavanda suave'),
        ('DORADO', 'Champagne dorado'),
        ('TINTA_MARFIL', 'Tinta azul y marfil'),
        ('NEGRO_DORADO', 'Negro y dorado'),
        ('VINO_ROSA', 'Vino y rosa empolvado'),
        ('SALVIA_PERLA', 'Salvia y perla'),
        ('PERSONALIZADA', 'Personalizada con códigos'),
    ]
    ESTILOS_LETRA = [
        ('CLASICA', 'Clásica elegante'),
        ('EDITORIAL', 'Editorial sofisticada'),
        ('MODERNA', 'Moderna limpia'),
        ('ROMANTICA', 'Romántica manuscrita'),
        ('MANUSCRITA', 'Manuscrita fina'),
        ('CURSIVA_ELEGANTE', 'Cursiva elegante'),
    ]

    nombre_evento = models.CharField(max_length=180, blank=True, null=True)
    empresa = models.ForeignKey(
        'organizaciones.EmpresaSuscriptora',
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        related_name='eventos',
    )
    sede = models.ForeignKey(
        'organizaciones.SedeEvento',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='eventos',
    )
    tipo_evento = models.CharField(max_length=20, choices=TIPOS_EVENTO, default='BODA')
    estado = models.CharField(max_length=20, choices=ESTADOS_EVENTO, default='PLANEACION')
    novio = models.CharField(max_length=100)
    novia = models.CharField(max_length=100)
    nombre_principal = models.CharField(max_length=120, blank=True, null=True)
    nombre_secundario = models.CharField(max_length=120, blank=True, null=True)
    etiqueta_principal = models.CharField(max_length=80, default='Novia')
    etiqueta_secundario = models.CharField(max_length=80, default='Novio')
    mostrar_nombre_secundario = models.BooleanField(default=True)
    activo = models.BooleanField(default=True)

    frase_portada = models.CharField(max_length=255)
    mensaje_general = models.TextField()

    fecha_misa = models.DateTimeField()
    lugar_misa = models.CharField(max_length=200)
    direccion_ceremonia = models.CharField(max_length=255, blank=True, null=True)
    foto_ceremonia = models.FileField(upload_to='lugares/', validators=[validar_media_visual], blank=True, null=True)

    fecha_fiesta = models.DateTimeField()
    lugar_fiesta = models.CharField(max_length=200)
    direccion_recepcion = models.CharField(max_length=255, blank=True, null=True)
    foto_recepcion = models.FileField(upload_to='lugares/', validators=[validar_media_visual], blank=True, null=True)
    hora_inicio = models.TimeField(blank=True, null=True)
    hora_fin = models.TimeField(blank=True, null=True)
    numero_invitados_estimado = models.PositiveIntegerField(default=0)
    capacidad_contratada = models.PositiveIntegerField(default=0)
    precio_por_persona = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    dress_code = models.CharField(max_length=150, blank=True, null=True)
    dress_code_descripcion = models.TextField(blank=True, null=True)
    dress_code_permitido_imagen = models.FileField(upload_to='dress_code/', validators=[validar_imagen], blank=True, null=True)
    dress_code_prohibido_imagen = models.FileField(upload_to='dress_code/', validators=[validar_imagen], blank=True, null=True)

    link_mapa = models.URLField(blank=True, null=True)
    link_mapa_misa = models.URLField(blank=True, null=True)
    link_mapa_fiesta = models.URLField(blank=True, null=True)
    mapa_misa_embed = models.TextField(blank=True, null=True)
    mapa_fiesta_embed = models.TextField(blank=True, null=True)
    link_whatsapp = models.URLField(blank=True, null=True)
    link_mesa_regalos = models.URLField(blank=True, null=True)

    imagen_portada = models.URLField(blank=True, null=True)
    foto_portada = models.FileField(upload_to='portadas/', validators=[validar_media_visual], blank=True, null=True)
    logo_portada = models.FileField(upload_to='logos/', validators=[validar_imagen], blank=True, null=True)
    cancion = models.FileField(upload_to='canciones/', validators=[validar_audio], blank=True, null=True)
    paleta_sobre = models.CharField(max_length=20, choices=PALETAS, default='TINTA_MARFIL')
    sello_sobre = models.FileField(upload_to='sellos/', validators=[validar_imagen], blank=True, null=True)
    monograma_sobre = models.CharField(max_length=12, blank=True, null=True)
    texto_boton_sobre = models.CharField(max_length=80, default='Abrir invitación')
    fondo_invitacion = models.FileField(upload_to='fondos_secciones/', validators=[validar_media_visual], blank=True, null=True)
    fondo_cuenta_regresiva = models.FileField(upload_to='fondos_secciones/', validators=[validar_media_visual], blank=True, null=True)
    fondo_detalles = models.FileField(upload_to='fondos_secciones/', validators=[validar_media_visual], blank=True, null=True)
    fondo_album = models.FileField(upload_to='fondos_secciones/', validators=[validar_media_visual], blank=True, null=True)
    fondo_menu = models.FileField(upload_to='fondos_secciones/', validators=[validar_media_visual], blank=True, null=True)
    fondo_regalos = models.FileField(upload_to='fondos_secciones/', validators=[validar_media_visual], blank=True, null=True)
    fondo_rsvp = models.FileField(upload_to='fondos_secciones/', validators=[validar_media_visual], blank=True, null=True)

    paleta_colores = models.CharField(max_length=20, choices=PALETAS, default='BOSQUE')
    estilo_letra = models.CharField(max_length=20, choices=ESTILOS_LETRA, default='CLASICA')
    color_principal = models.CharField(max_length=20, default='#2f7a4d')
    color_secundario = models.CharField(max_length=20, default='#63b96d')
    color_acento = models.CharField(max_length=20, default='#d2b074')
    tema = models.CharField(max_length=150, blank=True, null=True)
    descripcion = models.TextField(blank=True, null=True)
    presupuesto_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    monto_pagado = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    wedding_planner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='eventos_planeados',
    )
    clientes = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        related_name='eventos_cliente',
    )
    fecha_creacion = models.DateTimeField(default=timezone.now)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    mostrar_album = models.BooleanField(default=True)
    mostrar_mapa = models.BooleanField(default=True)
    mostrar_regalos = models.BooleanField(default=True)
    mostrar_menu = models.BooleanField(default=True)
    mostrar_album_compartido = models.BooleanField(default=False)

    titulo_invitacion = models.CharField(max_length=120, default='Tu invitación')
    texto_invitacion = models.TextField(
        default='Hemos reservado este espacio para celebrar juntos este día tan especial.'
    )
    titulo_cuenta_regresiva = models.CharField(max_length=120, default='Faltan')
    titulo_detalles = models.CharField(max_length=120, default='Detalles del evento')
    texto_detalles = models.TextField(
        default='Aquí tienes ceremonia, fiesta, ubicación y dress code en un solo lugar.'
    )
    titulo_album = models.CharField(max_length=120, default='Álbum')
    titulo_menu = models.CharField(max_length=120, default='Menú')
    titulo_regalos = models.CharField(max_length=120, default='Regalos')
    titulo_album_compartido = models.CharField(max_length=120, default='Comparte tus fotos')
    texto_album_compartido = models.TextField(
        default='Ayúdanos a guardar tus mejores momentos. Sube tus fotos y videos al álbum compartido.'
    )
    link_album_compartido = models.URLField(blank=True, null=True)
    titulo_rsvp = models.CharField(max_length=120, default='Confirma tu asistencia')
    texto_rsvp = models.TextField(default='Tu respuesta nos ayuda a organizar lugares, mesas y buffet.')

    orden_invitacion = models.PositiveIntegerField(default=10)
    orden_cuenta_regresiva = models.PositiveIntegerField(default=20)
    orden_detalles = models.PositiveIntegerField(default=30)
    orden_album = models.PositiveIntegerField(default=50)
    orden_menu = models.PositiveIntegerField(default=60)
    orden_regalos = models.PositiveIntegerField(default=70)
    orden_rsvp = models.PositiveIntegerField(default=80)

    def __str__(self):
        return self.titulo_evento

    @property
    def titulo_evento(self):
        if self.nombre_evento:
            return self.nombre_evento
        if self.tipo_evento == 'BODA':
            return f'Boda {self.participante_secundario} & {self.participante_principal}'
        return f'{self.get_tipo_evento_display()} {self.participante_principal}'

    @property
    def participante_principal(self):
        return self.nombre_principal or self.novia

    @property
    def participante_secundario(self):
        return self.nombre_secundario or self.novio

    @property
    def titulo_portada(self):
        if self.mostrar_nombre_secundario and self.participante_secundario:
            return f'{self.participante_principal} & {self.participante_secundario}'
        return self.participante_principal

    @property
    def mapa_misa_embed_html(self):
        return iframe_google_maps(self.mapa_misa_embed)

    @property
    def mapa_fiesta_embed_html(self):
        return iframe_google_maps(self.mapa_fiesta_embed)

    @property
    def monto_pendiente(self):
        pendiente = self.presupuesto_total - self.monto_pagado
        return pendiente if pendiente > 0 else 0

    @property
    def numero_invitados_confirmados(self):
        return Invitado.objects.filter(
            grupo__evento=self,
            asistira=True,
        ).count()

    def obtener_paleta(self, codigo=None):
        codigo = codigo or self.paleta_colores
        paletas = {
            'BOSQUE': {
                'primary': '#2f7a4d',
                'secondary': '#79b87a',
                'accent': '#d2b074',
                'bg': '#f7faf3',
                'text': '#253126',
                'muted': '#647263',
                'line': '#d9e5d4',
                'envelope': '#203428',
                'envelope_inner': '#f4e3bd',
                'seal': '#1d2d25',
            },
            'ROSA': {
                'primary': '#9b4f63',
                'secondary': '#d99aaa',
                'accent': '#c59a55',
                'bg': '#fff7f8',
                'text': '#38282d',
                'muted': '#7a6269',
                'line': '#edd5db',
                'envelope': '#6d3c49',
                'envelope_inner': '#f6d8df',
                'seal': '#9b4f63',
            },
            'TERRACOTA': {
                'primary': '#9a583d',
                'secondary': '#d68b6a',
                'accent': '#61735b',
                'bg': '#fff8f3',
                'text': '#342820',
                'muted': '#76675e',
                'line': '#ead8ca',
                'envelope': '#7b432f',
                'envelope_inner': '#f1c7ad',
                'seal': '#8e5139',
            },
            'AZUL': {
                'primary': '#24476f',
                'secondary': '#7ca0c4',
                'accent': '#d4b06a',
                'bg': '#f3f7fb',
                'text': '#202d3c',
                'muted': '#5e6d7a',
                'line': '#d4dfeb',
                'envelope': '#122742',
                'envelope_inner': '#e9dcc1',
                'seal': '#203b60',
            },
            'LAVANDA': {
                'primary': '#746099',
                'secondary': '#b8a7d8',
                'accent': '#c4a05b',
                'bg': '#faf7ff',
                'text': '#302b3b',
                'muted': '#6d637a',
                'line': '#ded4ee',
                'envelope': '#4f4169',
                'envelope_inner': '#eadff7',
                'seal': '#746099',
            },
            'DORADO': {
                'primary': '#8a6a2f',
                'secondary': '#d5bd7a',
                'accent': '#5f6f52',
                'bg': '#fffaf0',
                'text': '#332d20',
                'muted': '#726953',
                'line': '#e9dcc1',
                'envelope': '#3d3321',
                'envelope_inner': '#f1dfad',
                'seal': '#8a6a2f',
            },
            'TINTA_MARFIL': {
                'primary': '#1e2b44',
                'secondary': '#52627d',
                'accent': '#c8a56a',
                'bg': '#f7f0e8',
                'text': '#242331',
                'muted': '#6c6470',
                'line': '#ded2c4',
                'envelope': '#121b2f',
                'envelope_inner': '#f2d9aa',
                'seal': '#223350',
            },
            'NEGRO_DORADO': {
                'primary': '#22201d',
                'secondary': '#5c5750',
                'accent': '#c7a05a',
                'bg': '#f7f2ea',
                'text': '#201f1d',
                'muted': '#6a6259',
                'line': '#ddd0bd',
                'envelope': '#111111',
                'envelope_inner': '#ddc28a',
                'seal': '#202020',
            },
            'VINO_ROSA': {
                'primary': '#643244',
                'secondary': '#b77b89',
                'accent': '#d3ad70',
                'bg': '#fff4f0',
                'text': '#32252a',
                'muted': '#765f66',
                'line': '#ead1d0',
                'envelope': '#4b2432',
                'envelope_inner': '#f4c7cb',
                'seal': '#6f3145',
            },
            'SALVIA_PERLA': {
                'primary': '#50685c',
                'secondary': '#93a79b',
                'accent': '#bd9b62',
                'bg': '#f4f3ec',
                'text': '#26302b',
                'muted': '#68736d',
                'line': '#d7d8ce',
                'envelope': '#43564c',
                'envelope_inner': '#e5e0cf',
                'seal': '#50685c',
            },
        }
        if codigo == 'PERSONALIZADA':
            return {
                'primary': self.color_principal,
                'secondary': self.color_secundario,
                'accent': self.color_acento,
                'bg': '#f8faf5',
                'text': '#253126',
                'muted': '#657164',
                'line': '#dce5d9',
                'envelope': self.color_principal,
                'envelope_inner': self.color_acento,
                'seal': self.color_principal,
            }
        return paletas.get(codigo, paletas['BOSQUE'])

    @property
    def color_principal_final(self):
        return self.obtener_paleta()['primary']

    @property
    def color_secundario_final(self):
        return self.obtener_paleta()['secondary']

    @property
    def color_acento_final(self):
        return self.obtener_paleta()['accent']

    @property
    def color_fondo_final(self):
        return self.obtener_paleta()['bg']

    @property
    def color_texto_final(self):
        return self.obtener_paleta()['text']

    @property
    def color_muted_final(self):
        return self.obtener_paleta()['muted']

    @property
    def color_linea_final(self):
        return self.obtener_paleta()['line']

    @property
    def color_sobre_final(self):
        return self.obtener_paleta(self.paleta_sobre)['envelope']

    @property
    def color_forro_sobre_final(self):
        return self.obtener_paleta(self.paleta_sobre)['envelope_inner']

    @property
    def color_sello_final(self):
        return self.obtener_paleta(self.paleta_sobre)['seal']

    @property
    def monograma_final(self):
        if self.monograma_sobre:
            return self.monograma_sobre
        novio = (self.novio or 'N')[:1]
        novia = (self.novia or 'N')[:1]
        return f'{novio}&{novia}'.upper()

    @property
    def portada_es_video(self):
        return es_video_archivo(self.foto_portada)

    @property
    def ceremonia_es_video(self):
        return es_video_archivo(self.foto_ceremonia)

    @property
    def recepcion_es_video(self):
        return es_video_archivo(self.foto_recepcion)

    @property
    def fondo_invitacion_es_video(self):
        return es_video_archivo(self.fondo_invitacion)

    @property
    def fondo_cuenta_regresiva_es_video(self):
        return es_video_archivo(self.fondo_cuenta_regresiva)

    @property
    def fondo_detalles_es_video(self):
        return es_video_archivo(self.fondo_detalles)

    @property
    def fondo_album_es_video(self):
        return es_video_archivo(self.fondo_album)

    @property
    def fondo_menu_es_video(self):
        return es_video_archivo(self.fondo_menu)

    @property
    def fondo_regalos_es_video(self):
        return es_video_archivo(self.fondo_regalos)

    @property
    def fondo_rsvp_es_video(self):
        return es_video_archivo(self.fondo_rsvp)

    @property
    def fuente_titulos(self):
        fuentes = {
            'CLASICA': "'Cormorant Garamond', serif",
            'EDITORIAL': "'Playfair Display', serif",
            'MODERNA': "'Poppins', sans-serif",
            'ROMANTICA': "'Great Vibes', cursive",
            'MANUSCRITA': "'Allura', cursive",
            'CURSIVA_ELEGANTE': "'Parisienne', cursive",
        }
        return fuentes.get(self.estilo_letra, fuentes['CLASICA'])

    @property
    def fuente_texto(self):
        fuentes = {
            'CLASICA': "'Montserrat', sans-serif",
            'EDITORIAL': "'Lato', sans-serif",
            'MODERNA': "'Inter', sans-serif",
            'ROMANTICA': "'Quicksand', sans-serif",
            'MANUSCRITA': "'Montserrat', sans-serif",
            'CURSIVA_ELEGANTE': "'Cormorant Garamond', serif",
        }
        return fuentes.get(self.estilo_letra, fuentes['CLASICA'])


class PlantillaInvitacion(models.Model):
    codigo = models.SlugField(max_length=80, unique=True)
    nombre = models.CharField(max_length=120)
    tipo_evento = models.CharField(max_length=20, choices=EventoBoda.TIPOS_EVENTO, default='BODA')
    descripcion = models.TextField(blank=True, null=True)
    paleta_colores = models.CharField(max_length=20, choices=EventoBoda.PALETAS, default='BOSQUE')
    paleta_sobre = models.CharField(max_length=20, choices=EventoBoda.PALETAS, default='TINTA_MARFIL')
    estilo_letra = models.CharField(max_length=20, choices=EventoBoda.ESTILOS_LETRA, default='CLASICA')
    activa = models.BooleanField(default=True)
    configuracion = models.JSONField(default=dict, blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['tipo_evento', 'nombre']
        verbose_name = 'Plantilla de invitacion'
        verbose_name_plural = 'Plantillas de invitacion'

    def __str__(self):
        return self.nombre


class SeccionInvitacion(models.Model):
    TIPOS = [
        ('PORTADA', 'Portada'),
        ('PADRES_PADRINOS', 'Padres y padrinos'),
        ('CUENTA_REGRESIVA', 'Cuenta regresiva'),
        ('DETALLES', 'Detalles y mapas'),
        ('DRESS_CODE', 'Dress code'),
        ('ITINERARIO', 'Itinerario'),
        ('ALBUM', 'Album'),
        ('MENU', 'Menu'),
        ('REGALOS', 'Regalos'),
        ('ALBUM_COMPARTIDO', 'Album compartido'),
        ('RSVP', 'Confirmacion'),
        ('PERSONALIZADA', 'Personalizada'),
    ]
    POSICIONES_FONDO = [
        ('center center', 'Centro'),
        ('top center', 'Arriba'),
        ('bottom center', 'Abajo'),
        ('center left', 'Izquierda'),
        ('center right', 'Derecha'),
    ]

    evento = models.ForeignKey(EventoBoda, on_delete=models.CASCADE, related_name='secciones_invitacion')
    plantilla = models.ForeignKey(
        PlantillaInvitacion,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='secciones_evento',
    )
    tipo = models.CharField(max_length=30, choices=TIPOS)
    titulo = models.CharField(max_length=140, blank=True, null=True)
    descripcion = models.TextField(blank=True, null=True)
    orden = models.PositiveIntegerField(default=0)
    activa = models.BooleanField(default=True)
    mostrar_titulo_texto = models.BooleanField(default=True)
    imagen_titulo = models.FileField(upload_to='secciones/titulos/', validators=[validar_media_visual], blank=True, null=True)
    fondo = models.FileField(upload_to='secciones/fondos/', validators=[validar_media_visual], blank=True, null=True)
    posicion_fondo = models.CharField(max_length=30, choices=POSICIONES_FONDO, default='center center')
    opacidad_fondo = models.DecimalField(max_digits=3, decimal_places=2, default=0.18)
    color_texto = models.CharField(max_length=20, blank=True, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['evento', 'orden', 'id']
        unique_together = ('evento', 'tipo')
        verbose_name = 'Seccion de invitacion'
        verbose_name_plural = 'Secciones de invitacion'

    def __str__(self):
        return f'{self.get_tipo_display()} - {self.evento}'

    @property
    def fondo_es_video(self):
        return es_video_archivo(self.fondo)

    @property
    def imagen_titulo_es_video(self):
        return es_video_archivo(self.imagen_titulo)


class MediaSeccionInvitacion(models.Model):
    seccion = models.ForeignKey(SeccionInvitacion, on_delete=models.CASCADE, related_name='medios')
    titulo = models.CharField(max_length=120, blank=True, null=True)
    descripcion = models.TextField(blank=True, null=True)
    archivo = models.FileField(upload_to='secciones/media/', validators=[validar_media_visual])
    orden = models.PositiveIntegerField(default=0)
    visible = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['seccion', 'orden', 'id']
        verbose_name = 'Media de seccion'
        verbose_name_plural = 'Media de secciones'

    def __str__(self):
        return self.titulo or f'Media {self.id}'

    @property
    def es_video(self):
        return es_video_archivo(self.archivo)


class ComponenteInvitacion(models.Model):
    TIPOS = [
        ('TEXTO', 'Texto'),
        ('IMAGEN', 'Imagen'),
        ('BOTON', 'Boton'),
    ]
    LAYOUT_MODES = [
        ('FLOW', 'Flujo'),
        ('ABSOLUTE', 'Absoluto'),
        ('LAYER', 'Capa permanente'),
    ]

    COORDINATE_SPACES = [
        ('PAGE', 'Pagina'),
        ('SECTION', 'Seccion'),
        ('CONTAINER', 'Contenedor'),
        ('COMPONENT', 'Componente'),
    ]

    evento = models.ForeignKey(
        EventoBoda,
        on_delete=models.CASCADE,
        related_name='componentes_invitacion',
    )
    seccion = models.ForeignKey(
        SeccionInvitacion,
        on_delete=models.CASCADE,
        related_name='componentes',
    )
    tipo = models.CharField(max_length=20, choices=TIPOS)
    x = models.FloatField(default=50)
    y = models.FloatField(default=50)
    width = models.FloatField(default=44)
    height = models.FloatField(default=12)
    rotation = models.FloatField(default=0)
    opacity = models.FloatField(default=1)
    z_index = models.PositiveIntegerField(default=20)
    locked = models.BooleanField(default=False)
    hidden = models.BooleanField(default=False)

    layout_mode = models.CharField(
        max_length=20,
        choices=LAYOUT_MODES,
        default='ABSOLUTE',
    )

    coordinate_space = models.CharField(
        max_length=20,
        choices=COORDINATE_SPACES,
        default='SECTION',
    )

    parent_key = models.CharField(
        max_length=120,
        blank=True,
        default='',
    )

    constraints = models.JSONField(
        default=dict,
        blank=True,
    )

    properties = models.JSONField(
        default=dict,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['evento', 'seccion', 'z_index', 'id']
        indexes = [
            models.Index(fields=['evento', 'seccion', 'tipo']),
            models.Index(fields=['evento', 'hidden']),
        ]
        verbose_name = 'Componente de invitacion'
        verbose_name_plural = 'Componentes de invitacion'

    def __str__(self):
        return f'{self.get_tipo_display()} - {self.seccion.get_tipo_display()}'

    def clean(self):
        super().clean()
        if self.seccion_id and self.evento_id and self.seccion.evento_id != self.evento_id:
            raise ValidationError('La seccion no pertenece al evento seleccionado.')
        if not isinstance(self.properties, dict):
            raise ValidationError('Las propiedades del componente deben ser un objeto JSON.')
        if not isinstance(self.constraints, dict):
            raise ValidationError(
                'Las restricciones del componente deben ser un objeto JSON.'
            )

    def save(self, *args, **kwargs):
        if self.seccion_id:
            self.evento_id = self.seccion.evento_id
        super().save(*args, **kwargs)


class DisenoInvitacion(models.Model):
    ESTADOS = [
        ('BORRADOR', 'Borrador'),
        ('PUBLICADO', 'Publicado'),
    ]
    ALCANCES = [
        ('EVENTO', 'Evento'),
        ('PLANTILLA', 'Plantilla'),
    ]
    CONFIG_DEFAULT = {
        'theme': {
            'palette': 'TINTA_MARFIL',
            'envelopePalette': 'TINTA_MARFIL',
            'fontStyle': 'CURSIVA_ELEGANTE',
            'primary': '',
            'secondary': '',
            'accent': '',
            'background': '',
        },
        'layout': {
            'maxWidth': 430,
            'sectionSpacing': 'soft',
            'animation': 'fade',
        },
        'sections': [],
    }

    evento = models.OneToOneField(EventoBoda, on_delete=models.CASCADE, related_name='diseno_visual')
    plantilla_base = models.ForeignKey(
        PlantillaInvitacion,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='disenos_evento',
    )
    nombre = models.CharField(max_length=120, default='Diseño principal')
    estado = models.CharField(max_length=20, choices=ESTADOS, default='BORRADOR')
    configuracion_borrador = models.JSONField(default=dict, blank=True)
    configuracion_publicada = models.JSONField(default=dict, blank=True)
    documento_builder_borrador = models.JSONField(default=dict, blank=True)
    documento_builder_publicado = models.JSONField(default=dict, blank=True)
    builder_revision = models.PositiveIntegerField(default=0)
    publicado_en = models.DateTimeField(blank=True, null=True)
    actualizado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='disenos_invitacion_actualizados',
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Diseño visual de invitacion'
        verbose_name_plural = 'Diseños visuales de invitacion'

    def __str__(self):
        return f'{self.nombre} - {self.evento}'

    @classmethod
    def configuracion_inicial(cls, evento):
        config = {
            'theme': {
                'palette': evento.paleta_colores or cls.CONFIG_DEFAULT['theme']['palette'],
                'envelopePalette': evento.paleta_sobre or cls.CONFIG_DEFAULT['theme']['envelopePalette'],
                'fontStyle': evento.estilo_letra or cls.CONFIG_DEFAULT['theme']['fontStyle'],
                'primary': evento.color_principal or '',
                'secondary': evento.color_secundario or '',
                'accent': evento.color_acento or '',
                'background': getattr(evento, 'color_fondo_final', '') or '',
            },
            'layout': dict(cls.CONFIG_DEFAULT['layout']),
            'sections': [],
        }
        return config

    @property
    def configuracion_activa(self):
        return self.configuracion_publicada or self.configuracion_borrador or self.CONFIG_DEFAULT

    @property
    def tiene_publicacion(self):
        return bool(self.configuracion_publicada)

    def publicar(self, usuario=None):
        self.configuracion_publicada = self.configuracion_borrador or self.configuracion_activa
        self.estado = 'PUBLICADO'
        self.publicado_en = timezone.now()
        self.actualizado_por = usuario


class VersionDisenoInvitacion(models.Model):
    diseno = models.ForeignKey(DisenoInvitacion, on_delete=models.CASCADE, related_name='versiones')
    nombre = models.CharField(max_length=120)
    configuracion = models.JSONField(default=dict)
    publicado = models.BooleanField(default=False)
    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='versiones_diseno_invitacion',
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-fecha_creacion', '-id']
        verbose_name = 'Version de diseño de invitacion'
        verbose_name_plural = 'Versiones de diseño de invitacion'

    def __str__(self):
        return self.nombre


class AssetInvitacion(models.Model):
    TIPOS = [
        ('FONDO', 'Fondo'),
        ('PORTADA', 'Portada'),
        ('TITULO', 'Titulo visual'),
        ('DECORACION', 'Decoracion'),
        ('ALBUM', 'Album'),
        ('VIDEO', 'Video'),
        ('GIF', 'GIF'),
        ('AUDIO', 'Audio'),
    ]
    evento = models.ForeignKey(EventoBoda, on_delete=models.CASCADE, related_name='assets_invitacion')
    seccion = models.ForeignKey(
        SeccionInvitacion,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='assets_editor',
    )
    tipo = models.CharField(max_length=20, choices=TIPOS, default='DECORACION')
    titulo = models.CharField(max_length=120, blank=True, null=True)
    archivo = models.FileField(upload_to='editor_invitaciones/assets/', validators=[validar_media_visual])
    orden = models.PositiveIntegerField(default=0)
    visible = models.BooleanField(default=True)
    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='assets_invitacion_subidos',
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['evento', 'orden', '-fecha_creacion']
        verbose_name = 'Asset de invitacion'
        verbose_name_plural = 'Assets de invitacion'

    def __str__(self):
        return self.titulo or f'{self.get_tipo_display()} {self.id}'

    @property
    def es_video(self):
        return es_video_archivo(self.archivo)


class PersonaCeremonia(models.Model):
    SECCIONES = [
        ('PADRES_NOVIO', 'Padres del novio'),
        ('PADRES_NOVIA', 'Padres de la novia'),
        ('PADRINOS', 'Padrinos'),
    ]
    evento = models.ForeignKey(EventoBoda, on_delete=models.CASCADE, related_name='personas_ceremonia')
    seccion = models.CharField(max_length=20, choices=SECCIONES)
    etiqueta = models.CharField(max_length=80, default='Papá')
    nombre = models.CharField(max_length=120)
    orden = models.PositiveIntegerField(default=0)
    visible = models.BooleanField(default=True)

    class Meta:
        ordering = ['seccion', 'orden', 'id']

    def __str__(self):
        return f'{self.etiqueta}: {self.nombre}'


class FotoEvento(models.Model):
    evento = models.ForeignKey(EventoBoda, on_delete=models.CASCADE, related_name='fotos')
    titulo = models.CharField(max_length=100, blank=True, null=True)
    imagen = models.FileField(upload_to='album/', validators=[validar_media_visual])
    orden = models.PositiveIntegerField(default=0)
    visible = models.BooleanField(default=True)

    class Meta:
        ordering = ['orden', 'id']

    def __str__(self):
        return self.titulo or f'Foto {self.id}'

    @property
    def es_video(self):
        return es_video_archivo(self.imagen)

    @property
    def es_gif(self):
        return extension_archivo(self.imagen) == 'gif'


class EnlaceRegalo(models.Model):
    TIPOS = [
        ('TIENDA', 'Link de tienda'),
        ('DEPOSITO', 'Deposito bancario'),
    ]
    evento = models.ForeignKey(EventoBoda, on_delete=models.CASCADE, related_name='regalos')
    nombre = models.CharField(max_length=100)
    tipo = models.CharField(max_length=20, choices=TIPOS, default='TIENDA')
    url = models.URLField(blank=True, null=True)
    banco = models.CharField(max_length=100, blank=True, null=True)
    titular = models.CharField(max_length=120, blank=True, null=True)
    numero_cuenta = models.CharField(max_length=60, blank=True, null=True)
    clabe = models.CharField(max_length=40, blank=True, null=True)
    instrucciones = models.TextField(blank=True, null=True)
    visible = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre

    @property
    def es_deposito(self):
        return self.tipo == 'DEPOSITO'


class ItinerarioEvento(models.Model):
    ICONOS = [
        ('ceremonia', 'Ceremonia'),
        ('civil', 'Civil'),
        ('recepcion', 'Recepcion'),
        ('brindis', 'Brindis'),
        ('cena', 'Cena'),
        ('baile', 'Baile'),
        ('general', 'General'),
    ]
    evento = models.ForeignKey(EventoBoda, on_delete=models.CASCADE, related_name='itinerario')
    hora = models.TimeField()
    titulo = models.CharField(max_length=100)
    descripcion = models.CharField(max_length=180, blank=True, null=True)
    icono = models.CharField(max_length=20, choices=ICONOS, default='general')
    orden = models.PositiveIntegerField(default=0)
    visible = models.BooleanField(default=True)

    class Meta:
        ordering = ['orden', 'hora', 'id']

    def __str__(self):
        return f'{self.hora:%H:%M} - {self.titulo}'


class MenuBoda(models.Model):
    evento = models.ForeignKey(EventoBoda, on_delete=models.CASCADE, related_name='menus')
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True, null=True)
    tipo = models.CharField(
        max_length=20,
        choices=[
            ('ADULTO', 'Adulto'),
            ('NINO', 'Niño'),
            ('GENERAL', 'General'),
        ],
        default='GENERAL'
    )
    visible = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre


# Modelo que representa una invitación completa para una persona, pareja o familia.
# Cada grupo tiene un UUID único para acceder a su invitación.
class DetalleProduccionEvento(models.Model):
    evento = models.OneToOneField(
        EventoBoda,
        on_delete=models.CASCADE,
        related_name='detalle_produccion',
    )
    folio_contrato = models.CharField(max_length=80, blank=True, null=True)
    cliente_contrato = models.CharField(max_length=180, blank=True, null=True)
    arrendador = models.CharField(max_length=180, blank=True, null=True)
    lugar_contrato = models.CharField(max_length=180, blank=True, null=True)
    adultos_contratados = models.PositiveIntegerField(default=0)
    ninos_contratados = models.PositiveIntegerField(default=0)
    horas_evento = models.PositiveIntegerField(default=0)
    recepcion_hora = models.TimeField(blank=True, null=True)
    inicio_evento = models.TimeField(blank=True, null=True)
    fin_evento = models.TimeField(blank=True, null=True)
    minutos_desalojo = models.PositiveIntegerField(default=0)
    costo_hora_extra = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    precio_renta_salon = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    deposito_apartado = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    anticipo_recibido = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    saldo_contrato = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    dias_antes_liquidacion = models.PositiveIntegerField(default=0)
    banco = models.CharField(max_length=100, blank=True, null=True)
    numero_cuenta = models.CharField(max_length=80, blank=True, null=True)
    clabe = models.CharField(max_length=40, blank=True, null=True)
    tarjeta = models.CharField(max_length=80, blank=True, null=True)
    color_mantel = models.CharField(max_length=120, blank=True, null=True)
    color_servilleta = models.CharField(max_length=120, blank=True, null=True)
    tipo_mesa = models.CharField(max_length=160, blank=True, null=True)
    tamano_mesa = models.CharField(max_length=120, blank=True, null=True)
    mobiliario = models.TextField(blank=True, null=True)
    tipo_loza_cristaleria = models.TextField(blank=True, null=True)
    diseno_carpa = models.CharField(max_length=180, blank=True, null=True)
    tamano_carpa = models.CharField(max_length=120, blank=True, null=True)
    color_carpa = models.CharField(max_length=120, blank=True, null=True)
    montaje_carpa = models.TextField(blank=True, null=True)
    menu_entrada = models.TextField(blank=True, null=True)
    menu_plato_fuerte = models.TextField(blank=True, null=True)
    menu_postre = models.TextField(blank=True, null=True)
    menu_trasnochado = models.TextField(blank=True, null=True)
    menu_infantil = models.TextField(blank=True, null=True)
    bebidas = models.TextField(blank=True, null=True)
    servicios_incluidos = models.TextField(blank=True, null=True)
    notas_puntualidad = models.TextField(blank=True, null=True)
    politica_cancelacion = models.TextField(blank=True, null=True)
    notas_contrato = models.TextField(blank=True, null=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Detalle de produccion del evento'
        verbose_name_plural = 'Detalles de produccion de eventos'

    def __str__(self):
        return f'Detalle de produccion - {self.evento}'

    @property
    def total_personas_contratadas(self):
        return self.adultos_contratados + self.ninos_contratados


class Grupoinvitacion(models.Model):
    TIPO_INVITACION = [
        ('FAMILIAR', 'Familiar'),
        ('PERSONAL', 'Personal'),
    ]
    evento = models.ForeignKey(
        EventoBoda,
        on_delete=models.CASCADE,
        related_name='grupos',
        blank=True,
        null=True,
    )
    nombre_grupo = models.CharField(max_length=100)
    codigo = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    tipo = models.CharField(max_length=10, choices=TIPO_INVITACION)
    cantidad_maxima = models.IntegerField(default=1)
    cantidad_extra_permitida = models.PositiveIntegerField(default=0)
    permitir_acompanantes_extra = models.BooleanField(
        default=False,
        help_text='Solo el organizador habilita acompañantes adicionales sin nombre conocido.',
    )
    confirmado = models.BooleanField(default=False)
    asistira = models.BooleanField(null=True, blank=True)
    cantidad_confirmada = models.PositiveIntegerField(blank=True, null=True)
    acompanantes_adultos = models.PositiveIntegerField(default=0)
    acompanantes_ninos = models.PositiveIntegerField(default=0)
    comentario = models.TextField(blank=True, null=True)
    mesa = models.CharField(max_length=50, blank=True, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    telefono_contacto = models.CharField(max_length=20, blank=True, null=True)
    correo_contacto = models.EmailField(blank=True, null=True)
    restricciones_alimentarias = models.TextField(blank=True, null=True)
    alergias = models.TextField(blank=True, null=True)
    requiere_menu_infantil = models.BooleanField(default=False)
    fecha_confirmacion = models.DateTimeField(blank=True, null=True)
    estado_envio = models.CharField(
        max_length=30,
        choices=[
            ('PENDIENTE', 'Pendiente'),
            ('INVITACION_PREPARADA', 'Invitación preparada'),
            ('RECORDATORIO_PREPARADO', 'Recordatorio preparado'),
        ],
        default='PENDIENTE'
    )

    fecha_ultimo_envio = models.DateTimeField(blank=True, null=True)
    fecha_ultimo_recordatorio = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return self.nombre_grupo

    @property
    def es_personal(self):
        return self.tipo == 'PERSONAL'

    @property
    def es_familiar(self):
        return self.tipo == 'FAMILIAR'

    @property
    def invitados_nominales(self):
        if not self.pk:
            return Invitado.objects.none()
        return self.invitados.filter(es_acompanante_extra=False)

    @property
    def acompanantes_extra(self):
        if not self.pk:
            return Invitado.objects.none()
        return self.invitados.filter(es_acompanante_extra=True)

    @property
    def cantidad_acompanantes_autorizados(self):
        # During R.1 the numeric legacy field remains the compatibility source.
        # R.2 will make the enable/disable toggle set this value explicitly.
        return max(int(self.cantidad_extra_permitida or 0), 0)

    @property
    def total_personas_v2(self):
        if not self.pk:
            return 0
        return self.invitados.count()

    @property
    def confirmados_v2(self):
        if not self.pk:
            return 0
        return self.invitados.filter(asistira=True).count()

    @property
    def pendientes_v2(self):
        if not self.pk:
            return 0
        return self.invitados.filter(asistira__isnull=True).count()

    @property
    def total_lugares(self):
        invitados_count = self.invitados.count() if self.pk else 0
        if invitados_count:
            return invitados_count
        if self.es_personal:
            return 1 + self.cantidad_acompanantes_autorizados
        return self.cantidad_maxima

    @property
    def lugares_asistiran(self):
        invitados_count = self.invitados.count() if self.pk else 0
        if invitados_count:
            return self.invitados.filter(asistira=True).count()
        if self.es_personal and self.asistira is True:
            return 1 + self.acompanantes_adultos + self.acompanantes_ninos
        return 0

    @property
    def lugares_no_asistiran(self):
        invitados_count = self.invitados.count() if self.pk else 0
        if invitados_count:
            return self.invitados.filter(asistira=False).count()
        if self.es_personal and self.asistira is False:
            return self.total_lugares
        return 0

    @property
    def lugares_pendientes(self):
        invitados_count = self.invitados.count() if self.pk else 0
        if invitados_count:
            return self.invitados.filter(asistira__isnull=True).count()
        if self.es_personal and self.asistira is None:
            return self.total_lugares
        return self.cantidad_maxima if self.es_familiar else 0

    @property
    def adultos_confirmados(self):
        invitados_count = self.invitados.count() if self.pk else 0
        if invitados_count:
            return self.invitados.filter(asistira=True, tipo_persona='ADULTO').count()
        return (1 + self.acompanantes_adultos) if self.es_personal and self.asistira is True else 0

    @property
    def ninos_confirmados(self):
        invitados_count = self.invitados.count() if self.pk else 0
        if invitados_count:
            return self.invitados.filter(asistira=True, tipo_persona='NINO').count()
        return self.acompanantes_ninos if self.es_personal and self.asistira is True else 0



class Invitado(models.Model):
    TIPO_PERSONA = [
        ('ADULTO', 'Adulto'),
        ('NINO', 'Niño'),
    ]
    TIPO_MENU = [
        ('SEGUN_TIPO', 'Según tipo de persona'),
        ('ADULTO', 'Menú adulto'),
        ('INFANTIL', 'Menú infantil'),
    ]
    grupo = models.ForeignKey(Grupoinvitacion, on_delete=models.CASCADE, related_name='invitados')
    nombre = models.CharField(max_length=100)
    apellidos = models.CharField(max_length=120, blank=True, null=True)
    telefono = models.CharField(max_length=30, blank=True, null=True)
    correo = models.EmailField(blank=True, null=True)
    tipo_persona = models.CharField(max_length=10, choices=TIPO_PERSONA, default='ADULTO')
    es_acompanante_extra = models.BooleanField(default=False)
    menu_asignado = models.CharField(
        max_length=12,
        choices=TIPO_MENU,
        default='SEGUN_TIPO',
        help_text='Decisión interna del organizador. El invitado no modifica este valor.',
    )
    asistira = models.BooleanField(null=True, blank=True)
    comentario = models.TextField(blank=True, null=True)
    restricciones_alimentarias = models.TextField(blank=True, null=True)
    alergias = models.TextField(blank=True, null=True)
    menu_infantil = models.BooleanField(default=False)
    mesa = models.CharField(max_length=50, blank=True, null=True)
    notas = models.TextField(blank=True, null=True)
    fecha_confirmacion = models.DateTimeField(blank=True, null=True)
    orden = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['orden', 'id']

    @property
    def menu_buffet_efectivo(self):
        if self.menu_asignado == 'ADULTO':
            return 'ADULTO'
        if self.menu_asignado == 'INFANTIL':
            return 'INFANTIL'
        return 'INFANTIL' if self.tipo_persona == 'NINO' else 'ADULTO'

    def __str__(self):
        if self.apellidos:
            return f'{self.nombre} {self.apellidos}'
        return self.nombre
