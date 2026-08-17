from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from catalogo.storage import private_catalogo_storage
from invitaciones.models import validar_documento, validar_imagen


TIPOS_SERVICIO = [
    ('SALON', 'Salon'),
    ('BANQUETE', 'Banquete'),
    ('MESEROS', 'Meseros'),
    ('DECORACION', 'Decoracion'),
    ('MANTELERIA', 'Manteleria'),
    ('DJ', 'DJ'),
    ('BANDA', 'Banda'),
    ('FOTOGRAFIA', 'Fotografia'),
    ('VIDEO', 'Video'),
    ('PASTEL', 'Pastel'),
    ('BARRA_LIBRE', 'Barra libre'),
    ('INVITACIONES', 'Invitaciones'),
    ('COORDINACION', 'Coordinacion'),
    ('MOBILIARIO', 'Mobiliario'),
    ('ILUMINACION', 'Iluminacion'),
    ('TRANSPORTE', 'Transporte'),
    ('OTRO', 'Otro'),
]


class PaqueteBoda(models.Model):
    empresa = models.ForeignKey(
        'organizaciones.EmpresaSuscriptora',
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        related_name='paquetes',
    )
    nombre = models.CharField(max_length=140)
    descripcion = models.TextField(blank=True, null=True)
    precio_base = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    numero_personas_incluidas = models.PositiveIntegerField(default=0)
    precio_adulto = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    precio_nino = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    cargo_fijo = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    capacidad_minima_recomendada = models.PositiveIntegerField(blank=True, null=True)
    capacidad_maxima_recomendada = models.PositiveIntegerField(blank=True, null=True)
    duracion_evento = models.PositiveIntegerField(blank=True, null=True, help_text='Duracion comercial en horas.')
    portada = models.FileField(
        storage=private_catalogo_storage,
        upload_to='paquetes/portadas/',
        validators=[validar_imagen],
        blank=True,
        null=True,
    )
    pdf_comercial = models.FileField(
        storage=private_catalogo_storage,
        upload_to='paquetes/pdfs/',
        validators=[validar_documento],
        blank=True,
        null=True,
    )
    activo = models.BooleanField(default=True)

    class Meta:
        ordering = ['nombre']
        verbose_name = 'Paquete comercial'
        verbose_name_plural = 'Paquetes comerciales'

    def __str__(self):
        return self.nombre

    def clean(self):
        super().clean()
        if (
            self.capacidad_minima_recomendada
            and self.capacidad_maxima_recomendada
            and self.capacidad_minima_recomendada > self.capacidad_maxima_recomendada
        ):
            raise ValidationError({
                'capacidad_maxima_recomendada': 'La capacidad maxima debe ser mayor o igual a la minima.'
            })
        if self.pdf_comercial:
            validar_documento(self.pdf_comercial)
            nombre = getattr(self.pdf_comercial, 'name', '') or ''
            if not nombre.lower().endswith('.pdf'):
                raise ValidationError({'pdf_comercial': 'PDF comercial: formato no permitido. Usa: pdf.'})


class PaqueteMediaComercial(models.Model):
    TIPOS = [
        ('IMAGEN', 'Imagen'),
        ('PDF', 'PDF'),
    ]

    paquete = models.ForeignKey(
        PaqueteBoda,
        on_delete=models.CASCADE,
        related_name='media_comercial',
    )
    tipo = models.CharField(max_length=10, choices=TIPOS)
    archivo = models.FileField(storage=private_catalogo_storage, upload_to='paquetes/media/')
    titulo = models.CharField(max_length=140, blank=True, null=True)
    orden = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['paquete', 'orden', 'id']
        indexes = [
            models.Index(fields=['paquete', 'tipo'], name='paq_media_pkg_tipo_idx'),
        ]
        verbose_name = 'Media comercial de paquete'
        verbose_name_plural = 'Media comercial de paquetes'

    def __str__(self):
        return self.titulo or f'{self.get_tipo_display()} - {self.paquete}'

    def clean(self):
        super().clean()
        if self.tipo == 'IMAGEN':
            validar_imagen(self.archivo)
        elif self.tipo == 'PDF':
            validar_documento(self.archivo)
            nombre = getattr(self.archivo, 'name', '') or ''
            if not nombre.lower().endswith('.pdf'):
                raise ValidationError({'archivo': 'PDF: formato no permitido. Usa: pdf.'})


class PaqueteServicio(models.Model):
    paquete = models.ForeignKey(
        PaqueteBoda,
        on_delete=models.CASCADE,
        related_name='servicios_catalogo_k9',
    )
    servicio_catalogo = models.ForeignKey(
        'catalogo.ServicioCatalogo',
        on_delete=models.PROTECT,
        related_name='paquetes_servicio_k9',
    )
    cantidad = models.DecimalField(max_digits=10, decimal_places=2, default=1)
    orden = models.PositiveIntegerField(default=0)
    notas = models.TextField(blank=True, null=True)
    incluido = models.BooleanField(default=True)
    obligatorio = models.BooleanField(default=True)
    config = models.JSONField(default=dict, blank=True)
    clave_origen = models.CharField(max_length=80, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['paquete', 'orden', 'id']
        constraints = [
            models.UniqueConstraint(
                fields=['paquete', 'clave_origen'],
                name='paquete_servicio_clave_origen_unica',
            ),
        ]
        indexes = [
            models.Index(fields=['paquete', 'incluido'], name='paq_srv_pkg_incl_idx'),
            models.Index(fields=['servicio_catalogo'], name='paq_srv_catalogo_idx'),
        ]
        verbose_name = 'Servicio K9 de paquete'
        verbose_name_plural = 'Servicios K9 de paquete'

    def __str__(self):
        return f'{self.servicio_catalogo} - {self.paquete}'

    def clean(self):
        super().clean()
        if not self.paquete_id:
            raise ValidationError({'paquete': 'El servicio debe pertenecer a un paquete.'})
        if not self.servicio_catalogo_id:
            raise ValidationError({'servicio_catalogo': 'Selecciona un servicio del catalogo.'})
        if self.paquete.empresa_id != self.servicio_catalogo.empresa_id:
            raise ValidationError({
                'servicio_catalogo': 'El servicio debe pertenecer a la misma empresa del paquete.'
            })
        if self.cantidad <= 0:
            raise ValidationError({'cantidad': 'La cantidad debe ser mayor a cero.'})
        if not self.clave_origen:
            self.clave_origen = f'catalogo:{self.servicio_catalogo_id}'

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class ServicioPaquete(models.Model):
    paquete = models.ForeignKey(
        PaqueteBoda,
        on_delete=models.CASCADE,
        related_name='servicios',
    )
    tipo_servicio = models.CharField(max_length=30, choices=TIPOS_SERVICIO)
    descripcion = models.CharField(max_length=220)
    cantidad = models.PositiveIntegerField(default=1)
    precio_incluido = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    class Meta:
        ordering = ['paquete', 'tipo_servicio', 'descripcion']
        verbose_name = 'Servicio de paquete'
        verbose_name_plural = 'Servicios de paquete'

    def __str__(self):
        return f'{self.get_tipo_servicio_display()} - {self.paquete}'


class PaqueteEvento(models.Model):
    ESTADOS = [
        ('PROPUESTO', 'Propuesto'),
        ('EN_REVISION', 'En revision'),
        ('APROBADO', 'Aprobado'),
        ('CONTRATADO', 'Contratado'),
        ('CANCELADO', 'Cancelado'),
    ]

    evento = models.ForeignKey(
        'invitaciones.EventoBoda',
        on_delete=models.CASCADE,
        related_name='paquetes_evento',
    )
    paquete = models.ForeignKey(
        PaqueteBoda,
        on_delete=models.PROTECT,
        related_name='eventos',
    )
    precio_acordado = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    servicios_adicionales = models.TextField(blank=True, null=True)
    descuento = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='PROPUESTO')
    notas = models.TextField(blank=True, null=True)

    # K.8.3: snapshot contractual congelado del paquete maestro. Una vez
    # generado, cambios posteriores en PaqueteBoda/ServicioPaquete no alteran
    # el acuerdo historico del evento.
    snapshot_paquete = models.JSONField(default=dict, blank=True)
    snapshot_generado_en = models.DateTimeField(blank=True, null=True)
    materializado_en = models.DateTimeField(blank=True, null=True)
    materializacion_version = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ['evento', 'estado', 'paquete__nombre']
        verbose_name = 'Paquete asignado al evento'
        verbose_name_plural = 'Paquetes asignados a eventos'

    def __str__(self):
        return f'{self.paquete} - {self.evento}'

    def clean(self):
        super().clean()
        if not self.evento_id or not self.paquete_id:
            return
        evento_empresa_id = getattr(self.evento, 'empresa_id', None)
        paquete_empresa_id = getattr(self.paquete, 'empresa_id', None)
        if evento_empresa_id and paquete_empresa_id and evento_empresa_id != paquete_empresa_id:
            raise ValidationError(
                {'paquete': 'El paquete debe pertenecer a la misma empresa del evento.'}
            )

    def save(self, *args, **kwargs):
        if not self.total:
            base = self.precio_acordado or self.paquete.precio_base
            self.total = base - self.descuento
        super().save(*args, **kwargs)

    @property
    def tiene_snapshot(self):
        return bool(self.snapshot_paquete)

    @property
    def esta_materializado(self):
        return self.materializado_en is not None


class PropuestaEvento(models.Model):
    ESTADOS = [
        ('BORRADOR', 'Borrador'),
        ('PROPUESTA', 'Propuesta'),
        ('EN_REVISION', 'En revision'),
        ('ACEPTADO', 'Aceptado'),
        ('CANCELADO', 'Cancelado'),
    ]

    empresa = models.ForeignKey(
        'organizaciones.EmpresaSuscriptora',
        on_delete=models.PROTECT,
        related_name='propuestas_k9',
    )
    evento = models.ForeignKey(
        'invitaciones.EventoBoda',
        on_delete=models.PROTECT,
        related_name='propuestas_k9',
    )
    sede = models.ForeignKey(
        'organizaciones.SedeEvento',
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        related_name='propuestas_k9',
    )
    paquete = models.ForeignKey(
        PaqueteBoda,
        on_delete=models.PROTECT,
        related_name='propuestas_k9',
    )
    adultos = models.PositiveIntegerField(default=0)
    ninos = models.PositiveIntegerField(default=0)
    descuento = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='BORRADOR')
    notas_comerciales = models.TextField(blank=True, null=True)
    subtotal_base = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    version_calculo = models.PositiveIntegerField(default=1)
    desglose_calculado = models.JSONField(default=dict, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='propuestas_k9_creadas',
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='propuestas_k9_actualizadas',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['evento', '-updated_at', '-id']
        indexes = [
            models.Index(fields=['empresa', 'estado'], name='paq_prop_emp_est_idx'),
            models.Index(fields=['evento', 'estado'], name='paq_prop_evt_est_idx'),
        ]
        verbose_name = 'Propuesta comercial K9'
        verbose_name_plural = 'Propuestas comerciales K9'

    def __str__(self):
        return f'Propuesta {self.get_estado_display()} - {self.evento}'

    def clean(self):
        super().clean()
        if not self.empresa_id:
            raise ValidationError({'empresa': 'La propuesta debe pertenecer a una empresa.'})
        if self.evento_id and self.evento.empresa_id != self.empresa_id:
            raise ValidationError({'evento': 'El evento debe pertenecer a la misma empresa.'})
        if self.sede_id and self.sede.empresa_id != self.empresa_id:
            raise ValidationError({'sede': 'La sede debe pertenecer a la misma empresa.'})
        if self.paquete_id and self.paquete.empresa_id != self.empresa_id:
            raise ValidationError({'paquete': 'El paquete debe pertenecer a la misma empresa.'})
        if self.descuento < 0:
            raise ValidationError({'descuento': 'El descuento no puede ser negativo.'})


class PropuestaLinea(models.Model):
    TIPOS = [
        ('ADICIONAL', 'Adicional'),
        ('CORTESIA', 'Cortesia'),
    ]
    MODOS_PRECIO = [
        ('FIJO', 'Fijo'),
        ('POR_ADULTO', 'Por adulto'),
        ('POR_NINO', 'Por nino'),
        ('POR_PERSONA', 'Por persona'),
        ('POR_UNIDAD', 'Por unidad'),
        ('MANUAL', 'Manual'),
    ]

    propuesta = models.ForeignKey(
        PropuestaEvento,
        on_delete=models.CASCADE,
        related_name='lineas',
    )
    tipo = models.CharField(max_length=12, choices=TIPOS, default='ADICIONAL')
    servicio_catalogo = models.ForeignKey(
        'catalogo.ServicioCatalogo',
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        related_name='lineas_propuesta_k9',
    )
    nombre = models.CharField(max_length=160)
    descripcion = models.TextField(blank=True, null=True)
    modo_precio = models.CharField(max_length=20, choices=MODOS_PRECIO, default='FIJO')
    tarifa = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    cantidad = models.DecimalField(max_digits=10, decimal_places=2, default=1)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    valor_informativo = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    orden = models.PositiveIntegerField(default=0)
    activo = models.BooleanField(default=True)
    snapshot_linea = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['propuesta', 'orden', 'id']
        indexes = [
            models.Index(fields=['propuesta', 'tipo', 'activo'], name='paq_linea_prop_tipo_idx'),
            models.Index(fields=['servicio_catalogo'], name='paq_linea_catalogo_idx'),
        ]
        verbose_name = 'Linea de propuesta K9'
        verbose_name_plural = 'Lineas de propuesta K9'

    def __str__(self):
        return f'{self.get_tipo_display()} - {self.nombre}'

    def clean(self):
        super().clean()
        if not self.propuesta_id:
            raise ValidationError({'propuesta': 'La linea debe pertenecer a una propuesta.'})
        if self.servicio_catalogo_id:
            if self.servicio_catalogo.empresa_id != self.propuesta.empresa_id:
                raise ValidationError({
                    'servicio_catalogo': 'El servicio debe pertenecer a la misma empresa de la propuesta.'
                })
            if not self.servicio_catalogo.activo:
                raise ValidationError({'servicio_catalogo': 'No puedes agregar un servicio de catalogo inactivo.'})
            if not self.nombre:
                self.nombre = self.servicio_catalogo.nombre
        if not (self.nombre or '').strip():
            raise ValidationError({'nombre': 'El nombre de la linea es obligatorio.'})
        self.nombre = self.nombre.strip()
        if self.tarifa < 0:
            raise ValidationError({'tarifa': 'La tarifa no puede ser negativa.'})
        if self.cantidad <= 0:
            raise ValidationError({'cantidad': 'La cantidad debe ser mayor a cero.'})

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
