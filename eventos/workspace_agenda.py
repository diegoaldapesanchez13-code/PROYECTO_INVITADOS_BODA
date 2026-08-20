from dataclasses import dataclass, field

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction

from core.services.auditoria import registrar_auditoria
from core.services.permisos import roles_usuario_empresa, usuario_es_dirtec_operativo
from itinerario.models import ActividadItinerario, ParticipanteActividad
from itinerario.services import asegurar_participantes_cita


@dataclass(frozen=True)
class EvaluacionEliminacionActividad:
    permitido: bool
    motivos: tuple[str, ...] = field(default_factory=tuple)


def usuario_puede_purgar_actividad(user, actividad):
    if usuario_es_dirtec_operativo(user):
        return True
    return "ADMIN_EMPRESA" in roles_usuario_empresa(user, actividad.evento.empresa)


def evaluar_eliminacion_actividad(actividad, *, para_purga=False):
    motivos = []

    participantes = actividad.participantes.all()
    if participantes.filter(respondido_en__isnull=False).exists():
        motivos.append("Tiene respuestas de participantes.")
    if participantes.exclude(comentario__isnull=True).exclude(comentario="").exists():
        motivos.append("Tiene comentarios de participantes.")

    if not para_purga:
        if actividad.estado != "PENDIENTE":
            motivos.append("La actividad ya avanzó de estado.")
        if actividad.servicio_evento_id:
            motivos.append("Está vinculada a un servicio.")
        if actividad.cancelado_en or actividad.archivado_en:
            motivos.append("Ya tiene historial de ciclo de vida.")

    return EvaluacionEliminacionActividad(
        permitido=not motivos,
        motivos=tuple(dict.fromkeys(motivos)),
    )


@transaction.atomic
def guardar_actividad(actividad, *, evento, cleaned_data, user=None, request=None):
    nueva = actividad.pk is None
    anterior_tipo = None
    anteriores = {}

    if not nueva:
        locked = ActividadItinerario.objects.select_for_update().get(pk=actividad.pk)
        anterior_tipo = locked.tipo
        anteriores = {
            "tipo": locked.tipo,
            "estado": locked.estado,
            "fecha": str(locked.fecha),
            "hora_inicio": str(locked.hora_inicio),
            "responsable_id": locked.responsable_id,
            "proveedor_id": locked.proveedor_id,
        }

    actividad.evento = evento
    for field_name, value in cleaned_data.items():
        setattr(actividad, field_name, value)

    actividad.full_clean()
    actividad.save()

    if actividad.tipo == "CITA":
        asegurar_participantes_cita(actividad, creador=user)
    elif anterior_tipo == "CITA":
        actividad.participantes.filter(
            respondido_en__isnull=True,
            estado="PENDIENTE",
        ).update(requerido=False, estado="NO_REQUIERE")
        actividad.participantes.filter(
            respondido_en__isnull=True,
            estado="CONFIRMADO",
        ).update(requerido=False)

    registrar_auditoria(
        usuario=user,
        empresa=evento.empresa,
        evento=evento,
        accion="CREAR_ACTIVIDAD_AGENDA_K9" if nueva else "EDITAR_ACTIVIDAD_AGENDA_K9",
        modelo="ActividadItinerario",
        objeto_id=actividad.id,
        descripcion=("Se creó" if nueva else "Se actualizó") + f" agenda: {actividad.titulo}.",
        valores_anteriores=anteriores,
        valores_nuevos={
            "tipo": actividad.tipo,
            "estado": actividad.estado,
            "fecha": str(actividad.fecha),
            "hora_inicio": str(actividad.hora_inicio),
            "responsable_id": actividad.responsable_id,
            "proveedor_id": actividad.proveedor_id,
        },
        request=request,
    )
    return actividad


@transaction.atomic
def completar_actividad(actividad, *, user=None, request=None):
    actividad = ActividadItinerario.objects.select_for_update().get(pk=actividad.pk)
    if actividad.archivado_en:
        raise ValidationError("Una actividad archivada no puede completarse.")
    if actividad.estado == "CANCELADA":
        raise ValidationError("Una actividad cancelada no puede completarse.")

    anterior = actividad.estado
    actividad.estado = "COMPLETADA"
    actividad.save(update_fields=["estado"])

    registrar_auditoria(
        usuario=user,
        empresa=actividad.evento.empresa,
        evento=actividad.evento,
        accion="COMPLETAR_ACTIVIDAD_AGENDA_K9",
        modelo="ActividadItinerario",
        objeto_id=actividad.id,
        descripcion=f"Actividad completada: {actividad.titulo}.",
        valores_anteriores={"estado": anterior},
        valores_nuevos={"estado": "COMPLETADA"},
        request=request,
    )
    return actividad


@transaction.atomic
def eliminar_actividad_error(actividad, *, user=None, request=None):
    evaluacion = evaluar_eliminacion_actividad(actividad)
    if not evaluacion.permitido:
        raise ValidationError(
            ["La actividad ya tiene historial y no puede borrarse como error.", *evaluacion.motivos]
        )

    evento = actividad.evento
    actividad_id = actividad.id
    titulo = actividad.titulo
    registrar_auditoria(
        usuario=user,
        empresa=evento.empresa,
        evento=evento,
        accion="ELIMINAR_ACTIVIDAD_ERROR_K9",
        modelo="ActividadItinerario",
        objeto_id=actividad_id,
        descripcion=f"Se eliminó actividad creada por error: {titulo}.",
        valores_anteriores={
            "titulo": titulo,
            "tipo": actividad.tipo,
            "estado": actividad.estado,
            "fecha": str(actividad.fecha),
        },
        request=request,
    )
    actividad.delete()
    return {"id": actividad_id, "titulo": titulo}


@transaction.atomic
def purgar_actividad_archivada(actividad, *, user=None, request=None):
    if not usuario_puede_purgar_actividad(user, actividad):
        raise PermissionDenied("Solo DIRTEC o Admin Empresa puede purgar actividades archivadas.")
    if not actividad.archivado_en:
        raise ValidationError("La actividad debe estar archivada antes de purgarla.")

    evaluacion = evaluar_eliminacion_actividad(actividad, para_purga=True)
    if not evaluacion.permitido:
        raise ValidationError(
            ["La actividad archivada conserva historial protegido.", *evaluacion.motivos]
        )

    evento = actividad.evento
    actividad_id = actividad.id
    titulo = actividad.titulo
    registrar_auditoria(
        usuario=user,
        empresa=evento.empresa,
        evento=evento,
        accion="PURGAR_ACTIVIDAD_AGENDA_K9",
        modelo="ActividadItinerario",
        objeto_id=actividad_id,
        descripcion=f"Se purgó actividad archivada: {titulo}.",
        valores_anteriores={"titulo": titulo, "archivada": True},
        request=request,
    )
    actividad.delete()
    return {"id": actividad_id, "titulo": titulo}
