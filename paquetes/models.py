from django.db import models


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
    activo = models.BooleanField(default=True)

    class Meta:
        ordering = ['nombre']
        verbose_name = 'Paquete comercial'
        verbose_name_plural = 'Paquetes comerciales'

    def __str__(self):
        return self.nombre


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

    class Meta:
        ordering = ['evento', 'estado', 'paquete__nombre']
        verbose_name = 'Paquete asignado al evento'
        verbose_name_plural = 'Paquetes asignados a eventos'

    def __str__(self):
        return f'{self.paquete} - {self.evento}'

    def save(self, *args, **kwargs):
        if not self.total:
            base = self.precio_acordado or self.paquete.precio_base
            self.total = base - self.descuento
        super().save(*args, **kwargs)

# Create your models here.
