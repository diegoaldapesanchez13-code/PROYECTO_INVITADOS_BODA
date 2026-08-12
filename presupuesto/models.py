from django.conf import settings
from django.db import models
from django.core.exceptions import ValidationError
from django.db.models import Sum
from django.utils import timezone
from invitaciones.models import validar_documento


class CategoriaGasto(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    activo = models.BooleanField(default=True)

    class Meta:
        ordering = ['nombre']
        verbose_name = 'Categoria de gasto'
        verbose_name_plural = 'Categorias de gasto'

    def __str__(self):
        return self.nombre


class GastoEvento(models.Model):
    ESTADOS = [
        ('PENDIENTE', 'Pendiente'),
        ('PARCIAL', 'Parcialmente pagado'),
        ('PAGADO', 'Pagado'),
        ('VENCIDO', 'Vencido'),
        ('CANCELADO', 'Cancelado'),
    ]

    evento = models.ForeignKey(
        'invitaciones.EventoBoda',
        on_delete=models.CASCADE,
        related_name='gastos_evento',
    )
    servicio_evento = models.ForeignKey(
        'proveedores.ServicioEvento',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='gastos_operativos',
        help_text='Servicio del evento que origina este gasto, cuando aplique.',
    )
    categoria = models.ForeignKey(
        CategoriaGasto,
        on_delete=models.PROTECT,
        related_name='gastos',
    )
    proveedor = models.ForeignKey(
        'proveedores.Proveedor',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='gastos_evento',
    )
    concepto = models.CharField(max_length=160)
    monto_estimado = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    monto_real = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    fecha_limite = models.DateField(blank=True, null=True)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='PENDIENTE')
    notas = models.TextField(blank=True, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['evento', 'fecha_limite', 'concepto']
        verbose_name = 'Gasto del evento'
        verbose_name_plural = 'Gastos del evento'

    def __str__(self):
        return f'{self.concepto} - {self.evento}'

    def clean(self):
        super().clean()
        if self.servicio_evento_id and self.evento_id:
            servicio_evento_id = (
                getattr(self.servicio_evento, 'evento_id', None)
                if 'servicio_evento' in self._state.fields_cache
                else None
            )
            if servicio_evento_id is None:
                from proveedores.models import ServicioEvento
                servicio_evento_id = ServicioEvento.objects.filter(pk=self.servicio_evento_id).values_list('evento_id', flat=True).first()
            if servicio_evento_id != self.evento_id:
                raise ValidationError({'servicio_evento': 'El servicio debe pertenecer al mismo evento que el gasto.'})
        if self.servicio_evento_id and self.proveedor_id:
            servicio_proveedor_id = (
                getattr(self.servicio_evento, 'proveedor_id', None)
                if 'servicio_evento' in self._state.fields_cache
                else None
            )
            if servicio_proveedor_id is None:
                from proveedores.models import ServicioEvento
                servicio_proveedor_id = ServicioEvento.objects.filter(pk=self.servicio_evento_id).values_list('proveedor_id', flat=True).first()
            if servicio_proveedor_id and servicio_proveedor_id != self.proveedor_id:
                raise ValidationError({'proveedor': 'El proveedor del gasto no coincide con el proveedor del servicio.'})

    @property
    def total_pagado(self):
        return self.pagos.aggregate(total=Sum('monto'))['total'] or 0

    @property
    def monto_objetivo(self):
        return self.monto_real or self.monto_estimado

    @property
    def saldo_pendiente(self):
        saldo = self.monto_objetivo - self.total_pagado
        return saldo if saldo > 0 else 0

    @property
    def esta_vencido(self):
        return (
            self.estado not in {'PAGADO', 'CANCELADO'}
            and self.fecha_limite
            and self.fecha_limite < timezone.localdate()
            and self.saldo_pendiente > 0
        )

    @property
    def porcentaje_pagado(self):
        objetivo = self.monto_objetivo
        if not objetivo:
            return 0
        return round((self.total_pagado / objetivo) * 100, 2)


class PagoEvento(models.Model):
    METODOS = [
        ('EFECTIVO', 'Efectivo'),
        ('TRANSFERENCIA', 'Transferencia'),
        ('TARJETA', 'Tarjeta'),
        ('CHEQUE', 'Cheque'),
        ('DEPOSITO', 'Deposito'),
        ('OTRO', 'Otro'),
    ]

    gasto = models.ForeignKey(
        GastoEvento,
        on_delete=models.CASCADE,
        related_name='pagos',
    )
    monto = models.DecimalField(max_digits=12, decimal_places=2)
    fecha_pago = models.DateField(default=timezone.localdate)
    metodo_pago = models.CharField(max_length=20, choices=METODOS, default='TRANSFERENCIA')
    referencia = models.CharField(max_length=120, blank=True, null=True)
    comprobante = models.FileField(upload_to='presupuesto/comprobantes/', validators=[validar_documento], blank=True, null=True)
    notas = models.TextField(blank=True, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-fecha_pago', '-id']
        verbose_name = 'Pago del evento'
        verbose_name_plural = 'Pagos del evento'

    def __str__(self):
        return f'Pago {self.monto} - {self.gasto}'

    @property
    def servicio_evento(self):
        return self.gasto.servicio_evento

# Create your models here.

class PagoClienteEvento(models.Model):
    """Pago reportado por un cliente hacia la empresa/planner del evento.

    No representa un pago al proveedor ni reemplaza PagoEvento/GastoEvento.
    Puede relacionarse opcionalmente con un ServicioEvento solo como concepto.
    """

    METODOS = PagoEvento.METODOS
    ESTADOS = [
        ('PENDIENTE', 'Pendiente de revisión'),
        ('RECIBIDO', 'Recibido por empresa / planner'),
        ('OBSERVADO', 'Observado / requiere revisión'),
        ('CANCELADO', 'Cancelado'),
    ]

    evento = models.ForeignKey(
        'invitaciones.EventoBoda',
        on_delete=models.CASCADE,
        related_name='pagos_cliente_reportados',
    )
    servicio_evento = models.ForeignKey(
        'proveedores.ServicioEvento',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='pagos_cliente_evento',
        help_text='Concepto opcional del pago; el receptor sigue siendo la empresa/planner.',
    )
    registrado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='pagos_cliente_evento_registrados',
    )
    concepto = models.CharField(max_length=160, blank=True, null=True)
    monto = models.DecimalField(max_digits=12, decimal_places=2)
    fecha_pago = models.DateField(default=timezone.localdate)
    metodo_pago = models.CharField(max_length=20, choices=METODOS, default='TRANSFERENCIA')
    referencia = models.CharField(max_length=120, blank=True, null=True)
    comprobante = models.FileField(
        upload_to='presupuesto/pagos_cliente_evento/',
        validators=[validar_documento],
    )
    comentario_cliente = models.TextField(blank=True, null=True)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='PENDIENTE')
    comentario_equipo = models.TextField(blank=True, null=True)
    revisado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='pagos_cliente_evento_revisados',
    )
    fecha_revision = models.DateTimeField(blank=True, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-fecha_pago', '-id']
        indexes = [
            models.Index(fields=['evento', 'estado'], name='pres_pago_cli_evt_est_idx'),
            models.Index(fields=['registrado_por', 'estado'], name='pres_pago_cli_usr2_est_idx'),
        ]
        verbose_name = 'Pago reportado por cliente'
        verbose_name_plural = 'Pagos reportados por clientes'

    def __str__(self):
        return f'Pago cliente {self.monto} · {self.evento}'

    def clean(self):
        super().clean()
        if self.monto is not None and self.monto <= 0:
            raise ValidationError({'monto': 'El monto debe ser mayor a cero.'})
        if self.servicio_evento_id and self.evento_id:
            if self.servicio_evento.evento_id != self.evento_id:
                raise ValidationError({'servicio_evento': 'El servicio debe pertenecer al mismo evento.'})
        if self.registrado_por_id and self.evento_id:
            es_cliente = self.evento.clientes.filter(id=self.registrado_por_id).exists()
            if not es_cliente:
                from eventos.models import ParticipanteEvento
                es_cliente = ParticipanteEvento.objects.filter(
                    evento_id=self.evento_id,
                    usuario_id=self.registrado_por_id,
                    rol='CLIENTE',
                    activo=True,
                ).exists()
            if not es_cliente:
                raise ValidationError({'registrado_por': 'El pago debe ser registrado por un cliente del evento.'})

    @property
    def comprobante_es_imagen(self):
        nombre = (self.comprobante.name or '').lower() if self.comprobante else ''
        return nombre.endswith(('.jpg', '.jpeg', '.png', '.webp'))

