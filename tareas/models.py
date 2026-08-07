from django.conf import settings
from django.db import models
from django.utils import timezone
from invitaciones.models import validar_documento


class TareaEvento(models.Model):
    ESTADOS = [
        ('PENDIENTE', 'Pendiente'),
        ('EN_PROCESO', 'En proceso'),
        ('EN_REVISION', 'En revision'),
        ('COMPLETADA', 'Completada'),
        ('CANCELADA', 'Cancelada'),
    ]
    PRIORIDADES = [
        ('BAJA', 'Baja'),
        ('MEDIA', 'Media'),
        ('ALTA', 'Alta'),
        ('URGENTE', 'Urgente'),
    ]
    CATEGORIAS = [
        ('GENERAL', 'General'),
        ('INVITADOS', 'Invitados'),
        ('PROVEEDORES', 'Proveedores'),
        ('CATERING', 'Catering'),
        ('DECORACION', 'Decoracion'),
        ('MUSICA', 'Musica'),
        ('MESAS', 'Mesas'),
        ('PRESUPUESTO', 'Presupuesto'),
        ('DOCUMENTOS', 'Documentos'),
        ('OTRA', 'Otra'),
    ]

    evento = models.ForeignKey(
        'invitaciones.EventoBoda',
        on_delete=models.CASCADE,
        related_name='tareas_evento',
    )
    titulo = models.CharField(max_length=160)
    descripcion = models.TextField(blank=True, null=True)
    responsable = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='tareas_asignadas',
    )
    fecha_inicio = models.DateField(blank=True, null=True)
    fecha_limite = models.DateField(blank=True, null=True)
    prioridad = models.CharField(max_length=20, choices=PRIORIDADES, default='MEDIA')
    estado = models.CharField(max_length=20, choices=ESTADOS, default='PENDIENTE')
    porcentaje_avance = models.PositiveIntegerField(default=0)
    categoria = models.CharField(max_length=20, choices=CATEGORIAS, default='GENERAL')
    evidencia = models.FileField(upload_to='tareas/evidencias/', validators=[validar_documento], blank=True, null=True)
    notas = models.TextField(blank=True, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['evento', 'fecha_limite', 'prioridad', 'titulo']
        verbose_name = 'Tarea del evento'
        verbose_name_plural = 'Tareas del evento'

    def __str__(self):
        return self.titulo

    @property
    def esta_vencida(self):
        return (
            self.estado not in {'COMPLETADA', 'CANCELADA'}
            and self.fecha_limite
            and self.fecha_limite < timezone.localdate()
        )

    def save(self, *args, **kwargs):
        if self.estado == 'COMPLETADA':
            self.porcentaje_avance = 100
        if self.porcentaje_avance > 100:
            self.porcentaje_avance = 100
        super().save(*args, **kwargs)

# Create your models here.
