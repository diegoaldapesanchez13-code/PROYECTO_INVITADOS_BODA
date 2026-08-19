from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from core.services.auditoria import registrar_auditoria
from eventos.models import ContratoEvento
from eventos.services import generar_contrato_v2_desde_propuesta
from paquetes.models import PropuestaEvento, PropuestaLinea
from paquetes.services import actualizar_totales_propuesta


EDITABLE_PROPOSAL_STATES = {"BORRADOR", "PROPUESTA", "EN_REVISION", "ACEPTADO", "CANCELADO"}


def propuesta_es_editable(propuesta):
    if propuesta is None:
        return True
    if propuesta.estado == "CONTRATADO":
        return False
    return not ContratoEvento.objects.filter(propuesta_origen=propuesta).exists()


def eliminar_propuesta_error(propuesta, *, user=None, request=None):
    """
    Hard-delete only a draft proposal that never became contract truth.
    """
    if propuesta.estado != "BORRADOR":
        raise ValidationError("Solo una propuesta en borrador puede eliminarse como error.")
    if ContratoEvento.objects.filter(propuesta_origen=propuesta).exists():
        raise ValidationError("La propuesta ya tiene contrato y no puede eliminarse.")

    evento = propuesta.evento
    empresa = propuesta.empresa
    propuesta_id = propuesta.id

    registrar_auditoria(
        usuario=user,
        empresa=empresa,
        evento=evento,
        accion="ELIMINAR_PROPUESTA_ERROR_K9",
        modelo="PropuestaEvento",
        objeto_id=propuesta_id,
        descripcion=f"Se elimino la propuesta borrador {propuesta_id} creada por error.",
        valores_anteriores={
            "estado": propuesta.estado,
            "total": str(propuesta.total),
        },
        request=request,
    )
    propuesta.delete()
    return propuesta_id


@transaction.atomic
def crear_revision_desde_contrato(contrato, *, user=None, request=None):
    """
    Contract changes are modeled as a new proposal revision.

    The original contract snapshot remains frozen. A future accepted revision
    generates the next ContratoEvento.version.
    """
    if contrato.estado not in {"CONTRATADO", "FIRMADO"}:
        raise ValidationError("Solo un contrato vigente puede iniciar una revision.")
    origen = contrato.propuesta_origen
    if origen is None:
        raise ValidationError("Este contrato legacy no tiene propuesta K9 para revisar.")

    nueva = PropuestaEvento.objects.create(
        empresa=origen.empresa,
        evento=origen.evento,
        sede=origen.sede,
        paquete=origen.paquete,
        adultos=origen.adultos,
        ninos=origen.ninos,
        descuento=origen.descuento,
        estado="EN_REVISION",
        notas_comerciales=origen.notas_comerciales,
        created_by=user,
        updated_by=user,
    )

    for linea in origen.lineas.filter(activo=True).order_by("orden", "id"):
        PropuestaLinea.objects.create(
            propuesta=nueva,
            tipo=linea.tipo,
            servicio_catalogo=linea.servicio_catalogo,
            nombre=linea.nombre,
            descripcion=linea.descripcion,
            modo_precio=linea.modo_precio,
            tarifa=linea.tarifa,
            cantidad=linea.cantidad,
            valor_informativo=linea.valor_informativo,
            orden=linea.orden,
            activo=True,
        )

    actualizar_totales_propuesta(nueva, user=user)

    registrar_auditoria(
        usuario=user,
        empresa=nueva.empresa,
        evento=nueva.evento,
        accion="CREAR_REVISION_CONTRACTUAL_K9",
        modelo="PropuestaEvento",
        objeto_id=nueva.id,
        descripcion=f"Se creo revision comercial desde contrato v{contrato.version}.",
        valores_anteriores={"contrato_id": contrato.id, "contrato_version": contrato.version},
        valores_nuevos={"propuesta_id": nueva.id, "estado": nueva.estado},
        request=request,
    )
    return nueva


@transaction.atomic
def generar_version_contractual(propuesta, *, user=None, request=None):
    """
    Generate a frozen contract and supersede the previous current version.

    Idempotency is preserved by generar_contrato_v2_desde_propuesta().
    """
    contrato = generar_contrato_v2_desde_propuesta(propuesta.id, user=user)

    anteriores = (
        ContratoEvento.objects.select_for_update()
        .filter(evento=propuesta.evento, estado="CONTRATADO")
        .exclude(pk=contrato.pk)
    )
    reemplazados = list(anteriores.values_list("id", "version"))
    anteriores.update(estado="REEMPLAZADO")

    registrar_auditoria(
        usuario=user,
        empresa=propuesta.empresa,
        evento=propuesta.evento,
        accion="GENERAR_CONTRATO_K9",
        modelo="ContratoEvento",
        objeto_id=contrato.id,
        descripcion=f"Se genero contrato comercial v{contrato.version}.",
        valores_anteriores={"reemplazados": reemplazados},
        valores_nuevos={
            "contrato_id": contrato.id,
            "version": contrato.version,
            "estado": contrato.estado,
        },
        request=request,
    )
    return contrato


@transaction.atomic
def cancelar_contrato(contrato, *, motivo="", user=None, request=None):
    if contrato.estado in {"CANCELADO", "REEMPLAZADO"}:
        return contrato

    anterior = contrato.estado
    motivo = (motivo or "").strip()
    nota = contrato.notas or ""
    marca = f"[Cancelado {timezone.localdate().isoformat()}]"
    if user is not None:
        marca += f" por {getattr(user, 'username', user)}"
    if motivo:
        marca += f": {motivo}"
    contrato.notas = (nota + "\n" + marca).strip()
    contrato.estado = "CANCELADO"
    contrato.save(update_fields=["estado", "notas", "fecha_actualizacion"])

    registrar_auditoria(
        usuario=user,
        empresa=contrato.evento.empresa,
        evento=contrato.evento,
        accion="CANCELAR_CONTRATO_K9",
        modelo="ContratoEvento",
        objeto_id=contrato.id,
        descripcion=f"Se cancelo contrato v{contrato.version}.",
        valores_anteriores={"estado": anterior},
        valores_nuevos={"estado": "CANCELADO", "motivo": motivo},
        request=request,
    )
    return contrato
