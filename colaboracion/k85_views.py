from datetime import date

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views.decorators.http import require_POST

from proveedores.models import ServicioEvento
from .models import AprobacionServicio, CotizacionServicio, MensajeServicio, PropuestaServicioCliente, TemaServicio
from .services import (
    crear_cotizacion_servicio, crear_propuesta_servicio, decidir_cotizacion_servicio,
    es_operador_servicio_workspace, es_proveedor_servicio_workspace, registrar_decision_servicio,
    responder_aprobacion_servicio, responder_propuesta_servicio, solicitar_aprobacion_servicio,
)


def _url(servicio):
    return f"{reverse('colaboracion_workspace_servicio', args=[servicio.id])}?canal=CLIENTE_PLANNER"


def _servicio(pk):
    return get_object_or_404(ServicioEvento.objects.select_related("evento", "evento__empresa", "proveedor"), pk=pk)


@login_required
@require_POST
@transaction.atomic
def registrar_decision(request, servicio_id):
    servicio = _servicio(servicio_id)
    tema = None
    if request.POST.get("tema_id"):
        tema = get_object_or_404(TemaServicio, pk=request.POST["tema_id"], servicio_evento=servicio)
    mensaje_origen = None
    if request.POST.get("mensaje_id"):
        mensaje_origen = get_object_or_404(MensajeServicio, pk=request.POST["mensaje_id"], conversacion__servicio_evento=servicio)
    try:
        registrar_decision_servicio(servicio, user=request.user, titulo=request.POST.get("titulo"), descripcion=request.POST.get("descripcion", ""), tema=tema, mensaje_origen=mensaje_origen)
        messages.success(request, "Decision registrada.")
    except (ValueError, PermissionDenied) as exc:
        if isinstance(exc, PermissionDenied): raise
        messages.error(request, str(exc))
    return redirect(_url(servicio))


@login_required
@require_POST
@transaction.atomic
def crear_cotizacion(request, servicio_id):
    servicio = _servicio(servicio_id)
    try:
        crear_cotizacion_servicio(servicio, user=request.user, costo_proveedor=request.POST.get("costo_proveedor"), descripcion=request.POST.get("descripcion", ""), vigencia=request.POST.get("vigencia") or None, archivo=request.FILES.get("archivo"))
        messages.success(request, "Cotizacion registrada como nueva version.")
    except (ValueError, PermissionDenied) as exc:
        if isinstance(exc, PermissionDenied): raise
        messages.error(request, str(exc))
    if es_proveedor_servicio_workspace(request.user, servicio):
        return redirect(f"{reverse('portal_proveedor')}?evento={servicio.evento_id}#cotizaciones")
    return redirect(_url(servicio))


@login_required
@require_POST
@transaction.atomic
def decidir_cotizacion(request, cotizacion_id):
    cotizacion = get_object_or_404(CotizacionServicio.objects.select_related("servicio_evento__evento"), pk=cotizacion_id)
    try:
        decidir_cotizacion_servicio(cotizacion, user=request.user, estado=request.POST.get("estado"), comentario=request.POST.get("comentario", ""))
        messages.success(request, "Cotizacion actualizada.")
    except (ValueError, PermissionDenied) as exc:
        if isinstance(exc, PermissionDenied): raise
        messages.error(request, str(exc))
    return redirect(_url(cotizacion.servicio_evento))


@login_required
@require_POST
@transaction.atomic
def crear_propuesta(request, servicio_id):
    servicio = _servicio(servicio_id)
    cotizacion = None
    if request.POST.get("cotizacion_id"):
        cotizacion = get_object_or_404(CotizacionServicio, pk=request.POST["cotizacion_id"], servicio_evento=servicio)
    try:
        crear_propuesta_servicio(servicio, user=request.user, descripcion=request.POST.get("descripcion", ""), modalidad=request.POST.get("modalidad") or None, cargo_adicional_cliente=request.POST.get("cargo_adicional_cliente"), cotizacion=cotizacion, enviar=True)
        messages.success(request, "Propuesta enviada al cliente.")
    except (ValueError, PermissionDenied) as exc:
        if isinstance(exc, PermissionDenied): raise
        messages.error(request, str(exc))
    return redirect(_url(servicio))


@login_required
@require_POST
@transaction.atomic
def responder_propuesta(request, propuesta_id):
    propuesta = get_object_or_404(PropuestaServicioCliente.objects.select_related("servicio_evento__evento"), pk=propuesta_id)
    try:
        responder_propuesta_servicio(propuesta, user=request.user, estado=request.POST.get("estado"), comentario=request.POST.get("comentario", ""))
        messages.success(request, "Respuesta de propuesta registrada.")
    except (ValueError, PermissionDenied) as exc:
        if isinstance(exc, PermissionDenied): raise
        messages.error(request, str(exc))
    return redirect(_url(propuesta.servicio_evento))


@login_required
@require_POST
@transaction.atomic
def solicitar_aprobacion(request, servicio_id):
    servicio = _servicio(servicio_id)
    try:
        solicitar_aprobacion_servicio(servicio, user=request.user, titulo=request.POST.get("titulo"), descripcion=request.POST.get("descripcion", ""))
        messages.success(request, "Aprobacion enviada al cliente.")
    except (ValueError, PermissionDenied) as exc:
        if isinstance(exc, PermissionDenied): raise
        messages.error(request, str(exc))
    return redirect(_url(servicio))


@login_required
@require_POST
@transaction.atomic
def responder_aprobacion(request, aprobacion_id):
    aprobacion = get_object_or_404(AprobacionServicio.objects.select_related("servicio_evento__evento"), pk=aprobacion_id)
    try:
        responder_aprobacion_servicio(aprobacion, user=request.user, estado=request.POST.get("estado"), comentario=request.POST.get("comentario", ""))
        messages.success(request, "Aprobacion respondida.")
    except (ValueError, PermissionDenied) as exc:
        if isinstance(exc, PermissionDenied): raise
        messages.error(request, str(exc))
    return redirect(_url(aprobacion.servicio_evento))
