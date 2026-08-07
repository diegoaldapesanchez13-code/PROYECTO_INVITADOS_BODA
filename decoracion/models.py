from django.db import models
from invitaciones.models import validar_imagen


class ElementoDecoracion(models.Model):
    CATEGORIAS = [
        ('ARREGLOS', 'Arreglos'),
        ('FLORES', 'Flores'),
        ('MANTELES', 'Manteles'),
        ('SERVILLETAS', 'Servilletas'),
        ('SILLAS', 'Sillas'),
        ('MESAS', 'Mesas'),
        ('CENTROS_MESA', 'Centros de mesa'),
        ('ILUMINACION', 'Iluminacion'),
        ('ESCENARIO', 'Escenario'),
        ('CEREMONIA', 'Ceremonia'),
        ('RECEPCION', 'Recepcion'),
        ('MESA_PRINCIPAL', 'Mesa principal'),
        ('ACCESORIOS', 'Accesorios'),
        ('OTRO', 'Otro'),
    ]
    ESTADOS = [
        ('IDEA', 'Idea'),
        ('COTIZADO', 'Cotizado'),
        ('EN_REVISION', 'En revision'),
        ('APROBADO', 'Aprobado'),
        ('COMPRADO', 'Comprado'),
        ('RENTADO', 'Rentado'),
        ('LISTO_MONTAJE', 'Listo para montaje'),
        ('MONTADO', 'Montado'),
        ('CANCELADO', 'Cancelado'),
    ]

    evento = models.ForeignKey(
        'invitaciones.EventoBoda',
        on_delete=models.CASCADE,
        related_name='elementos_decoracion',
    )
    categoria = models.CharField(max_length=30, choices=CATEGORIAS, default='OTRO')
    nombre = models.CharField(max_length=140)
    descripcion = models.TextField(blank=True, null=True)
    cantidad = models.PositiveIntegerField(default=1)
    color = models.CharField(max_length=80, blank=True, null=True)
    material = models.CharField(max_length=120, blank=True, null=True)
    proveedor = models.ForeignKey(
        'proveedores.Proveedor',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='elementos_decoracion',
    )
    costo = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    imagen_referencia = models.FileField(upload_to='decoracion/referencias/', validators=[validar_imagen], blank=True, null=True)
    imagen_final = models.FileField(upload_to='decoracion/finales/', validators=[validar_imagen], blank=True, null=True)
    aprobado_cliente = models.BooleanField(default=False)
    estado = models.CharField(max_length=30, choices=ESTADOS, default='IDEA')
    notas = models.TextField(blank=True, null=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['evento', 'categoria', 'nombre']
        verbose_name = 'Elemento de decoracion'
        verbose_name_plural = 'Elementos de decoracion'

    def __str__(self):
        return f'{self.nombre} - {self.evento}'

# Create your models here.
