from dataclasses import dataclass, field

from django.core.exceptions import ObjectDoesNotExist, PermissionDenied, ValidationError
from django.db import transaction

from core.services.auditoria import registrar_auditoria
from core.services.permisos import roles_usuario_empresa, usuario_es_dirtec_operativo
from tareas.models import TareaEvento


KANBAN_STATES = {"PENDIENTE", "EN_PROCESO", "EN_REVISION", "COMPLETADA"}


@dataclass(frozen=True)
class EvaluacionEliminacionTarea:
    permitido: bool
    motivos: tuple[str, ...] = field(default_factory=tuple)


def usuario_puede_purgar_tarea(user, tarea):
    if usuario_es_dirtec_operativo(user):
        return True
    return "ADMIN_EMPRESA" in roles_usuario_empresa(user, tarea.evento.empresa)


def _reverse_history(tarea):
    motivos = []
    for relation in tarea._meta.related_objects:
        accessor = relation.get_accessor_name()
        if not accessor:
            continue
        try:
            related = getattr(tarea, accessor)
        except ObjectDoesNotExist:
            continue
        try:
            exists = related.exists()
        except AttributeError:
            exists = related is not None
        if exists:
            motivos.append(f"Tiene {relation.related_model._meta.verbose_name_plural} relacionados.")
    return motivos


def evaluar_eliminacion_tarea(tarea, *, para_purga=False):
    motivos = []

    if tarea.evidencia:
        motivos.append("Tiene evidencia adjunta.")

    if not para_purga:
        if tarea.estado != "PENDIENTE":
            motivos.append("La tarea ya avanzó de estado.")
        if tarea.porcentaje_avance:
            motivos.append("La tarea ya tiene avance registrado.")
        if tarea.servicio_evento_id:
            motivos.append("La tarea está vinculada a un servicio.")
        if tarea.cancelado_en or tarea.archivado_en:
            motivos.append("La tarea ya tiene historial de ciclo de vida.")

    motivos.extend(_reverse_history(tarea))
    return EvaluacionEliminacionTarea(
        permitido=not motivos,
        motivos=tuple(dict.fromkeys(motivos)),
    )


@transaction.atomic
def guardar_tarea(tarea, *, evento, cleaned_data, user=None, request=None):
    nueva = tarea.pk is None
    anteriores = {}

    if not nueva:
        locked = TareaEvento.objects.select_for_update().get(pk=tarea.pk)
        anteriores = {
            "estado": locked.estado,
            "prioridad": locked.prioridad,
            "responsable_id": locked.responsable_id,
            "fecha_limite": str(locked.fecha_limite or ""),
            "avance": locked.porcentaje_avance,
        }

    tarea.evento = evento
    for field_name, value in cleaned_data.items():
        setattr(tarea, field_name, value)

    tarea.full_clean()
    tarea.save()

    registrar_auditoria(
        usuario=user,
        empresa=evento.empresa,
        evento=evento,
        accion="CREAR_TAREA_K9" if nueva else "EDITAR_TAREA_K9",
        modelo="TareaEvento",
        objeto_id=tarea.id,
        descripcion=("Se creó" if nueva else "Se actualizó") + f" tarea: {tarea.titulo}.",
        valores_anteriores=anteriores,
        valores_nuevos={
            "estado": tarea.estado,
            "prioridad": tarea.prioridad,
            "responsable_id": tarea.responsable_id,
            "fecha_limite": str(tarea.fecha_limite or ""),
            "avance": tarea.porcentaje_avance,
        },
        request=request,
    )
    return tarea


@transaction.atomic
def mover_tarea_kanban(tarea, *, estado, user=None, request=None):
    if estado not in KANBAN_STATES:
        raise ValidationError("Estado de tablero no permitido.")
    tarea = TareaEvento.objects.select_for_update().get(pk=tarea.pk)
    if tarea.archivado_en:
        raise ValidationError("Una tarea archivada no puede moverse.")
    if tarea.estado == "CANCELADA":
        raise ValidationError("Una tarea cancelada no puede moverse.")

    anterior = tarea.estado
    tarea.estado = estado
    if estado == "COMPLETADA":
        tarea.porcentaje_avance = 100
    elif estado == "PENDIENTE" and tarea.porcentaje_avance == 100:
        tarea.porcentaje_avance = 0
    tarea.save(update_fields=["estado", "porcentaje_avance", "fecha_actualizacion"])

    registrar_auditoria(
        usuario=user,
        empresa=tarea.evento.empresa,
        evento=tarea.evento,
        accion="MOVER_TAREA_KANBAN_K9",
        modelo="TareaEvento",
        objeto_id=tarea.id,
        descripcion=f"Tarea movida de {anterior} a {estado}: {tarea.titulo}.",
        valores_anteriores={"estado": anterior},
        valores_nuevos={"estado": estado, "avance": tarea.porcentaje_avance},
        request=request,
    )
    return tarea


@transaction.atomic
def eliminar_tarea_error(tarea, *, user=None, request=None):
    evaluacion = evaluar_eliminacion_tarea(tarea)
    if not evaluacion.permitido:
        raise ValidationError(["La tarea ya tiene historial y no puede borrarse como error.", *evaluacion.motivos])

    evento = tarea.evento
    tarea_id = tarea.id
    titulo = tarea.titulo
    registrar_auditoria(
        usuario=user,
        empresa=evento.empresa,
        evento=evento,
        accion="ELIMINAR_TAREA_ERROR_K9",
        modelo="TareaEvento",
        objeto_id=tarea_id,
        descripcion=f"Se eliminó tarea creada por error: {titulo}.",
        valores_anteriores={"titulo": titulo, "estado": tarea.estado},
        request=request,
    )
    tarea.delete()
    return {"id": tarea_id, "titulo": titulo}


@transaction.atomic
def purgar_tarea_archivada(tarea, *, user=None, request=None):
    if not usuario_puede_purgar_tarea(user, tarea):
        raise PermissionDenied("Solo DIRTEC o Admin Empresa puede purgar tareas archivadas.")
    if not tarea.archivado_en:
        raise ValidationError("La tarea debe estar archivada antes de purgarla.")

    evaluacion = evaluar_eliminacion_tarea(tarea, para_purga=True)
    if not evaluacion.permitido:
        raise ValidationError(["La tarea archivada conserva historial protegido.", *evaluacion.motivos])

    evento = tarea.evento
    tarea_id = tarea.id
    titulo = tarea.titulo
    registrar_auditoria(
        usuario=user,
        empresa=evento.empresa,
        evento=evento,
        accion="PURGAR_TAREA_K9",
        modelo="TareaEvento",
        objeto_id=tarea_id,
        descripcion=f"Se purgó tarea archivada: {titulo}.",
        valores_anteriores={"titulo": titulo, "estado": tarea.estado, "archivada": True},
        request=request,
    )
    tarea.delete()
    return {"id": tarea_id, "titulo": titulo}
