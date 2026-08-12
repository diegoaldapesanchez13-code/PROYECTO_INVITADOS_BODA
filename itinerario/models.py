from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.utils import timezone


class ActividadItinerario(models.Model):
    TIPOS = [
        ('CITA', 'Cita'),
        ('ACTIVIDAD', 'Actividad operativa'),
        ('HITO', 'Hito del evento'),
    ]
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
    servicio_evento = models.ForeignKey(
        'proveedores.ServicioEvento',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='actividades_agenda',
        help_text='Servicio del evento relacionado con esta actividad, cuando aplique.',
    )
    tipo = models.CharField(max_length=15, choices=TIPOS, default='ACTIVIDAD')
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
        verbose_name = 'Actividad de agenda'
        verbose_name_plural = 'Actividades de agenda'

    def __str__(self):
        return f'{self.hora_inicio:%H:%M} - {self.titulo}'

    @property
    def requiere_confirmacion(self):
        return self.tipo == 'CITA'

    @property
    def confirmaciones_pendientes(self):
        if not self.requiere_confirmacion:
            return 0
        return self.participantes.filter(requerido=True, estado='PENDIENTE').count()

    @property
    def confirmada_completa(self):
        if not self.requiere_confirmacion:
            return self.estado == 'CONFIRMADA'
        return not self.participantes.filter(
            requerido=True,
        ).exclude(estado='CONFIRMADO').exists()

    def clean(self):
        super().clean()
        if self.hora_fin and self.hora_fin <= self.hora_inicio:
            raise ValidationError({'hora_fin': 'La hora de fin debe ser posterior a la hora de inicio.'})
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
                raise ValidationError({'servicio_evento': 'El servicio debe pertenecer al mismo evento que la actividad.'})


class ParticipanteActividad(models.Model):
    ROLES = [
        ('CLIENTE', 'Cliente'),
        ('PLANNER', 'Planner'),
        ('COLABORADOR', 'Colaborador'),
        ('PROVEEDOR', 'Proveedor'),
        ('OTRO', 'Otro'),
    ]
    ESTADOS = [
        ('PENDIENTE', 'Pendiente de confirmar'),
        ('CONFIRMADO', 'Confirmado'),
        ('NO_ASISTE', 'No asistirá'),
        ('REPROGRAMAR', 'Solicita reprogramar'),
        ('NO_REQUIERE', 'No requiere confirmación'),
    ]

    actividad = models.ForeignKey(
        ActividadItinerario,
        on_delete=models.CASCADE,
        related_name='participantes',
    )
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name='participaciones_agenda',
    )
    proveedor = models.ForeignKey(
        'proveedores.Proveedor',
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name='participaciones_agenda',
    )
    rol = models.CharField(max_length=20, choices=ROLES)
    nombre_snapshot = models.CharField(max_length=180, blank=True, null=True)
    requerido = models.BooleanField(default=True)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='PENDIENTE')
    comentario = models.TextField(blank=True, null=True)
    respondido_en = models.DateTimeField(blank=True, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['actividad', 'rol', 'id']
        constraints = [
            models.UniqueConstraint(
                fields=['actividad', 'usuario'],
                condition=Q(usuario__isnull=False),
                name='itin_part_act_usuario_unico',
            ),
            models.UniqueConstraint(
                fields=['actividad', 'proveedor'],
                condition=Q(proveedor__isnull=False),
                name='itin_part_act_prov_unico',
            ),
        ]
        indexes = [
            models.Index(fields=['actividad', 'estado'], name='itin_part_act_est_idx'),
            models.Index(fields=['usuario', 'estado'], name='itin_part_usr_est_idx'),
            models.Index(fields=['proveedor', 'estado'], name='itin_part_prov_est_idx'),
        ]
        verbose_name = 'Participante de agenda'
        verbose_name_plural = 'Participantes de agenda'

    def __str__(self):
        return f'{self.nombre_visible} · {self.get_estado_display()}'

    @property
    def nombre_visible(self):
        if self.usuario_id:
            nombre = self.usuario.get_full_name().strip()
            return nombre or self.usuario.username
        if self.proveedor_id:
            return self.proveedor.nombre_comercial
        return self.nombre_snapshot or self.get_rol_display()

    def clean(self):
        super().clean()
        if not (self.usuario_id or self.proveedor_id or self.nombre_snapshot):
            raise ValidationError('El participante necesita usuario, proveedor o nombre.')
        if self.usuario_id and self.proveedor_id:
            raise ValidationError('Un participante no puede ser usuario y proveedor al mismo tiempo.')
        if self.actividad_id and self.actividad.tipo != 'CITA' and self.requerido:
            raise ValidationError({'requerido': 'Solo las citas requieren confirmación individual.'})

    def registrar_respuesta(self, estado, comentario=None):
        if estado not in dict(self.ESTADOS):
            raise ValidationError({'estado': 'Estado de confirmación inválido.'})
        self.estado = estado
        self.comentario = (comentario or '').strip() or None
        self.respondido_en = timezone.now()
        self.save(update_fields=['estado', 'comentario', 'respondido_en'])
