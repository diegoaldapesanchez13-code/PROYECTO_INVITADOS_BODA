from django.conf import settings
from django.db import models
from invitaciones.models import validar_documento


class DocumentoEvento(models.Model):
    TIPOS = [
        ('CONTRATO', 'Contrato'),
        ('COTIZACION', 'Cotizacion'),
        ('COMPROBANTE', 'Comprobante de pago'),
        ('FACTURA', 'Factura'),
        ('MENU', 'Menu'),
        ('FOTOGRAFIA', 'Fotografia'),
        ('DISENO', 'Diseno'),
        ('PLANO', 'Plano'),
        ('LISTA', 'Lista'),
        ('IDENTIFICACION', 'Identificacion'),
        ('OTRO', 'Otro'),
    ]

    evento = models.ForeignKey(
        'invitaciones.EventoBoda',
        on_delete=models.CASCADE,
        related_name='documentos_evento',
    )
    tipo_documento = models.CharField(max_length=30, choices=TIPOS, default='OTRO')
    titulo = models.CharField(max_length=160)
    archivo = models.FileField(upload_to='documentos/eventos/', validators=[validar_documento])
    proveedor = models.ForeignKey(
        'proveedores.Proveedor',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='documentos_evento',
    )
    descripcion = models.TextField(blank=True, null=True)
    fecha_carga = models.DateTimeField(auto_now_add=True)
    cargado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='documentos_cargados',
    )
    visible_cliente = models.BooleanField(default=False)

    class Meta:
        ordering = ['evento', '-fecha_carga']
        verbose_name = 'Documento del evento'
        verbose_name_plural = 'Documentos del evento'

    def __str__(self):
        return self.titulo

# Create your models here.
