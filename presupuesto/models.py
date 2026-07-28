from django.db import models
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

# Create your models here.
