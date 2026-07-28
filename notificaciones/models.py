from django.conf import settings
from django.db import models
from django.utils import timezone


class Notificacion(models.Model):
    TIPOS = [
        ('INFO', 'Informacion'),
        ('ALERTA', 'Alerta'),
        ('PAGO', 'Pago'),
        ('TAREA', 'Tarea'),
        ('PROVEEDOR', 'Proveedor'),
        ('INVITADOS', 'Invitados'),
        ('DOCUMENTO', 'Documento'),
        ('APROBACION', 'Aprobacion'),
    ]

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notificaciones',
    )
    evento = models.ForeignKey(
        'invitaciones.EventoBoda',
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name='notificaciones_evento',
    )
    titulo = models.CharField(max_length=140)
    mensaje = models.TextField()
    tipo = models.CharField(max_length=20, choices=TIPOS, default='INFO')
    leida = models.BooleanField(default=False)
    fecha_creacion = models.DateTimeField(default=timezone.now)
    enlace = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        ordering = ['leida', '-fecha_creacion']
        verbose_name = 'Notificacion'
        verbose_name_plural = 'Notificaciones'

    def __str__(self):
        return self.titulo

# Create your models here.
