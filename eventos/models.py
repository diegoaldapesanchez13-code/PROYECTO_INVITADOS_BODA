from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from invitaciones.models import validar_documento


class ParticipanteEvento(models.Model):
    ROLES = [
        ('CLIENTE', 'Cliente'),
        ('PLANNER', 'Wedding planner'),
        ('COLABORADOR', 'Colaborador'),
    ]

    evento = models.ForeignKey(
        'invitaciones.EventoBoda',
        on_delete=models.CASCADE,
        related_name='participantes_evento',
    )
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='participaciones_evento',
    )
    rol = models.CharField(max_length=20, choices=ROLES)
    activo = models.BooleanField(default=True)
    es_contacto_principal = models.BooleanField(default=False)
    puede_ver_finanzas = models.BooleanField(default=False)
    puede_aprobar = models.BooleanField(default=False)
    puede_gestionar_invitados = models.BooleanField(default=False)
    puede_gestionar_servicios = models.BooleanField(default=False)
    notas = models.TextField(blank=True, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['evento', 'rol', 'usuario__username']
        constraints = [
            models.UniqueConstraint(
                fields=['evento', 'usuario', 'rol'],
                name='eventos_participante_evento_usuario_rol_unico',
            ),
        ]
        indexes = [
            models.Index(fields=['evento', 'rol', 'activo'], name='evt_part_evt_rol_act_idx'),
            models.Index(fields=['usuario', 'activo'], name='evt_part_usr_act_idx'),
        ]
        verbose_name = 'Participante del evento'
        verbose_name_plural = 'Participantes del evento'

    def __str__(self):
        return f'{self.usuario} - {self.evento} ({self.get_rol_display()})'

    def clean(self):
        super().clean()
        if not self.evento_id or not self.usuario_id:
            return
        empresa_id = getattr(self.evento, 'empresa_id', None)
        if not empresa_id:
            return
        if self.rol in {'PLANNER', 'COLABORADOR'}:
            membresia_valida = self.usuario.membresias_empresa.filter(
                empresa_id=empresa_id,
                activo=True,
            ).exists()
            if not membresia_valida:
                raise ValidationError(
                    {'usuario': 'El planner o colaborador debe tener membresia activa en la empresa del evento.'}
                )


class ContratoEvento(models.Model):
    ESTADOS = [
        ('BORRADOR', 'Borrador'),
        ('EN_REVISION', 'En revision'),
        ('FIRMADO', 'Firmado'),
        ('CONTRATADO', 'Contratado'),
        ('CANCELADO', 'Cancelado'),
        ('REEMPLAZADO', 'Reemplazado'),
    ]

    evento = models.ForeignKey(
        'invitaciones.EventoBoda',
        on_delete=models.CASCADE,
        related_name='contratos_evento',
    )
    numero_contrato = models.CharField(max_length=80, blank=True, null=True)
    version = models.PositiveIntegerField(default=1)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='BORRADOR')
    monto_base = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    moneda = models.CharField(max_length=3, default='MXN')
    fecha_emision = models.DateField(blank=True, null=True)
    fecha_firma = models.DateField(blank=True, null=True)
    archivo = models.FileField(
        upload_to='eventos/contratos/',
        validators=[validar_documento],
        blank=True,
        null=True,
    )
    snapshot_comercial = models.JSONField(default=dict, blank=True)
    snapshot_version = models.PositiveIntegerField(default=1)
    materializado_en = models.DateTimeField(blank=True, null=True)
    materializacion_version = models.PositiveIntegerField(default=0)
    propuesta_origen = models.ForeignKey(
        'paquetes.PropuestaEvento',
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        related_name='contratos_v2',
    )
    notas = models.TextField(blank=True, null=True)
    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='contratos_evento_creados',
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['evento', '-version', '-id']
        constraints = [
            models.UniqueConstraint(
                fields=['evento', 'version'],
                name='eventos_contrato_evento_version_unica',
            ),
            models.UniqueConstraint(
                fields=['propuesta_origen'],
                name='eventos_contrato_propuesta_origen_unica',
            ),
        ]
        indexes = [
            models.Index(fields=['evento', 'estado'], name='evt_contrato_evt_est_idx'),
            models.Index(fields=['snapshot_version'], name='evt_contrato_snap_ver_idx'),
            models.Index(fields=['materializacion_version'], name='evt_contrato_mat_ver_idx'),
        ]
        verbose_name = 'Contrato del evento'
        verbose_name_plural = 'Contratos del evento'

    def __str__(self):
        return f'{self.evento} - contrato v{self.version}'
