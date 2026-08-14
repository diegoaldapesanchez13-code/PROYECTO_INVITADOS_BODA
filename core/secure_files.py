import mimetypes
from pathlib import Path

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404

from core.services.authorization import Actions, usuario_puede_evento, usuario_tiene_permiso
from colaboracion.models import AdjuntoMensajeServicio, CotizacionServicio
from colaboracion.services import canales_visibles_workspace
from documentos.models import DocumentoEvento
from presupuesto.models import PagoClienteEvento, PagoEvento
from proveedores.models import ServicioEvento
from tareas.models import TareaEvento


def _file_response(field_file, *, download=False):
    if not field_file:
        raise Http404("Archivo no disponible.")
    try:
        path = field_file.path
    except (NotImplementedError, ValueError):
        path = None
    if not path or not Path(path).exists():
        raise Http404("Archivo no encontrado.")
    content_type, _ = mimetypes.guess_type(field_file.name)
    return FileResponse(
        open(path, "rb"),
        as_attachment=download,
        filename=Path(field_file.name).name,
        content_type=content_type or "application/octet-stream",
    )


def _es_cliente_evento(user, evento):
    return bool(
        getattr(user, "is_authenticated", False)
        and usuario_tiene_permiso(user, Actions.CLIENT_PORTAL, empresa=evento.empresa)
        and evento.clientes.filter(id=user.id).exists()
    )


def _es_proveedor_servicio(user, servicio):
    return bool(
        getattr(user, "is_authenticated", False)
        and usuario_tiene_permiso(user, Actions.PROVIDER_PORTAL, empresa=servicio.evento.empresa)
        and servicio.proveedor_id
        and servicio.proveedor
        and servicio.proveedor.activo
        and servicio.proveedor.usuario_id == user.id
    )


def _es_proveedor_directo_recurso(user, proveedor, evento):
    return bool(
        getattr(user, "is_authenticated", False)
        and proveedor
        and proveedor.activo
        and proveedor.usuario_id == user.id
        and proveedor.empresa_id == evento.empresa_id
        and usuario_tiene_permiso(user, Actions.PROVIDER_PORTAL, empresa=evento.empresa)
    )


@login_required
def documento_evento(request, documento_id):
    documento = get_object_or_404(
        DocumentoEvento.objects.select_related(
            "evento",
            "evento__empresa",
            "servicio_evento",
            "servicio_evento__proveedor",
            "proveedor",
        ),
        pk=documento_id,
    )
    evento = documento.evento
    permitido = usuario_puede_evento(request.user, evento, Actions.EVENT_OPERATIONS)
    if not permitido and documento.visible_cliente and _es_cliente_evento(request.user, evento):
        permitido = True
    if not permitido and documento.visible_proveedor:
        servicio = documento.servicio_evento
        if servicio and _es_proveedor_servicio(request.user, servicio):
            permitido = True
        elif not servicio and _es_proveedor_directo_recurso(request.user, documento.proveedor, evento):
            permitido = True
    if not permitido:
        raise PermissionDenied("No tienes permiso para descargar este documento.")
    return _file_response(documento.archivo)


@login_required
def pago_cliente_comprobante(request, pago_id):
    pago = get_object_or_404(
        PagoClienteEvento.objects.select_related("evento", "evento__empresa"),
        pk=pago_id,
    )
    if not (
        usuario_puede_evento(request.user, pago.evento, Actions.EVENT_OPERATIONS)
        or _es_cliente_evento(request.user, pago.evento)
    ):
        raise PermissionDenied("No tienes permiso para ver este comprobante.")
    return _file_response(pago.comprobante)


@login_required
def pago_operativo_comprobante(request, pago_id):
    pago = get_object_or_404(
        PagoEvento.objects.select_related(
            "gasto__evento",
            "gasto__evento__empresa",
            "gasto__proveedor",
            "gasto__servicio_evento__evento",
            "gasto__servicio_evento__evento__empresa",
            "gasto__servicio_evento__proveedor",
        ),
        pk=pago_id,
    )
    evento = pago.gasto.evento
    permitido = usuario_puede_evento(request.user, evento, Actions.EVENT_OPERATIONS)
    if not permitido:
        servicio = pago.gasto.servicio_evento
        if servicio:
            permitido = _es_proveedor_servicio(request.user, servicio)
        elif pago.gasto.proveedor_id:
            permitido = _es_proveedor_directo_recurso(request.user, pago.gasto.proveedor, evento)
    if not permitido:
        raise PermissionDenied("No tienes permiso para ver este comprobante.")
    return _file_response(pago.comprobante)


@login_required
def cotizacion_servicio(request, cotizacion_id):
    cotizacion = get_object_or_404(
        CotizacionServicio.objects.select_related(
            "servicio_evento__evento",
            "servicio_evento__evento__empresa",
            "servicio_evento__proveedor",
        ),
        pk=cotizacion_id,
    )
    servicio = cotizacion.servicio_evento
    if not (
        usuario_puede_evento(request.user, servicio.evento, Actions.EVENT_OPERATIONS)
        or _es_proveedor_servicio(request.user, servicio)
    ):
        raise PermissionDenied("No tienes permiso para ver esta cotización.")
    return _file_response(cotizacion.archivo)


@login_required
def adjunto_workspace(request, adjunto_id):
    adjunto = get_object_or_404(
        AdjuntoMensajeServicio.objects.select_related(
            "mensaje__conversacion__servicio_evento__evento",
            "mensaje__conversacion__servicio_evento__evento__empresa",
            "mensaje__conversacion__servicio_evento__proveedor",
        ),
        pk=adjunto_id,
    )
    conversacion = adjunto.mensaje.conversacion
    servicio = conversacion.servicio_evento
    if conversacion.canal not in canales_visibles_workspace(request.user, servicio):
        raise PermissionDenied("No tienes permiso para ver este archivo.")
    return _file_response(adjunto.archivo)


@login_required
def evidencia_tarea(request, tarea_id):
    tarea = get_object_or_404(
        TareaEvento.objects.select_related("evento", "evento__empresa", "responsable"),
        pk=tarea_id,
    )
    if not (
        usuario_puede_evento(request.user, tarea.evento, Actions.EVENT_OPERATIONS)
        or tarea.responsable_id == request.user.id
    ):
        raise PermissionDenied("No tienes permiso para ver esta evidencia.")
    return _file_response(tarea.evidencia)
