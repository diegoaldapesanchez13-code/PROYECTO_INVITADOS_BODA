from django.db import transaction

from core.services.auditoria import registrar_auditoria
from invitaciones.rsvp_models import RsvpConfiguracionEvento, RsvpExcepcionGrupo


@transaction.atomic
def guardar_configuracion_rsvp(evento, *, cleaned_data, user=None, request=None):
    config, _created = RsvpConfiguracionEvento.objects.select_for_update().get_or_create(
        evento=evento,
    )
    before = {
        "estado": config.estado,
        "fecha_limite": str(config.fecha_limite or ""),
        "recordatorio_desde": str(config.recordatorio_desde or ""),
        "mostrar_recordatorio": config.mostrar_recordatorio,
    }

    for field, value in cleaned_data.items():
        setattr(config, field, value)
    config.actualizado_por = user
    config.full_clean()
    config.save()

    registrar_auditoria(
        usuario=user,
        empresa=evento.empresa,
        evento=evento,
        accion="CONFIGURAR_RSVP_EVENTO_K9",
        modelo="RsvpConfiguracionEvento",
        objeto_id=config.id,
        descripcion=f"Se actualizó control RSVP del evento: {evento}.",
        valores_anteriores=before,
        valores_nuevos={
            "estado": config.estado,
            "fecha_limite": str(config.fecha_limite or ""),
            "recordatorio_desde": str(config.recordatorio_desde or ""),
            "mostrar_recordatorio": config.mostrar_recordatorio,
        },
        request=request,
    )
    return config


@transaction.atomic
def guardar_excepcion_rsvp(grupo, *, cleaned_data, user=None, request=None):
    exception, _created = RsvpExcepcionGrupo.objects.select_for_update().get_or_create(
        grupo=grupo,
    )
    before = {
        "modo": exception.modo,
        "motivo": exception.motivo,
    }

    exception.modo = cleaned_data["modo"]
    exception.motivo = cleaned_data.get("motivo") or ""
    exception.actualizado_por = user
    exception.full_clean()
    exception.save()

    registrar_auditoria(
        usuario=user,
        empresa=grupo.evento.empresa,
        evento=grupo.evento,
        accion="CONFIGURAR_EXCEPCION_RSVP_K9",
        modelo="RsvpExcepcionGrupo",
        objeto_id=exception.id,
        descripcion=(
            f"RSVP de {grupo.nombre_grupo}: {exception.get_modo_display()}."
        ),
        valores_anteriores=before,
        valores_nuevos={
            "modo": exception.modo,
            "motivo": exception.motivo,
        },
        request=request,
    )
    return exception
