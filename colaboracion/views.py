from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.views.decorators.http import require_POST

from invitaciones.models import EventoBoda
from proveedores.models import Proveedor, ServicioEvento

from .models import (
    CotizacionProveedor,
    ExpedienteServicio,
    MensajeExpediente,
    PartidaPresupuestoCliente,
    PropuestaCliente,
)
from .services import (
    cliente_puede_evento,
    cliente_puede_expediente,
    notificar_clientes,
    notificar_planner,
    notificar_proveedor,
    planner_puede_expediente,
    proveedor_puede_expediente,
    registrar_mensaje_sistema,
    siguiente_version,
)


def _redirect_cliente(expediente):
    return redirect(
        f"/cliente/dashboard/?evento={expediente.evento_id}#colaboracion"
    )


def _redirect_planner(expediente):
    return redirect(
        "/dashboard/planner/#colaboracion"
    )


def _redirect_proveedor(expediente):
    return redirect(
        f"/proveedor/dashboard/?evento={expediente.evento_id}#colaboracion"
    )


def _decimal_post(request, name, default="0"):
    raw = (request.POST.get(name) or default).strip()
    try:
        return Decimal(raw)
    except (InvalidOperation, ValueError):
        return None


@login_required
@require_POST
def cliente_crear_solicitud(request):
    evento_id = request.POST.get(
        "evento_id"
    )
    evento = (
        EventoBoda.objects
        .select_related(
            "empresa",
            "wedding_planner",
        )
        .filter(id=evento_id)
        .first()
    )

    if not cliente_puede_evento(
        request.user,
        evento,
    ):
        messages.error(
            request,
            (
                "La sesion actual no corresponde al cliente "
                "que abrio este evento. Si estas probando varios "
                "roles, usa perfiles de navegador separados."
            ),
        )
        return redirect("redirigir_por_rol")

    titulo = (
        request.POST.get("titulo")
        or ""
    ).strip()
    descripcion = (
        request.POST.get("descripcion")
        or ""
    ).strip()
    categoria = request.POST.get("categoria")

    categorias = {
        value
        for value, _
        in ExpedienteServicio.CATEGORIAS
    }
    if not titulo:
        messages.error(
            request,
            "Escribe un titulo para la solicitud.",
        )
        return redirect(
            f"/cliente/dashboard/?evento={evento.id}#colaboracion"
        )

    if categoria not in categorias:
        categoria = "OTRO"

    expediente = ExpedienteServicio.objects.create(
        evento=evento,
        titulo=titulo,
        descripcion=descripcion or None,
        categoria=categoria,
        creado_por=request.user,
        cliente_solicitante=request.user,
    )

    if descripcion:
        MensajeExpediente.objects.create(
            expediente=expediente,
            canal="CLIENTE_PLANNER",
            autor=request.user,
            mensaje=descripcion,
        )

    registrar_mensaje_sistema(
        expediente,
        "CLIENTE_PLANNER",
        "Solicitud creada. El planner revisara el requerimiento.",
    )
    notificar_planner(
        expediente,
        "Nueva solicitud del cliente",
        (
            f"{request.user.get_full_name() or request.user.username}: "
            f"{expediente.titulo}"
        ),
    )
    messages.success(
        request,
        "Solicitud enviada al planner.",
    )
    return _redirect_cliente(expediente)


@login_required
@require_POST
def enviar_mensaje(request, expediente_id):
    expediente = get_object_or_404(
        ExpedienteServicio.objects.select_related(
            "evento",
            "proveedor",
        ),
        id=expediente_id,
    )
    canal = request.POST.get("canal")
    texto = (
        request.POST.get("mensaje")
        or ""
    ).strip()
    archivo = request.FILES.get("archivo")

    if canal not in {
        "CLIENTE_PLANNER",
        "PLANNER_PROVEEDOR",
    }:
        raise PermissionDenied(
            "Canal no valido."
        )

    es_planner = planner_puede_expediente(
        request.user,
        expediente,
    )
    es_cliente = cliente_puede_expediente(
        request.user,
        expediente,
    )
    es_proveedor = proveedor_puede_expediente(
        request.user,
        expediente,
    )

    autorizado = (
        es_planner
        or (
            canal == "CLIENTE_PLANNER"
            and es_cliente
        )
        or (
            canal == "PLANNER_PROVEEDOR"
            and es_proveedor
        )
    )
    if not autorizado:
        raise PermissionDenied(
            "No tienes acceso a esta conversacion."
        )

    if not texto and not archivo:
        messages.error(
            request,
            "Escribe un mensaje o adjunta un archivo.",
        )
    else:
        MensajeExpediente.objects.create(
            expediente=expediente,
            canal=canal,
            autor=request.user,
            mensaje=texto,
            archivo=archivo,
        )

        resumen = (
            texto[:180]
            if texto
            else "Nuevo archivo adjunto."
        )
        if canal == "CLIENTE_PLANNER":
            if es_planner:
                notificar_clientes(
                    expediente,
                    "Nuevo mensaje de tu planner",
                    resumen,
                )
            else:
                notificar_planner(
                    expediente,
                    "Nuevo mensaje del cliente",
                    resumen,
                )
        elif canal == "PLANNER_PROVEEDOR":
            if es_planner:
                notificar_proveedor(
                    expediente,
                    "Nuevo mensaje del planner",
                    resumen,
                )
            else:
                notificar_planner(
                    expediente,
                    "Nuevo mensaje del proveedor",
                    resumen,
                )

    if es_planner:
        return _redirect_planner(expediente)
    if es_proveedor:
        return _redirect_proveedor(expediente)
    return _redirect_cliente(expediente)


@login_required
@require_POST
@transaction.atomic
def planner_asignar_proveedor(request, expediente_id):
    expediente = get_object_or_404(
        ExpedienteServicio.objects.select_related(
            "evento",
            "servicio_evento",
        ),
        id=expediente_id,
    )
    if not planner_puede_expediente(
        request.user,
        expediente,
    ):
        raise PermissionDenied(
            "No puedes administrar este expediente."
        )

    proveedor = get_object_or_404(
        Proveedor,
        id=request.POST.get("proveedor_id"),
        empresa=expediente.evento.empresa,
        activo=True,
        visible_para_wedding_planners=True,
    )

    if (
        expediente.proveedor_id
        and expediente.proveedor_id
        != proveedor.id
    ):
        messages.error(
            request,
            (
                "Este expediente ya tiene proveedor y "
                "conversacion asociados. Para consultar otro "
                "proveedor crea un expediente separado y asi "
                "no se mezclan historiales ni cotizaciones."
            ),
        )
        return _redirect_planner(expediente)

    servicio = expediente.servicio_evento
    if not servicio:
        servicio = ServicioEvento.objects.create(
            evento=expediente.evento,
            proveedor=proveedor,
            nombre_servicio=expediente.titulo,
            descripcion=expediente.descripcion,
            estado="SOLICITADO",
        )
        expediente.servicio_evento = servicio
    else:
        servicio.proveedor = proveedor
        servicio.save(
            update_fields=[
                "proveedor",
                "fecha_actualizacion",
            ]
        )

    expediente.proveedor = proveedor
    expediente.estado = "CONSULTA_PROVEEDOR"
    expediente.save(
        update_fields=[
            "proveedor",
            "servicio_evento",
            "estado",
            "fecha_actualizacion",
        ]
    )

    registrar_mensaje_sistema(
        expediente,
        "PLANNER_PROVEEDOR",
        (
            "El planner asigno este requerimiento a "
            f"{proveedor.nombre_comercial}."
        ),
        autor=request.user,
    )
    registrar_mensaje_sistema(
        expediente,
        "CLIENTE_PLANNER",
        "El planner esta consultando opciones con proveedor.",
        autor=request.user,
    )

    notificar_proveedor(
        expediente,
        "Nueva solicitud de cotizacion",
        (
            f"{expediente.evento}: "
            f"{expediente.titulo}"
        ),
    )
    messages.success(
        request,
        "Proveedor asignado al expediente.",
    )
    return _redirect_planner(expediente)


@login_required
@require_POST
@transaction.atomic
def proveedor_cotizar(request, expediente_id):
    expediente = get_object_or_404(
        ExpedienteServicio.objects.select_related(
            "proveedor",
            "servicio_evento",
        ),
        id=expediente_id,
    )
    if not proveedor_puede_expediente(
        request.user,
        expediente,
    ):
        raise PermissionDenied(
            "No puedes cotizar este expediente."
        )

    costo = _decimal_post(
        request,
        "costo_proveedor",
    )
    if costo is None or costo < 0:
        messages.error(
            request,
            "Costo de cotizacion invalido.",
        )
        return _redirect_proveedor(expediente)

    cotizacion = CotizacionProveedor.objects.create(
        expediente=expediente,
        proveedor=expediente.proveedor,
        version=siguiente_version(
            CotizacionProveedor,
            expediente,
        ),
        costo_proveedor=costo,
        descripcion=(
            request.POST.get("descripcion")
            or ""
        ).strip() or None,
        vigencia=(
            request.POST.get("vigencia")
            or None
        ),
        archivo=request.FILES.get("archivo"),
        creado_por=request.user,
    )

    expediente.estado = "COTIZACION_RECIBIDA"
    expediente.save(
        update_fields=[
            "estado",
            "fecha_actualizacion",
        ]
    )
    if expediente.servicio_evento:
        expediente.servicio_evento.estado = "COTIZADO"
        expediente.servicio_evento.save(
            update_fields=[
                "estado",
                "fecha_actualizacion",
            ]
        )

    registrar_mensaje_sistema(
        expediente,
        "PLANNER_PROVEEDOR",
        f"Cotizacion v{cotizacion.version} enviada.",
        autor=request.user,
    )
    notificar_planner(
        expediente,
        "Cotizacion recibida",
        (
            f"{expediente.proveedor.nombre_comercial} "
            f"envio cotizacion v{cotizacion.version} "
            f"por ${cotizacion.costo_proveedor}."
        ),
    )
    messages.success(
        request,
        "Cotizacion enviada al planner.",
    )
    return _redirect_proveedor(expediente)


@login_required
@require_POST
@transaction.atomic
def planner_decidir_cotizacion(
    request,
    cotizacion_id,
):
    cotizacion = get_object_or_404(
        CotizacionProveedor.objects.select_related(
            "expediente__evento",
            "expediente__servicio_evento",
        ),
        id=cotizacion_id,
    )
    expediente = cotizacion.expediente

    if not planner_puede_expediente(
        request.user,
        expediente,
    ):
        raise PermissionDenied(
            "No puedes administrar esta cotizacion."
        )

    decision = request.POST.get("decision")
    comentario = (
        request.POST.get("comentario")
        or ""
    ).strip()

    if decision == "ACEPTAR":
        CotizacionProveedor.objects.filter(
            expediente=expediente,
            estado="ACEPTADA",
        ).exclude(id=cotizacion.id).update(
            estado="RECHAZADA"
        )
        cotizacion.estado = "ACEPTADA"
        expediente.estado = "COTIZACION_ACEPTADA"

        if expediente.servicio_evento:
            expediente.servicio_evento.costo_total = (
                cotizacion.costo_proveedor
            )
            expediente.servicio_evento.estado = (
                "PENDIENTE_APROBACION"
            )
            expediente.servicio_evento.save(
                update_fields=[
                    "costo_total",
                    "estado",
                    "fecha_actualizacion",
                ]
            )
        mensaje_estado = (
            f"Cotizacion v{cotizacion.version} aceptada por el planner."
        )

    elif decision == "CAMBIOS":
        cotizacion.estado = "CAMBIOS_SOLICITADOS"
        expediente.estado = "CONSULTA_PROVEEDOR"
        mensaje_estado = (
            f"Cambios solicitados a cotizacion v{cotizacion.version}."
        )
    elif decision == "RECHAZAR":
        cotizacion.estado = "RECHAZADA"
        expediente.estado = "CONSULTA_PROVEEDOR"
        mensaje_estado = (
            f"Cotizacion v{cotizacion.version} rechazada."
        )
    else:
        messages.error(
            request,
            "Decision invalida.",
        )
        return _redirect_planner(expediente)

    cotizacion.respuesta_planner = (
        comentario or None
    )
    cotizacion.save(
        update_fields=[
            "estado",
            "respuesta_planner",
            "fecha_actualizacion",
        ]
    )
    expediente.save(
        update_fields=[
            "estado",
            "fecha_actualizacion",
        ]
    )

    registrar_mensaje_sistema(
        expediente,
        "PLANNER_PROVEEDOR",
        (
            mensaje_estado
            + (
                f" Comentario: {comentario}"
                if comentario
                else ""
            )
        ),
        autor=request.user,
    )
    notificar_proveedor(
        expediente,
        "Respuesta a tu cotizacion",
        (
            mensaje_estado
            + (
                f" {comentario}"
                if comentario
                else ""
            )
        ),
    )

    return _redirect_planner(expediente)


@login_required
@require_POST
@transaction.atomic
def planner_enviar_propuesta(
    request,
    expediente_id,
):
    expediente = get_object_or_404(
        ExpedienteServicio.objects.select_related(
            "evento",
            "servicio_evento",
        ),
        id=expediente_id,
    )
    if not planner_puede_expediente(
        request.user,
        expediente,
    ):
        raise PermissionDenied(
            "No puedes crear esta propuesta."
        )

    modalidad = request.POST.get("modalidad")
    if modalidad not in {
        "ADICIONAL",
        "INCLUIDO_PAQUETE",
    }:
        messages.error(
            request,
            "Modalidad invalida.",
        )
        return _redirect_planner(expediente)

    cotizacion = (
        expediente.cotizaciones_proveedor
        .filter(estado="ACEPTADA")
        .order_by("-version")
        .first()
    )

    if modalidad == "ADICIONAL" and not cotizacion:
        messages.error(
            request,
            "Acepta primero una cotizacion del proveedor.",
        )
        return _redirect_planner(expediente)

    costo_base = (
        cotizacion.costo_proveedor
        if cotizacion
        else Decimal("0")
    )

    if modalidad == "INCLUIDO_PAQUETE":
        precio_cliente = Decimal("0")
        margen = Decimal("0")
    else:
        precio_cliente = _decimal_post(
            request,
            "precio_cliente",
        )
        if precio_cliente is None or precio_cliente < 0:
            messages.error(
                request,
                "Precio para cliente invalido.",
            )
            return _redirect_planner(expediente)
        margen = precio_cliente - costo_base

    PropuestaCliente.objects.filter(
        expediente=expediente,
        estado="ENVIADA",
    ).update(
        estado="REEMPLAZADA"
    )

    propuesta = PropuestaCliente.objects.create(
        expediente=expediente,
        cotizacion=cotizacion,
        version=siguiente_version(
            PropuestaCliente,
            expediente,
        ),
        modalidad=modalidad,
        descripcion=(
            request.POST.get("descripcion")
            or ""
        ).strip() or None,
        costo_base_snapshot=costo_base,
        margen=margen,
        precio_cliente=precio_cliente,
        referencia_paquete=(
            request.POST.get(
                "referencia_paquete"
            )
            or ""
        ).strip() or None,
        estado="ENVIADA",
        enviado_por=request.user,
        fecha_envio=timezone.now(),
    )

    expediente.estado = "PROPUESTA_CLIENTE"
    expediente.save(
        update_fields=[
            "estado",
            "fecha_actualizacion",
        ]
    )

    texto = (
        f"Propuesta v{propuesta.version} enviada al cliente"
        + (
            " como servicio incluido en paquete."
            if modalidad == "INCLUIDO_PAQUETE"
            else f" por ${propuesta.precio_cliente}."
        )
    )
    registrar_mensaje_sistema(
        expediente,
        "CLIENTE_PLANNER",
        texto,
        autor=request.user,
    )

    notificar_clientes(
        expediente,
        "Nueva propuesta para revisar",
        (
            f"{expediente.titulo}: "
            + (
                "incluido en tu paquete."
                if modalidad == "INCLUIDO_PAQUETE"
                else (
                    "propuesta por "
                    f"${propuesta.precio_cliente}."
                )
            )
        ),
    )
    messages.success(
        request,
        "Propuesta enviada al cliente.",
    )
    return _redirect_planner(expediente)


@login_required
@require_POST
@transaction.atomic
def cliente_responder_propuesta(
    request,
    propuesta_id,
):
    propuesta = get_object_or_404(
        PropuestaCliente.objects.select_related(
            "expediente__evento",
            "expediente__servicio_evento",
        ),
        id=propuesta_id,
    )
    expediente = propuesta.expediente

    if not cliente_puede_expediente(
        request.user,
        expediente,
    ):
        raise PermissionDenied(
            "No puedes responder esta propuesta."
        )
    if propuesta.estado != "ENVIADA":
        messages.error(
            request,
            "Esta propuesta ya no esta pendiente.",
        )
        return _redirect_cliente(expediente)

    accion = request.POST.get("accion")
    comentario = (
        request.POST.get("comentario")
        or ""
    ).strip()

    if accion == "APROBAR":
        propuesta.estado = "APROBADA"
        expediente.estado = "APROBADO_CLIENTE"

        PartidaPresupuestoCliente.objects.filter(
            expediente=expediente,
            estado="ACTIVA",
        ).update(
            estado="CANCELADA"
        )
        PartidaPresupuestoCliente.objects.create(
            evento=expediente.evento,
            expediente=expediente,
            propuesta=propuesta,
            concepto=expediente.titulo,
            monto_cliente=propuesta.precio_cliente,
            incluido_en_paquete=(
                propuesta.modalidad
                == "INCLUIDO_PAQUETE"
            ),
        )

        if expediente.servicio_evento:
            expediente.servicio_evento.estado = "APROBADO"
            expediente.servicio_evento.save(
                update_fields=[
                    "estado",
                    "fecha_actualizacion",
                ]
            )

        texto = "Cliente aprobo la propuesta."
    elif accion == "CAMBIOS":
        propuesta.estado = "CAMBIOS_SOLICITADOS"
        expediente.estado = "CAMBIOS_CLIENTE"
        texto = "Cliente solicito cambios a la propuesta."
    elif accion == "RECHAZAR":
        propuesta.estado = "RECHAZADA"
        expediente.estado = "EN_ANALISIS"
        texto = "Cliente rechazo la propuesta."
    else:
        messages.error(
            request,
            "Respuesta invalida.",
        )
        return _redirect_cliente(expediente)

    propuesta.respondido_por = request.user
    propuesta.comentario_cliente = (
        comentario or None
    )
    propuesta.fecha_respuesta = timezone.now()
    propuesta.save(
        update_fields=[
            "estado",
            "respondido_por",
            "comentario_cliente",
            "fecha_respuesta",
            "fecha_actualizacion",
        ]
    )
    expediente.save(
        update_fields=[
            "estado",
            "fecha_actualizacion",
        ]
    )

    registrar_mensaje_sistema(
        expediente,
        "CLIENTE_PLANNER",
        (
            texto
            + (
                f" Comentario: {comentario}"
                if comentario
                else ""
            )
        ),
        autor=request.user,
    )
    notificar_planner(
        expediente,
        "Cliente respondio propuesta",
        (
            texto
            + (
                f" {comentario}"
                if comentario
                else ""
            )
        ),
    )

    return _redirect_cliente(expediente)


@login_required
@require_POST
@transaction.atomic
def planner_confirmar_proveedor(
    request,
    expediente_id,
):
    expediente = get_object_or_404(
        ExpedienteServicio.objects.select_related(
            "evento",
            "proveedor",
            "servicio_evento",
        ),
        id=expediente_id,
    )
    if not planner_puede_expediente(
        request.user,
        expediente,
    ):
        raise PermissionDenied(
            "No puedes confirmar este servicio."
        )

    propuesta = (
        expediente.propuestas_cliente
        .filter(estado="APROBADA")
        .order_by("-version")
        .first()
    )
    if (
        not propuesta
        or not expediente.proveedor
        or not expediente.servicio_evento
    ):
        messages.error(
            request,
            "Falta aprobacion del cliente o proveedor asignado.",
        )
        return _redirect_planner(expediente)

    expediente.servicio_evento.estado = "CONTRATADO"
    expediente.servicio_evento.save(
        update_fields=[
            "estado",
            "fecha_actualizacion",
        ]
    )
    expediente.estado = "CONTRATADO"
    expediente.save(
        update_fields=[
            "estado",
            "fecha_actualizacion",
        ]
    )

    registrar_mensaje_sistema(
        expediente,
        "PLANNER_PROVEEDOR",
        "Contratacion confirmada por el planner.",
        autor=request.user,
    )
    registrar_mensaje_sistema(
        expediente,
        "CLIENTE_PLANNER",
        "El planner confirmo la contratacion del servicio.",
        autor=request.user,
    )
    notificar_proveedor(
        expediente,
        "Servicio contratado",
        (
            f"Contratacion confirmada: "
            f"{expediente.titulo}."
        ),
    )
    notificar_clientes(
        expediente,
        "Servicio confirmado",
        (
            f"El planner confirmo la contratacion de "
            f"{expediente.titulo}."
        ),
    )

    return _redirect_planner(expediente)
