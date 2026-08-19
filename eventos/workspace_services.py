from dataclasses import dataclass, field
from decimal import Decimal

from django.core.exceptions import ObjectDoesNotExist, PermissionDenied, ValidationError
from django.db import transaction

from core.services.auditoria import registrar_auditoria
from core.services.permisos import roles_usuario_empresa, usuario_es_dirtec_operativo
from proveedores.models import ServicioEvento


ZERO = Decimal("0.00")


@dataclass(frozen=True)
class EvaluacionEliminacionServicio:
    permitido: bool
    motivos: tuple[str, ...] = field(default_factory=tuple)

    def as_dict(self):
        return {"permitido": self.permitido, "motivos": list(self.motivos)}


def _reverse_history_reasons(servicio):
    reasons = []
    for relation in servicio._meta.related_objects:
        accessor = relation.get_accessor_name()
        if not accessor:
            continue
        try:
            related = getattr(servicio, accessor)
        except ObjectDoesNotExist:
            continue

        try:
            exists = related.exists()
        except AttributeError:
            exists = related is not None

        if exists:
            label = relation.related_model._meta.verbose_name_plural
            reasons.append(f"Tiene {label} relacionados.")
    return reasons


def evaluar_eliminacion_servicio(servicio, *, para_purga=False):
    motivos = []

    if servicio.contrato_origen_id:
        motivos.append("Proviene de un contrato materializado.")
    if servicio.paquete_evento_id or servicio.servicio_paquete_origen_id:
        motivos.append("Proviene de un paquete materializado.")

    if servicio.contrato or servicio.cotizacion or servicio.comprobante_pago:
        motivos.append("Tiene archivos comerciales u operativos.")

    if any(
        value not in {None, ZERO}
        for value in (
            servicio.costo_total,
            servicio.costo_proveedor,
            servicio.precio_cliente,
            servicio.ajuste_cliente,
            servicio.valor_contratado,
            servicio.cargo_adicional_cliente,
            servicio.anticipo,
        )
    ):
        motivos.append("Tiene valores financieros registrados.")

    if not para_purga:
        if servicio.origen != "MANUAL":
            motivos.append("No es un servicio creado manualmente.")
        if servicio.estado != "SOLICITADO":
            motivos.append("Ya avanzó en su ciclo legacy.")
        if servicio.estado_comercial != "BORRADOR":
            motivos.append("Ya avanzó comercialmente.")
        if servicio.estado_operativo != "PENDIENTE":
            motivos.append("Ya avanzó operativamente.")
        if servicio.cancelado_en or servicio.archivado_en:
            motivos.append("Ya tiene historial de ciclo de vida.")

    motivos.extend(_reverse_history_reasons(servicio))
    return EvaluacionEliminacionServicio(
        permitido=not motivos,
        motivos=tuple(dict.fromkeys(motivos)),
    )


def usuario_puede_purgar_servicio(user, servicio):
    if usuario_es_dirtec_operativo(user):
        return True
    roles = roles_usuario_empresa(user, servicio.evento.empresa)
    return "ADMIN_EMPRESA" in roles


@transaction.atomic
def guardar_servicio_operativo(
    servicio,
    *,
    evento,
    cleaned_data,
    user=None,
    request=None,
):
    nuevo = servicio.pk is None

    anterior = {}
    if not nuevo:
        locked = ServicioEvento.objects.select_for_update().get(pk=servicio.pk)
        anterior = {
            "proveedor_id": locked.proveedor_id,
            "prestacion_tipo": locked.prestacion_tipo,
            "estado_operativo": locked.estado_operativo,
            "fecha_servicio": str(locked.fecha_servicio or ""),
            "costo_proveedor": str(locked.costo_proveedor),
        }

    servicio.evento = evento

    for field, value in cleaned_data.items():
        setattr(servicio, field, value)

    if nuevo:
        servicio.origen = "CATALOGO" if servicio.servicio_catalogo_k9_id else "MANUAL"
        servicio.modalidad = "ADICIONAL"
        servicio.estado = "SOLICITADO"
        servicio.estado_comercial = "BORRADOR"
        servicio.cargo_adicional_cliente = ZERO
        servicio.valor_contratado = ZERO

    if servicio.servicio_catalogo_k9_id:
        if not servicio.nombre_servicio:
            servicio.nombre_servicio = servicio.servicio_catalogo_k9.nombre
        if not servicio.categoria:
            servicio.categoria = servicio.servicio_catalogo_k9.categoria
        if not servicio.catalogo_nombre_snapshot:
            servicio.catalogo_nombre_snapshot = servicio.servicio_catalogo_k9.nombre
            servicio.catalogo_descripcion_snapshot = servicio.servicio_catalogo_k9.descripcion

    if nuevo and servicio.proveedor_id and not servicio.proveedor_nombre_snapshot:
        servicio.proveedor_nombre_snapshot = servicio.proveedor.nombre_comercial

    servicio.full_clean()
    servicio.save()

    registrar_auditoria(
        usuario=user,
        empresa=evento.empresa,
        evento=evento,
        accion="CREAR_SERVICIO_OPERATIVO_K9" if nuevo else "EDITAR_SERVICIO_OPERATIVO_K9",
        modelo="ServicioEvento",
        objeto_id=servicio.id,
        descripcion=(
            f"Se creó servicio operativo: {servicio.nombre_servicio}."
            if nuevo
            else f"Se actualizó servicio operativo: {servicio.nombre_servicio}."
        ),
        valores_anteriores=anterior,
        valores_nuevos={
            "proveedor_id": servicio.proveedor_id,
            "prestacion_tipo": servicio.prestacion_tipo,
            "estado_operativo": servicio.estado_operativo,
            "fecha_servicio": str(servicio.fecha_servicio or ""),
            "costo_proveedor": str(servicio.costo_proveedor),
        },
        request=request,
    )
    return servicio


@transaction.atomic
def eliminar_servicio_error(servicio, *, user=None, request=None):
    evaluacion = evaluar_eliminacion_servicio(servicio)
    if not evaluacion.permitido:
        raise ValidationError(
            ["El servicio ya tiene historial y no puede borrarse como error.", *evaluacion.motivos]
        )

    evento = servicio.evento
    servicio_id = servicio.id
    nombre = servicio.nombre_servicio

    registrar_auditoria(
        usuario=user,
        empresa=evento.empresa,
        evento=evento,
        accion="ELIMINAR_SERVICIO_ERROR_K9",
        modelo="ServicioEvento",
        objeto_id=servicio_id,
        descripcion=f"Se eliminó servicio creado por error: {nombre}.",
        valores_anteriores={
            "nombre": nombre,
            "origen": servicio.origen,
            "estado_operativo": servicio.estado_operativo,
        },
        request=request,
    )
    servicio.delete()
    return {"id": servicio_id, "nombre": nombre}


@transaction.atomic
def purgar_servicio_archivado(servicio, *, user=None, request=None):
    if not usuario_puede_purgar_servicio(user, servicio):
        raise PermissionDenied("Solo DIRTEC o Admin Empresa puede purgar servicios archivados.")
    if not servicio.archivado_en:
        raise ValidationError("El servicio debe estar archivado antes de purgarlo.")

    evaluacion = evaluar_eliminacion_servicio(servicio, para_purga=True)
    if not evaluacion.permitido:
        raise ValidationError(
            ["El servicio archivado todavía tiene historial protegido.", *evaluacion.motivos]
        )

    evento = servicio.evento
    servicio_id = servicio.id
    nombre = servicio.nombre_servicio

    registrar_auditoria(
        usuario=user,
        empresa=evento.empresa,
        evento=evento,
        accion="PURGAR_SERVICIO_K9",
        modelo="ServicioEvento",
        objeto_id=servicio_id,
        descripcion=f"Se purgó servicio archivado sin historial protegido: {nombre}.",
        valores_anteriores={
            "nombre": nombre,
            "archivado": True,
        },
        request=request,
    )
    servicio.delete()
    return {"id": servicio_id, "nombre": nombre}
