from dataclasses import dataclass

from django.utils import timezone

from .rsvp_models import RsvpConfiguracionEvento, RsvpExcepcionGrupo


@dataclass(frozen=True)
class RsvpDecision:
    permitido: bool
    phase: str
    title: str
    message: str
    deadline: object = None
    reminder_from: object = None
    exception_mode: str = "HEREDA"

    def as_dict(self):
        return {
            "allowed": self.permitido,
            "phase": self.phase,
            "title": self.title,
            "message": self.message,
            "deadline": self.deadline.isoformat() if self.deadline else None,
            "deadlineLabel": (
                timezone.localtime(self.deadline).strftime("%d/%m/%Y %H:%M")
                if self.deadline
                else ""
            ),
            "reminderFrom": (
                self.reminder_from.isoformat()
                if self.reminder_from
                else None
            ),
            "exceptionMode": self.exception_mode,
        }


def obtener_configuracion_rsvp(evento):
    config = RsvpConfiguracionEvento.objects.filter(evento=evento).first()
    if config is None:
        return None
    return config


def obtener_excepcion_rsvp(grupo):
    return RsvpExcepcionGrupo.objects.filter(grupo=grupo).first()


def evaluar_rsvp(grupo, *, ahora=None):
    ahora = ahora or timezone.now()
    config = obtener_configuracion_rsvp(grupo.evento)
    excepcion = obtener_excepcion_rsvp(grupo)
    modo = excepcion.modo if excepcion else "HEREDA"

    if modo == "BLOQUEADA":
        return RsvpDecision(
            permitido=False,
            phase="BLOCKED",
            title="Confirmación bloqueada",
            message=(
                excepcion.motivo
                or "Esta invitación no permite cambios de confirmación por el momento."
            ),
            deadline=config.fecha_limite if config else None,
            reminder_from=config.recordatorio_desde if config else None,
            exception_mode=modo,
        )

    # An explicit planner/company exception can reopen one invitation even when
    # the event is globally closed or its deadline already passed.
    if modo == "HABILITADA":
        return RsvpDecision(
            permitido=True,
            phase="EXCEPTION_OPEN",
            title="Confirmación habilitada",
            message=(
                excepcion.motivo
                or (
                    config.mensaje_abierto
                    if config
                    else "Puedes actualizar tu confirmación."
                )
            ),
            deadline=config.fecha_limite if config else None,
            reminder_from=config.recordatorio_desde if config else None,
            exception_mode=modo,
        )

    # Backward-compatible default: if no RSVP configuration exists yet, RSVP
    # remains open exactly as it behaved before R4F-B.
    if config is None:
        return RsvpDecision(
            permitido=True,
            phase="OPEN",
            title="Confirmación abierta",
            message="Puedes confirmar tu asistencia.",
            exception_mode=modo,
        )

    if config.estado == "CERRADO":
        return RsvpDecision(
            permitido=False,
            phase="CLOSED",
            title="Confirmaciones cerradas",
            message=config.mensaje_cerrado,
            deadline=config.fecha_limite,
            reminder_from=config.recordatorio_desde,
            exception_mode=modo,
        )

    if config.fecha_limite and ahora > config.fecha_limite:
        return RsvpDecision(
            permitido=False,
            phase="DEADLINE_CLOSED",
            title="Periodo de confirmación finalizado",
            message=config.mensaje_cerrado,
            deadline=config.fecha_limite,
            reminder_from=config.recordatorio_desde,
            exception_mode=modo,
        )

    reminder_active = bool(
        config.mostrar_recordatorio
        and config.recordatorio_desde
        and ahora >= config.recordatorio_desde
        and (
            config.fecha_limite is None
            or ahora <= config.fecha_limite
        )
    )
    if reminder_active:
        return RsvpDecision(
            permitido=True,
            phase="REMINDER",
            title="Recuerda confirmar tu asistencia",
            message=config.mensaje_recordatorio,
            deadline=config.fecha_limite,
            reminder_from=config.recordatorio_desde,
            exception_mode=modo,
        )

    return RsvpDecision(
        permitido=True,
        phase="OPEN",
        title="Confirmación abierta",
        message=config.mensaje_abierto,
        deadline=config.fecha_limite,
        reminder_from=config.recordatorio_desde,
        exception_mode=modo,
    )
