from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from core.services.auditoria import registrar_auditoria
from eventos.models import ContratoEvento
from eventos.services import generar_contrato_v2_desde_propuesta
from eventos.selectors import (
    CONTRATO_ESTADOS_VIGENTES,
    contrato_es_vigente,
)
from paquetes.models import PropuestaEvento, PropuestaLinea
from paquetes.services import (
    PROPUESTA_ESTADOS_NEGOCIABLES,
    PROPUESTA_SNAPSHOT_ACEPTACION_VERSION,
    actualizar_totales_propuesta,
    construir_snapshot_aceptacion,
)


EDITABLE_PROPOSAL_STATES = PROPUESTA_ESTADOS_NEGOCIABLES


def propuesta_es_editable(propuesta):
    if propuesta is None:
        return True
    if propuesta.estado not in EDITABLE_PROPOSAL_STATES:
        return False
    return not ContratoEvento.objects.filter(propuesta_origen=propuesta).exists()


def propuesta_permite_editar_lineas(propuesta):
    """Extras/courtesies freeze once the proposal reaches ACEPTADO."""
    if propuesta is None:
        return False
    if propuesta.estado not in EDITABLE_PROPOSAL_STATES:
        return False
    return not ContratoEvento.objects.filter(propuesta_origen=propuesta).exists()


@transaction.atomic
def aceptar_propuesta(propuesta, *, user=None, request=None):
    propuesta = (
        PropuestaEvento.objects.select_for_update()
        .select_related("empresa", "evento", "sede", "paquete")
        .prefetch_related(
            "lineas__servicio_catalogo",
            "paquete__servicios_catalogo_k9__servicio_catalogo",
        )
        .get(pk=propuesta.pk)
    )
    if propuesta.estado not in EDITABLE_PROPOSAL_STATES:
        raise ValidationError("Solo una propuesta en negociacion puede aceptarse.")
    if ContratoEvento.objects.filter(propuesta_origen=propuesta).exists():
        raise ValidationError("La propuesta ya tiene contrato y no puede aceptarse de nuevo.")

    anterior = {
        "estado": propuesta.estado,
        "total": str(propuesta.total),
        "snapshot_aceptacion_version": propuesta.snapshot_aceptacion_version,
    }
    dto = actualizar_totales_propuesta(propuesta, user=user)
    propuesta.refresh_from_db()

    aceptado_en = timezone.now()
    snapshot = construir_snapshot_aceptacion(
        propuesta,
        dto,
        user=user,
        fecha=aceptado_en,
    )
    propuesta.estado = "ACEPTADO"
    propuesta.aceptado_en = aceptado_en
    propuesta.aceptado_por = user if getattr(user, "is_authenticated", False) else None
    propuesta.snapshot_aceptacion = snapshot
    propuesta.snapshot_aceptacion_version = PROPUESTA_SNAPSHOT_ACEPTACION_VERSION
    if user is not None:
        propuesta.updated_by = user
    propuesta.save(
        update_fields=[
            "estado",
            "aceptado_en",
            "aceptado_por",
            "snapshot_aceptacion",
            "snapshot_aceptacion_version",
            "updated_by",
            "updated_at",
        ]
    )

    registrar_auditoria(
        usuario=user,
        empresa=propuesta.empresa,
        evento=propuesta.evento,
        accion="ACEPTAR_PROPUESTA_K9_D1",
        modelo="PropuestaEvento",
        objeto_id=propuesta.id,
        descripcion=f"Se acepto propuesta comercial #{propuesta.id}.",
        valores_anteriores=anterior,
        valores_nuevos={
            "estado": propuesta.estado,
            "aceptado_en": propuesta.aceptado_en.isoformat(),
            "snapshot_aceptacion_version": propuesta.snapshot_aceptacion_version,
            "total": snapshot["totales"]["total_final"],
        },
        request=request,
    )
    return propuesta


@transaction.atomic
def reabrir_propuesta(propuesta, *, user=None, request=None):
    propuesta = (
        PropuestaEvento.objects.select_for_update()
        .select_related("empresa", "evento")
        .get(pk=propuesta.pk)
    )
    if propuesta.estado != "ACEPTADO":
        raise ValidationError("Solo una propuesta aceptada puede reabrirse.")
    if ContratoEvento.objects.filter(propuesta_origen=propuesta).exists():
        raise ValidationError("La propuesta ya tiene contrato; crea una revision contractual.")

    anterior = {
        "estado": propuesta.estado,
        "aceptado_en": propuesta.aceptado_en.isoformat() if propuesta.aceptado_en else None,
        "aceptado_por_id": propuesta.aceptado_por_id,
        "snapshot_aceptacion_version": propuesta.snapshot_aceptacion_version,
        "snapshot_aceptacion": propuesta.snapshot_aceptacion,
    }
    propuesta.estado = "EN_REVISION"
    propuesta.aceptado_en = None
    propuesta.aceptado_por = None
    propuesta.snapshot_aceptacion = {}
    propuesta.snapshot_aceptacion_version = 0
    if user is not None:
        propuesta.updated_by = user
    propuesta.save(
        update_fields=[
            "estado",
            "aceptado_en",
            "aceptado_por",
            "snapshot_aceptacion",
            "snapshot_aceptacion_version",
            "updated_by",
            "updated_at",
        ]
    )

    registrar_auditoria(
        usuario=user,
        empresa=propuesta.empresa,
        evento=propuesta.evento,
        accion="REABRIR_PROPUESTA_K9_D1",
        modelo="PropuestaEvento",
        objeto_id=propuesta.id,
        descripcion=f"Se reabrio negociacion de propuesta #{propuesta.id}.",
        valores_anteriores=anterior,
        valores_nuevos={"estado": propuesta.estado, "snapshot_aceptacion_version": 0},
        request=request,
    )
    return propuesta


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
    if contrato.estado not in CONTRATO_ESTADOS_VIGENTES or not contrato_es_vigente(contrato):
        raise ValidationError("Solo el contrato vigente puede iniciar una revision.")
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
        lineage = (linea.snapshot_linea or {}).get("operational_lineage_key")
        if not lineage:
            lineage = f"{linea.tipo}:proposal-line:{linea.id}"
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
            snapshot_linea={"operational_lineage_key": lineage},
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

    reemplazados = list(
        ContratoEvento.objects.filter(
            evento=propuesta.evento,
            estado="REEMPLAZADO",
        )
        .exclude(pk=contrato.pk)
        .values_list("id", "version")
    )

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
    if contrato.estado not in CONTRATO_ESTADOS_VIGENTES:
        raise ValidationError("Solo un contrato vigente puede cancelarse.")
    if not contrato_es_vigente(contrato):
        raise ValidationError("No puedes cancelar una version contractual que ya no es vigente.")

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
