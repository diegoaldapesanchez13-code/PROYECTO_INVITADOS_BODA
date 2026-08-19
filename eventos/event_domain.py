from dataclasses import dataclass, field

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone

from core.services.auditoria import registrar_auditoria
from core.services.authorization import Actions, usuario_puede_evento, usuario_tiene_permiso
from core.services.permisos import roles_usuario_empresa, usuario_es_dirtec_operativo
from invitaciones.models import EventoBoda
from organizaciones.models import MembresiaEmpresa


@dataclass(frozen=True)
class EvaluacionEliminacionEvento:
    permitido: bool
    motivos: tuple[str, ...] = field(default_factory=tuple)

    def as_dict(self):
        return {
            "permitido": self.permitido,
            "motivos": list(self.motivos),
        }


def _nombre_limpio(value):
    return " ".join(str(value or "").split()).strip()


def _planner_valido(empresa, planner):
    if planner is None:
        return None
    if not MembresiaEmpresa.objects.filter(
        empresa=empresa,
        usuario=planner,
        rol="WEDDING_PLANNER",
        activo=True,
    ).exists():
        raise ValidationError("El planner seleccionado no pertenece de forma activa a la empresa.")
    return planner


def _cliente_valido(empresa, cliente):
    if cliente is None:
        return None
    if not MembresiaEmpresa.objects.filter(
        empresa=empresa,
        usuario=cliente,
        rol="CLIENTE",
        activo=True,
    ).exists():
        raise ValidationError("El cliente seleccionado no pertenece de forma activa a la empresa.")
    return cliente


@transaction.atomic
def crear_evento_generico(
    *,
    empresa,
    usuario,
    nombre_evento,
    tipo_evento="OTRO",
    fecha_inicio=None,
    fecha_fin=None,
    planner=None,
    cliente=None,
    sede=None,
    request=None,
):
    if not usuario_tiene_permiso(usuario, Actions.EVENT_CREATE, empresa=empresa):
        raise PermissionDenied("No tienes permiso para crear eventos en esta empresa.")

    nombre = _nombre_limpio(nombre_evento)
    if not nombre:
        raise ValidationError({"nombre_evento": "El nombre del evento es obligatorio."})

    tipos_validos = {value for value, _label in EventoBoda.TIPOS_EVENTO}
    tipo = tipo_evento if tipo_evento in tipos_validos else "OTRO"

    planner = _planner_valido(empresa, planner)
    cliente = _cliente_valido(empresa, cliente)

    if sede is not None and getattr(sede, "empresa_id", None) != empresa.id:
        raise ValidationError("La sede seleccionada no pertenece a la empresa.")

    evento = EventoBoda.objects.create(
        empresa=empresa,
        sede=sede,
        nombre_evento=nombre,
        tipo_evento=tipo,
        estado="BORRADOR",
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        # Compatibilidad temporal: consumidores K8/K9 que aun leen fecha_fiesta
        # reciben la fecha principal cuando esta ya fue definida.
        fecha_fiesta=fecha_inicio,
        wedding_planner=planner,
        activo=True,
    )
    if cliente is not None:
        evento.clientes.add(cliente)

    registrar_auditoria(
        usuario=usuario,
        empresa=empresa,
        evento=evento,
        accion="CREAR_EVENTO_K9",
        modelo="EventoBoda",
        objeto_id=evento.id,
        descripcion=f"Se creo el evento {evento.titulo_evento}.",
        valores_nuevos={
            "nombre_evento": evento.nombre_evento,
            "tipo_evento": evento.tipo_evento,
            "estado": evento.estado,
        },
        request=request,
    )
    return evento


@transaction.atomic
def actualizar_datos_evento_generico(
    evento,
    *,
    usuario,
    nombre_evento=None,
    tipo_evento=None,
    fecha_inicio=None,
    fecha_fin=None,
    sede_marker=False,
    sede=None,
    planner_marker=False,
    planner=None,
    request=None,
):
    if not usuario_puede_evento(usuario, evento, Actions.EVENT_EDIT):
        raise PermissionDenied("No tienes permiso para editar este evento.")

    anterior = {
        "nombre_evento": evento.nombre_evento,
        "tipo_evento": evento.tipo_evento,
        "fecha_inicio": evento.fecha_inicio.isoformat() if evento.fecha_inicio else None,
        "fecha_fin": evento.fecha_fin.isoformat() if evento.fecha_fin else None,
        "sede_id": evento.sede_id,
        "planner_id": evento.wedding_planner_id,
    }

    if nombre_evento is not None:
        nombre = _nombre_limpio(nombre_evento)
        if not nombre:
            raise ValidationError({"nombre_evento": "El nombre del evento es obligatorio."})
        evento.nombre_evento = nombre

    if tipo_evento is not None:
        tipos_validos = {value for value, _label in EventoBoda.TIPOS_EVENTO}
        if tipo_evento not in tipos_validos:
            raise ValidationError({"tipo_evento": "Tipo de evento no valido."})
        evento.tipo_evento = tipo_evento

    evento.fecha_inicio = fecha_inicio
    evento.fecha_fin = fecha_fin
    if fecha_inicio is not None:
        evento.fecha_fiesta = fecha_inicio

    if sede_marker:
        if sede is not None and getattr(sede, "empresa_id", None) != evento.empresa_id:
            raise ValidationError("La sede seleccionada no pertenece a la empresa.")
        evento.sede = sede

    if planner_marker:
        evento.wedding_planner = _planner_valido(evento.empresa, planner)

    if evento.estado == "BORRADOR" and (
        evento.fecha_inicio or evento.sede_id or evento.wedding_planner_id
    ):
        evento.estado = "ACTIVO"

    evento.save()

    registrar_auditoria(
        usuario=usuario,
        empresa=evento.empresa,
        evento=evento,
        accion="EDITAR_EVENTO_K9",
        modelo="EventoBoda",
        objeto_id=evento.id,
        descripcion=f"Se actualizaron los datos del evento {evento.titulo_evento}.",
        valores_anteriores=anterior,
        valores_nuevos={
            "nombre_evento": evento.nombre_evento,
            "tipo_evento": evento.tipo_evento,
            "fecha_inicio": evento.fecha_inicio.isoformat() if evento.fecha_inicio else None,
            "fecha_fin": evento.fecha_fin.isoformat() if evento.fecha_fin else None,
            "sede_id": evento.sede_id,
            "planner_id": evento.wedding_planner_id,
            "estado": evento.estado,
        },
        request=request,
    )
    return evento


def evaluar_eliminacion_evento(evento):
    """
    Error-delete evaluation for R2.

    Participant mirrors, memberships, basic customer/planner assignment and
    audit rows are structural and do not block deleting a freshly-created
    erroneous event. Real commercial/operational history does.
    """
    checks = [
        ("Tiene una propuesta comercial.", evento.propuestas_k9.exists()),
        ("Tiene un contrato.", evento.contratos_evento.exists()),
        ("Tiene servicios operativos.", evento.servicios_contratados.exists()),
        ("Tiene gastos.", evento.gastos_evento.exists()),
        ("Tiene pagos de cliente.", evento.pagos_cliente_reportados.exists()),
        ("Tiene documentos.", evento.documentos_evento.exists()),
        ("Tiene tareas.", evento.tareas_evento.exists()),
        ("Tiene actividades de agenda.", evento.actividades_itinerario.exists()),
        ("Tiene grupos de invitados.", evento.grupos.exists()),
        ("Tiene paquetes legacy asociados.", evento.paquetes_evento.exists()),
        ("Tiene expedientes de colaboracion.", evento.expedientes_servicio.exists()),
    ]
    motivos = tuple(label for label, exists in checks if exists)
    return EvaluacionEliminacionEvento(permitido=not motivos, motivos=motivos)


@transaction.atomic
def eliminar_evento_error(evento, *, usuario, request=None):
    if not usuario_puede_evento(usuario, evento, Actions.EVENT_EDIT):
        raise PermissionDenied("No tienes permiso para eliminar este evento.")

    evaluacion = evaluar_eliminacion_evento(evento)
    if not evaluacion.permitido:
        raise ValidationError(
            ["El evento no puede eliminarse porque ya tiene historial relevante.", *evaluacion.motivos]
        )

    empresa = evento.empresa
    evento_id = evento.id
    nombre = evento.titulo_evento

    # La auditoria se registra antes del hard-delete y queda viva porque su FK
    # usa SET_NULL.
    registrar_auditoria(
        usuario=usuario,
        empresa=empresa,
        evento=evento,
        accion="ELIMINAR_EVENTO_ERROR_K9",
        modelo="EventoBoda",
        objeto_id=evento_id,
        descripcion=f"Se elimino el evento creado por error: {nombre}.",
        valores_anteriores={
            "nombre_evento": evento.nombre_evento,
            "tipo_evento": evento.tipo_evento,
            "estado": evento.estado,
        },
        request=request,
    )
    evento.delete()
    return {"evento_id": evento_id, "nombre": nombre}


@transaction.atomic
def cancelar_evento(evento, *, usuario, motivo="", request=None):
    if not usuario_puede_evento(usuario, evento, Actions.EVENT_EDIT):
        raise PermissionDenied("No tienes permiso para cancelar este evento.")
    if evento.estado == "ARCHIVADO":
        raise ValidationError("Restaura el evento antes de cancelarlo.")

    anterior = evento.estado
    evento.estado = "CANCELADO"
    evento.cancelado_en = timezone.now()
    evento.cancelado_por = usuario
    evento.motivo_cancelacion = _nombre_limpio(motivo)
    evento.activo = False
    evento.save(
        update_fields=[
            "estado",
            "cancelado_en",
            "cancelado_por",
            "motivo_cancelacion",
            "activo",
            "fecha_actualizacion",
        ]
    )

    registrar_auditoria(
        usuario=usuario,
        empresa=evento.empresa,
        evento=evento,
        accion="CANCELAR_EVENTO_K9",
        modelo="EventoBoda",
        objeto_id=evento.id,
        descripcion=f"Se cancelo el evento {evento.titulo_evento}.",
        valores_anteriores={"estado": anterior},
        valores_nuevos={"estado": evento.estado, "motivo": evento.motivo_cancelacion},
        request=request,
    )
    return evento


@transaction.atomic
def archivar_evento(evento, *, usuario, request=None):
    if not usuario_puede_evento(usuario, evento, Actions.EVENT_EDIT):
        raise PermissionDenied("No tienes permiso para archivar este evento.")
    if evento.estado == "ARCHIVADO":
        return evento

    anterior = evento.estado
    evento.estado_previo_archivado = anterior
    evento.estado = "ARCHIVADO"
    evento.archivado_en = timezone.now()
    evento.archivado_por = usuario
    evento.activo = False
    evento.save(
        update_fields=[
            "estado_previo_archivado",
            "estado",
            "archivado_en",
            "archivado_por",
            "activo",
            "fecha_actualizacion",
        ]
    )

    registrar_auditoria(
        usuario=usuario,
        empresa=evento.empresa,
        evento=evento,
        accion="ARCHIVAR_EVENTO_K9",
        modelo="EventoBoda",
        objeto_id=evento.id,
        descripcion=f"Se archivo el evento {evento.titulo_evento}.",
        valores_anteriores={"estado": anterior},
        valores_nuevos={"estado": "ARCHIVADO"},
        request=request,
    )
    return evento


@transaction.atomic
def restaurar_evento(evento, *, usuario, request=None):
    if not usuario_puede_evento(usuario, evento, Actions.EVENT_EDIT):
        raise PermissionDenied("No tienes permiso para restaurar este evento.")
    if evento.estado != "ARCHIVADO":
        return evento

    estado_restaurado = evento.estado_previo_archivado or "ACTIVO"
    estados_validos = {value for value, _label in EventoBoda.ESTADOS_EVENTO}
    if estado_restaurado not in estados_validos or estado_restaurado == "ARCHIVADO":
        estado_restaurado = "ACTIVO"

    evento.estado = estado_restaurado
    evento.estado_previo_archivado = ""
    evento.archivado_en = None
    evento.archivado_por = None
    evento.activo = estado_restaurado not in {"CANCELADO", "FINALIZADO"}
    evento.save(
        update_fields=[
            "estado",
            "estado_previo_archivado",
            "archivado_en",
            "archivado_por",
            "activo",
            "fecha_actualizacion",
        ]
    )

    registrar_auditoria(
        usuario=usuario,
        empresa=evento.empresa,
        evento=evento,
        accion="RESTAURAR_EVENTO_K9",
        modelo="EventoBoda",
        objeto_id=evento.id,
        descripcion=f"Se restauro el evento {evento.titulo_evento}.",
        valores_anteriores={"estado": "ARCHIVADO"},
        valores_nuevos={"estado": evento.estado},
        request=request,
    )
    return evento


def usuario_puede_purgar_evento(usuario, evento):
    if usuario_es_dirtec_operativo(usuario):
        return True
    roles = roles_usuario_empresa(usuario, evento.empresa)
    return "ADMIN_EMPRESA" in roles
