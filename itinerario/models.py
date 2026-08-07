from django.conf import settings
from django.db import models


class ActividadItinerario(models.Model):
    PRIORIDADES = [
        ('BAJA', 'Baja'),
        ('MEDIA', 'Media'),
        ('ALTA', 'Alta'),
        ('URGENTE', 'Urgente'),
    ]
    ESTADOS = [
        ('PENDIENTE', 'Pendiente'),
        ('CONFIRMADA', 'Confirmada'),
        ('EN_PROGRESO', 'En progreso'),
        ('COMPLETADA', 'Completada'),
        ('RETRASADA', 'Retrasada'),
        ('CANCELADA', 'Cancelada'),
    ]
    CATEGORIAS = [
        ('PROVEEDORES', 'Llegada de proveedores'),
        ('MONTAJE', 'Montaje'),
        ('MAQUILLAJE', 'Maquillaje'),
        ('PEINADO', 'Peinado'),
        ('FOTO_VIDEO', 'Foto y video'),
        ('CEREMONIA', 'Ceremonia'),
        ('TRASLADO', 'Traslado'),
        ('RECEPCION', 'Recepcion'),
        ('CENA', 'Cena'),
        ('BRINDIS', 'Brindis'),
        ('BAILE', 'Baile'),
        ('PASTEL', 'Pastel'),
        ('DESMONTAJE', 'Desmontaje'),
        ('OTRO', 'Otro'),
    ]

    evento = models.ForeignKey(
        'invitaciones.EventoBoda',
        on_delete=models.CASCADE,
        related_name='actividades_itinerario',
    )
    titulo = models.CharField(max_length=140)
    descripcion = models.TextField(blank=True, null=True)
    categoria = models.CharField(max_length=30, choices=CATEGORIAS, default='OTRO')
    fecha = models.DateField()
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField(blank=True, null=True)
    ubicacion = models.CharField(max_length=180, blank=True, null=True)
    responsable = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='actividades_responsable',
    )
    proveedor = models.ForeignKey(
        'proveedores.Proveedor',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='actividades_itinerario',
    )
    prioridad = models.CharField(max_length=20, choices=PRIORIDADES, default='MEDIA')
    estado = models.CharField(max_length=20, choices=ESTADOS, default='PENDIENTE')
    orden = models.PositiveIntegerField(default=0)
    notas = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['evento', 'fecha', 'hora_inicio', 'orden']
        verbose_name = 'Actividad de itinerario'
        verbose_name_plural = 'Actividades de itinerario'

    def __str__(self):
        return f'{self.hora_inicio:%H:%M} - {self.titulo}'

# Create your models here.
