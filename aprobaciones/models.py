from django.conf import settings
from django.db import models
from django.utils import timezone


class AprobacionEvento(models.Model):
    TIPOS = [
        ('DECORACION', 'Decoracion'),
        ('MENU', 'Menu'),
        ('PROVEEDOR', 'Proveedor'),
        ('PAQUETE', 'Paquete'),
        ('PRESUPUESTO', 'Presupuesto'),
        ('MESAS', 'Distribucion de mesas'),
        ('ITINERARIO', 'Itinerario'),
        ('INVITACION', 'Diseno de invitacion'),
        ('MUSICA', 'Musica'),
        ('OTRO', 'Otro'),
    ]
    ESTADOS = [
        ('PENDIENTE', 'Pendiente'),
        ('APROBADO', 'Aprobado'),
        ('RECHAZADO', 'Rechazado'),
        ('CAMBIOS', 'Solicitud de cambios'),
    ]

    evento = models.ForeignKey(
        'invitaciones.EventoBoda',
        on_delete=models.CASCADE,
        related_name='aprobaciones_evento',
    )
    tipo = models.CharField(max_length=30, choices=TIPOS)
    titulo = models.CharField(max_length=160)
    descripcion = models.TextField(blank=True, null=True)
    modelo = models.CharField(max_length=100, blank=True, null=True)
    objeto_id = models.PositiveIntegerField(blank=True, null=True)
    solicitado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='aprobaciones_solicitadas',
    )
    aprobado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='aprobaciones_respondidas',
    )
    estado = models.CharField(max_length=20, choices=ESTADOS, default='PENDIENTE')
    comentario = models.TextField(blank=True, null=True)
    fecha_solicitud = models.DateTimeField(default=timezone.now)
    fecha_respuesta = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ['evento', 'estado', '-fecha_solicitud']
        verbose_name = 'Aprobacion del evento'
        verbose_name_plural = 'Aprobaciones del evento'

    def __str__(self):
        return self.titulo

    def save(self, *args, **kwargs):
        if self.estado != 'PENDIENTE' and not self.fecha_respuesta:
            self.fecha_respuesta = timezone.now()
        if self.estado == 'PENDIENTE':
            self.fecha_respuesta = None
        super().save(*args, **kwargs)

# Create your models here.
