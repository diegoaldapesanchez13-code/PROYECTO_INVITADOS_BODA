from django.conf import settings
from django.db import models
from django.core.exceptions import ValidationError
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
    servicio_evento = models.ForeignKey(
        'proveedores.ServicioEvento',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='documentos_operativos',
        help_text='Servicio del evento al que corresponde el documento, cuando aplique.',
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
    visible_proveedor = models.BooleanField(default=False)
    archivado_en = models.DateTimeField(blank=True, null=True)
    archivado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='documentos_evento_archivados',
    )
    motivo_archivo = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['evento', '-fecha_carga']
        verbose_name = 'Documento del evento'
        verbose_name_plural = 'Documentos del evento'

    def __str__(self):
        return self.titulo

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
                raise ValidationError({'servicio_evento': 'El servicio debe pertenecer al mismo evento que el documento.'})

# Create your models here.
