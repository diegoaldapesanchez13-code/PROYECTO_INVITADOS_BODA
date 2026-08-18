from django.conf import settings
from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import datetime
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
    servicio_evento = models.ForeignKey(
        'proveedores.ServicioEvento',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='tareas_operativas',
        help_text='Servicio del evento al que pertenece esta tarea, cuando aplique.',
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
    hora_inicio = models.TimeField(blank=True, null=True)
    fecha_limite = models.DateField(blank=True, null=True)
    hora_fin = models.TimeField(blank=True, null=True)
    prioridad = models.CharField(max_length=20, choices=PRIORIDADES, default='MEDIA')
    estado = models.CharField(max_length=20, choices=ESTADOS, default='PENDIENTE')
    porcentaje_avance = models.PositiveIntegerField(default=0)
    categoria = models.CharField(max_length=20, choices=CATEGORIAS, default='GENERAL')
    evidencia = models.FileField(upload_to='tareas/evidencias/', validators=[validar_documento], blank=True, null=True)
    notas = models.TextField(blank=True, null=True)
    cancelado_en = models.DateTimeField(blank=True, null=True)
    cancelado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='tareas_evento_canceladas',
    )
    motivo_cancelacion = models.TextField(blank=True, null=True)
    archivado_en = models.DateTimeField(blank=True, null=True)
    archivado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='tareas_evento_archivadas',
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['evento', 'fecha_limite', 'prioridad', 'titulo']
        verbose_name = 'Tarea del evento'
        verbose_name_plural = 'Tareas del evento'

    def __str__(self):
        return self.titulo

    @property
    def fecha_hora_inicio(self):
        fecha = self.fecha_inicio or self.fecha_limite
        if not fecha:
            return None
        hora = self.hora_inicio
        if not hora:
            return None
        valor = datetime.combine(fecha, hora)
        return timezone.make_aware(
            valor,
            timezone.get_current_timezone(),
        )

    @property
    def fecha_hora_fin(self):
        fecha = self.fecha_limite or self.fecha_inicio
        if not fecha or not self.hora_fin:
            return None
        valor = datetime.combine(fecha, self.hora_fin)
        return timezone.make_aware(
            valor,
            timezone.get_current_timezone(),
        )

    @property
    def es_cita_agenda(self):
        # Retirado en K.8.7.1.2: las citas viven exclusivamente en ActividadItinerario.
        return False

    @property
    def esta_vencida(self):
        if self.estado in {
            'COMPLETADA',
            'CANCELADA',
        }:
            return False

        if not self.fecha_limite:
            return False

        return self.fecha_limite < timezone.localdate()

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
                raise ValidationError({'servicio_evento': 'El servicio debe pertenecer al mismo evento que la tarea.'})

    def save(self, *args, **kwargs):
        if self.estado == 'COMPLETADA':
            self.porcentaje_avance = 100
        if self.porcentaje_avance > 100:
            self.porcentaje_avance = 100
        super().save(*args, **kwargs)

# Create your models here.
