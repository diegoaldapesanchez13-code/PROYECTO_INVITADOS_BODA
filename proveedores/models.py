from django.conf import settings
from django.db import models
from invitaciones.models import validar_documento


class Proveedor(models.Model):
    TIPOS = [
        ('SALON', 'Salon'),
        ('JARDIN', 'Jardin'),
        ('BANQUETE', 'Banquete'),
        ('BUFFET', 'Buffet'),
        ('FOTOGRAFIA', 'Fotografia'),
        ('VIDEO', 'Video'),
        ('BANDA', 'Banda'),
        ('DJ', 'DJ'),
        ('MUSICA_VIVO', 'Musica en vivo'),
        ('DECORACION', 'Decoracion'),
        ('FLORERIA', 'Floreria'),
        ('MANTELERIA', 'Manteleria'),
        ('MESEROS', 'Meseros'),
        ('BARRA', 'Barra de bebidas'),
        ('PASTEL', 'Pastel'),
        ('TRANSPORTE', 'Transporte'),
        ('MAQUILLAJE', 'Maquillaje'),
        ('PEINADO', 'Peinado'),
        ('VESTUARIO', 'Vestuario'),
        ('SEGURIDAD', 'Seguridad'),
        ('ILUMINACION', 'Iluminacion'),
        ('AUDIO', 'Audio'),
        ('MOBILIARIO', 'Renta de mobiliario'),
        ('INVITACIONES', 'Invitaciones'),
        ('RECUERDOS', 'Recuerdos'),
        ('OTROS', 'Otros'),
    ]

    empresa = models.ForeignKey(
        'organizaciones.EmpresaSuscriptora',
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        related_name='proveedores',
    )
    nombre_comercial = models.CharField(max_length=160)
    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='perfil_proveedor',
    )
    razon_social = models.CharField(max_length=180, blank=True, null=True)
    tipo_proveedor = models.CharField(max_length=30, choices=TIPOS, default='OTROS')
    nombre_contacto = models.CharField(max_length=120, blank=True, null=True)
    telefono = models.CharField(max_length=30, blank=True, null=True)
    correo = models.EmailField(blank=True, null=True)
    direccion = models.CharField(max_length=255, blank=True, null=True)
    sitio_web = models.URLField(blank=True, null=True)
    redes_sociales = models.TextField(blank=True, null=True)
    descripcion = models.TextField(blank=True, null=True)
    contacto_operativo = models.CharField(max_length=160, blank=True, null=True)
    telefono_operativo = models.CharField(max_length=30, blank=True, null=True)
    correo_operativo = models.EmailField(blank=True, null=True)
    visible_para_wedding_planners = models.BooleanField(default=True)
    rfc = models.CharField(max_length=20, blank=True, null=True)
    datos_bancarios = models.TextField(blank=True, null=True)
    notas_privadas = models.TextField(blank=True, null=True)
    calificacion = models.DecimalField(max_digits=3, decimal_places=2, default=0)
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['nombre_comercial']
        verbose_name = 'Proveedor'
        verbose_name_plural = 'Proveedores'

    def __str__(self):
        return self.nombre_comercial

    @property
    def contacto_visible(self):
        return self.contacto_operativo or self.nombre_contacto

    @property
    def telefono_visible(self):
        return self.telefono_operativo or self.telefono

    @property
    def correo_visible(self):
        return self.correo_operativo or self.correo


class ServicioEvento(models.Model):
    ESTADOS = [
        ('SOLICITADO', 'Solicitado'),
        ('COTIZADO', 'Cotizado'),
        ('PENDIENTE_APROBACION', 'Pendiente de aprobacion'),
        ('APROBADO', 'Aprobado'),
        ('CONTRATADO', 'Contratado'),
        ('ANTICIPO_PAGADO', 'Anticipo pagado'),
        ('LIQUIDADO', 'Liquidado'),
        ('CANCELADO', 'Cancelado'),
        ('SERVICIO_COMPLETADO', 'Servicio completado'),
    ]

    evento = models.ForeignKey(
        'invitaciones.EventoBoda',
        on_delete=models.CASCADE,
        related_name='servicios_contratados',
    )
    proveedor = models.ForeignKey(
        Proveedor,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='servicios_evento',
    )
    nombre_servicio = models.CharField(max_length=160)
    descripcion = models.TextField(blank=True, null=True)
    fecha_servicio = models.DateField(blank=True, null=True)
    hora_inicio = models.TimeField(blank=True, null=True)
    hora_fin = models.TimeField(blank=True, null=True)
    lugar = models.CharField(max_length=180, blank=True, null=True)
    costo_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    anticipo = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    fecha_limite_pago = models.DateField(blank=True, null=True)
    estado = models.CharField(max_length=30, choices=ESTADOS, default='SOLICITADO')
    contrato = models.FileField(upload_to='proveedores/contratos/', validators=[validar_documento], blank=True, null=True)
    cotizacion = models.FileField(upload_to='proveedores/cotizaciones/', validators=[validar_documento], blank=True, null=True)
    comprobante_pago = models.FileField(upload_to='proveedores/comprobantes/', validators=[validar_documento], blank=True, null=True)
    notas = models.TextField(blank=True, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['evento', 'fecha_servicio', 'hora_inicio', 'nombre_servicio']
        verbose_name = 'Servicio contratado'
        verbose_name_plural = 'Servicios contratados'

    def __str__(self):
        return f'{self.nombre_servicio} - {self.evento}'

    @property
    def saldo_pendiente(self):
        saldo = self.costo_total - self.anticipo
        return saldo if saldo > 0 else 0


class PersonalEvento(models.Model):
    TIPOS = [
        ('CAPITAN', 'Capitan de meseros'),
        ('MESERO', 'Mesero'),
        ('BARTENDER', 'Bartender'),
        ('COCINA', 'Personal de cocina'),
        ('LIMPIEZA', 'Limpieza'),
        ('SEGURIDAD', 'Seguridad'),
        ('MONTAJE', 'Montaje'),
        ('COORDINACION', 'Coordinacion'),
        ('OTRO', 'Otro'),
    ]
    ESTADOS = [
        ('REQUERIDO', 'Requerido'),
        ('CONFIRMADO', 'Confirmado'),
        ('EN_SITIO', 'En sitio'),
        ('FINALIZADO', 'Finalizado'),
        ('CANCELADO', 'Cancelado'),
    ]

    evento = models.ForeignKey(
        'invitaciones.EventoBoda',
        on_delete=models.CASCADE,
        related_name='personal_evento',
    )
    proveedor = models.ForeignKey(
        Proveedor,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='personal_asignado',
    )
    nombre = models.CharField(max_length=120)
    tipo_personal = models.CharField(max_length=20, choices=TIPOS, default='MESERO')
    telefono = models.CharField(max_length=30, blank=True, null=True)
    hora_entrada = models.TimeField(blank=True, null=True)
    hora_salida = models.TimeField(blank=True, null=True)
    area_asignada = models.CharField(max_length=120, blank=True, null=True)
    mesas_asignadas = models.CharField(max_length=180, blank=True, null=True)
    costo = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    uniforme = models.CharField(max_length=180, blank=True, null=True)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='REQUERIDO')
    notas = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['evento', 'tipo_personal', 'nombre']
        verbose_name = 'Personal del evento'
        verbose_name_plural = 'Personal del evento'

    def __str__(self):
        return f'{self.nombre} ({self.get_tipo_personal_display()})'

# Create your models here.
