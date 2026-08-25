from django.conf import settings
from django.db import models


class RsvpConfiguracionEvento(models.Model):
    ESTADOS = [
        ("ABIERTO", "Abierto"),
        ("CERRADO", "Cerrado"),
    ]

    evento = models.OneToOneField(
        "invitaciones.EventoBoda",
        on_delete=models.CASCADE,
        related_name="rsvp_configuracion",
    )
    estado = models.CharField(
        max_length=12,
        choices=ESTADOS,
        default="ABIERTO",
    )
    fecha_limite = models.DateTimeField(blank=True, null=True)
    recordatorio_desde = models.DateTimeField(blank=True, null=True)
    mostrar_recordatorio = models.BooleanField(default=True)

    mensaje_abierto = models.CharField(
        max_length=220,
        blank=True,
        default="Confirma tu asistencia antes de la fecha indicada.",
    )
    mensaje_recordatorio = models.CharField(
        max_length=220,
        blank=True,
        default="La fecha límite para confirmar está próxima.",
    )
    mensaje_cerrado = models.CharField(
        max_length=220,
        blank=True,
        default=(
            "El periodo de confirmación ha finalizado. "
            "Si necesitas hacer un cambio, comunícate con los anfitriones."
        ),
    )

    actualizado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="rsvp_eventos_actualizados",
    )
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = "invitaciones"
        verbose_name = "Configuración RSVP del evento"
        verbose_name_plural = "Configuraciones RSVP del evento"

    def __str__(self):
        return f"RSVP - {self.evento}"


class RsvpExcepcionGrupo(models.Model):
    MODOS = [
        ("HEREDA", "Hereda del evento"),
        ("HABILITADA", "Habilitada manualmente"),
        ("BLOQUEADA", "Bloqueada"),
    ]

    grupo = models.OneToOneField(
        "invitaciones.Grupoinvitacion",
        on_delete=models.CASCADE,
        related_name="rsvp_excepcion",
    )
    modo = models.CharField(
        max_length=14,
        choices=MODOS,
        default="HEREDA",
    )
    motivo = models.CharField(max_length=220, blank=True, default="")
    actualizado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="rsvp_grupos_actualizados",
    )
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = "invitaciones"
        verbose_name = "Excepción RSVP de invitación"
        verbose_name_plural = "Excepciones RSVP de invitación"

    def __str__(self):
        return f"{self.grupo} - {self.get_modo_display()}"
