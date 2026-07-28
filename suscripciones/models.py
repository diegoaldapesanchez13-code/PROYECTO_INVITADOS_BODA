from django.conf import settings
from django.db import models
from django.utils import timezone

from invitaciones.models import validar_documento


class PlanSuscripcion(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True)
    precio_mensual = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    precio_anual = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    limite_usuarios = models.PositiveIntegerField(default=5)
    limite_wedding_planners = models.PositiveIntegerField(default=3)
    limite_eventos_activos = models.PositiveIntegerField(default=10)
    limite_clientes = models.PositiveIntegerField(default=50)
    limite_almacenamiento_mb = models.PositiveIntegerField(default=1024)
    permite_proveedores = models.BooleanField(default=True)
    permite_reportes = models.BooleanField(default=True)
    permite_api = models.BooleanField(default=False)
    permite_personalizacion = models.BooleanField(default=False)
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['nombre']
        verbose_name = 'Plan de suscripcion'
        verbose_name_plural = 'Planes de suscripcion'

    def __str__(self):
        return self.nombre


class SuscripcionEmpresa(models.Model):
    ESTADOS = [
        ('PRUEBA', 'Prueba'),
        ('ACTIVA', 'Activa'),
        ('PROXIMA_A_VENCER', 'Proxima a vencer'),
        ('VENCIDA', 'Vencida'),
        ('SUSPENDIDA', 'Suspendida'),
        ('CANCELADA', 'Cancelada'),
    ]

    empresa = models.OneToOneField(
        'organizaciones.EmpresaSuscriptora',
        on_delete=models.CASCADE,
        related_name='suscripcion',
    )
    plan = models.ForeignKey(PlanSuscripcion, on_delete=models.PROTECT, related_name='suscripciones')
    fecha_inicio = models.DateField(default=timezone.localdate)
    fecha_vencimiento = models.DateField()
    fecha_periodo_gracia = models.DateField(null=True, blank=True)
    estado = models.CharField(max_length=25, choices=ESTADOS, default='PRUEBA')
    renovacion_automatica = models.BooleanField(default=False)
    bloqueada_manualmente = models.BooleanField(default=False)
    motivo_bloqueo = models.TextField(blank=True)
    observaciones = models.TextField(blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['fecha_vencimiento', 'empresa__nombre_comercial']
        verbose_name = 'Suscripcion de empresa'
        verbose_name_plural = 'Suscripciones de empresa'

    def __str__(self):
        return f'{self.empresa} - {self.plan}'

    @property
    def esta_vencida_por_fecha(self):
        return self.fecha_vencimiento < timezone.localdate()

    @property
    def dentro_periodo_gracia(self):
        hoy = timezone.localdate()
        return self.fecha_periodo_gracia and self.fecha_vencimiento < hoy <= self.fecha_periodo_gracia


class PagoSuscripcion(models.Model):
    ESTADOS = [
        ('PENDIENTE', 'Pendiente'),
        ('PAGADO', 'Pagado'),
        ('VENCIDO', 'Vencido'),
        ('CANCELADO', 'Cancelado'),
    ]

    empresa = models.ForeignKey(
        'organizaciones.EmpresaSuscriptora',
        on_delete=models.CASCADE,
        related_name='pagos_suscripcion',
    )
    suscripcion = models.ForeignKey(SuscripcionEmpresa, on_delete=models.CASCADE, related_name='pagos')
    monto = models.DecimalField(max_digits=12, decimal_places=2)
    fecha_vencimiento = models.DateField()
    fecha_pago = models.DateField(null=True, blank=True)
    metodo_pago = models.CharField(max_length=50, blank=True)
    referencia = models.CharField(max_length=150, blank=True)
    comprobante = models.FileField(
        upload_to='suscripciones/comprobantes/',
        validators=[validar_documento],
        null=True,
        blank=True,
    )
    estado = models.CharField(max_length=20, choices=ESTADOS, default='PENDIENTE')
    registrado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    notas = models.TextField(blank=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-fecha_vencimiento', '-fecha_registro']
        verbose_name = 'Pago de suscripcion'
        verbose_name_plural = 'Pagos de suscripcion'

    def __str__(self):
        return f'{self.empresa} - {self.monto} - {self.estado}'
