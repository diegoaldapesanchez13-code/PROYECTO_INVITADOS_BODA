"""Guardrails para endpoints legacy de ciclo de vida operativo.

Las mutaciones equivalentes viven en Event Workspace K9 y colaboracion K9. Estas
rutas legacy conservan resolucion tenant-aware y permisos, pero no ejecutan
logica de dominio.
"""

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.views.decorators.http import require_POST

from core.services.authorization import Actions, usuario_puede_evento
from core.services.runtime_guardrails import block_replaced_legacy_post
from core.services.tenant_context import validar_slug_tenant
from documentos.models import DocumentoEvento
from itinerario.models import ActividadItinerario
from presupuesto.models import GastoEvento, PagoEvento
from presupuesto.services import usuario_puede_ver_finanzas_internas
from proveedores.models import ServicioEvento
from tareas.models import TareaEvento


def _empresa(request, empresa_slug):
    return validar_slug_tenant(request, empresa_slug).empresa


def _exigir_operacion(user, evento):
    if not usuario_puede_evento(user, evento, Actions.EVENT_OPERATIONS):
        raise PermissionDenied('No tienes permiso para gestionar la operacion de este evento.')


def _exigir_finanzas(user, evento):
    if not usuario_puede_ver_finanzas_internas(user, evento):
        raise PermissionDenied('No tienes permiso para gestionar finanzas internas de este evento.')


def _k9_workspace_url(empresa, evento, route_name):
    return reverse(
        route_name,
        kwargs={'empresa_slug': empresa.slug, 'evento_id': evento.id},
    )


def _bloquear_lifecycle_legacy(request, *, endpoint, replacement, empresa, evento, route_name):
    return block_replaced_legacy_post(
        request,
        endpoint=endpoint,
        replacement=replacement,
        redirect_to=_k9_workspace_url(empresa, evento, route_name),
        empresa=empresa,
        evento=evento,
    )


def _servicio(empresa, objeto_id):
    return get_object_or_404(
        ServicioEvento.objects.select_related('evento', 'evento__empresa'),
        pk=objeto_id,
        evento__empresa=empresa,
    )


def _tarea(empresa, objeto_id):
    return get_object_or_404(
        TareaEvento.objects.select_related('evento', 'evento__empresa'),
        pk=objeto_id,
        evento__empresa=empresa,
    )


def _actividad(empresa, objeto_id):
    return get_object_or_404(
        ActividadItinerario.objects.select_related('evento', 'evento__empresa'),
        pk=objeto_id,
        evento__empresa=empresa,
    )


def _documento(empresa, objeto_id):
    return get_object_or_404(
        DocumentoEvento.objects.select_related('evento', 'evento__empresa'),
        pk=objeto_id,
        evento__empresa=empresa,
    )


def _gasto(empresa, objeto_id):
    return get_object_or_404(
        GastoEvento.objects.select_related('evento', 'evento__empresa'),
        pk=objeto_id,
        evento__empresa=empresa,
    )


def _pago(empresa, objeto_id):
    return get_object_or_404(
        PagoEvento.objects.select_related('gasto', 'gasto__evento', 'gasto__evento__empresa'),
        pk=objeto_id,
        gasto__evento__empresa=empresa,
    )


@login_required(login_url='/login/')
@require_POST
def servicio_cancelar(request, empresa_slug, servicio_id):
    empresa = _empresa(request, empresa_slug)
    servicio = _servicio(empresa, servicio_id)
    _exigir_operacion(request.user, servicio.evento)
    return _bloquear_lifecycle_legacy(
        request,
        endpoint='eventos_servicio_cancelar',
        replacement='k9_evento_servicios:accion=cancelar',
        empresa=empresa,
        evento=servicio.evento,
        route_name='k9_evento_servicios',
    )


@login_required(login_url='/login/')
@require_POST
def servicio_archivar(request, empresa_slug, servicio_id):
    empresa = _empresa(request, empresa_slug)
    servicio = _servicio(empresa, servicio_id)
    _exigir_operacion(request.user, servicio.evento)
    return _bloquear_lifecycle_legacy(
        request,
        endpoint='eventos_servicio_archivar',
        replacement='k9_evento_servicios:accion=archivar',
        empresa=empresa,
        evento=servicio.evento,
        route_name='k9_evento_servicios',
    )


@login_required(login_url='/login/')
@require_POST
def servicio_desarchivar(request, empresa_slug, servicio_id):
    empresa = _empresa(request, empresa_slug)
    servicio = _servicio(empresa, servicio_id)
    _exigir_operacion(request.user, servicio.evento)
    return _bloquear_lifecycle_legacy(
        request,
        endpoint='eventos_servicio_desarchivar',
        replacement='k9_evento_servicios:accion=restaurar',
        empresa=empresa,
        evento=servicio.evento,
        route_name='k9_evento_servicios',
    )


@login_required(login_url='/login/')
@require_POST
def tarea_cancelar(request, empresa_slug, tarea_id):
    empresa = _empresa(request, empresa_slug)
    tarea = _tarea(empresa, tarea_id)
    _exigir_operacion(request.user, tarea.evento)
    return _bloquear_lifecycle_legacy(
        request,
        endpoint='eventos_tarea_cancelar',
        replacement='k9_evento_tareas:accion=cancelar',
        empresa=empresa,
        evento=tarea.evento,
        route_name='k9_evento_tareas',
    )


@login_required(login_url='/login/')
@require_POST
def tarea_archivar(request, empresa_slug, tarea_id):
    empresa = _empresa(request, empresa_slug)
    tarea = _tarea(empresa, tarea_id)
    _exigir_operacion(request.user, tarea.evento)
    return _bloquear_lifecycle_legacy(
        request,
        endpoint='eventos_tarea_archivar',
        replacement='k9_evento_tareas:accion=archivar',
        empresa=empresa,
        evento=tarea.evento,
        route_name='k9_evento_tareas',
    )


@login_required(login_url='/login/')
@require_POST
def tarea_desarchivar(request, empresa_slug, tarea_id):
    empresa = _empresa(request, empresa_slug)
    tarea = _tarea(empresa, tarea_id)
    _exigir_operacion(request.user, tarea.evento)
    return _bloquear_lifecycle_legacy(
        request,
        endpoint='eventos_tarea_desarchivar',
        replacement='k9_evento_tareas:accion=restaurar',
        empresa=empresa,
        evento=tarea.evento,
        route_name='k9_evento_tareas',
    )


@login_required(login_url='/login/')
@require_POST
def actividad_cancelar(request, empresa_slug, actividad_id):
    empresa = _empresa(request, empresa_slug)
    actividad = _actividad(empresa, actividad_id)
    _exigir_operacion(request.user, actividad.evento)
    return _bloquear_lifecycle_legacy(
        request,
        endpoint='eventos_actividad_cancelar',
        replacement='k9_evento_agenda:accion=cancelar',
        empresa=empresa,
        evento=actividad.evento,
        route_name='k9_evento_agenda',
    )


@login_required(login_url='/login/')
@require_POST
def actividad_archivar(request, empresa_slug, actividad_id):
    empresa = _empresa(request, empresa_slug)
    actividad = _actividad(empresa, actividad_id)
    _exigir_operacion(request.user, actividad.evento)
    return _bloquear_lifecycle_legacy(
        request,
        endpoint='eventos_actividad_archivar',
        replacement='k9_evento_agenda:accion=archivar',
        empresa=empresa,
        evento=actividad.evento,
        route_name='k9_evento_agenda',
    )


@login_required(login_url='/login/')
@require_POST
def actividad_desarchivar(request, empresa_slug, actividad_id):
    empresa = _empresa(request, empresa_slug)
    actividad = _actividad(empresa, actividad_id)
    _exigir_operacion(request.user, actividad.evento)
    return _bloquear_lifecycle_legacy(
        request,
        endpoint='eventos_actividad_desarchivar',
        replacement='k9_evento_agenda:accion=restaurar',
        empresa=empresa,
        evento=actividad.evento,
        route_name='k9_evento_agenda',
    )


@login_required(login_url='/login/')
@require_POST
def documento_archivar(request, empresa_slug, documento_id):
    empresa = _empresa(request, empresa_slug)
    documento = _documento(empresa, documento_id)
    _exigir_operacion(request.user, documento.evento)
    return _bloquear_lifecycle_legacy(
        request,
        endpoint='eventos_documento_archivar',
        replacement='k9_documento_archivar',
        empresa=empresa,
        evento=documento.evento,
        route_name='k9_evento_documentos',
    )


@login_required(login_url='/login/')
@require_POST
def documento_desarchivar(request, empresa_slug, documento_id):
    empresa = _empresa(request, empresa_slug)
    documento = _documento(empresa, documento_id)
    _exigir_operacion(request.user, documento.evento)
    return _bloquear_lifecycle_legacy(
        request,
        endpoint='eventos_documento_desarchivar',
        replacement='k9_documento_restaurar',
        empresa=empresa,
        evento=documento.evento,
        route_name='k9_evento_documentos',
    )


@login_required(login_url='/login/')
@require_POST
def gasto_cancelar(request, empresa_slug, gasto_id):
    empresa = _empresa(request, empresa_slug)
    gasto = _gasto(empresa, gasto_id)
    _exigir_finanzas(request.user, gasto.evento)
    return _bloquear_lifecycle_legacy(
        request,
        endpoint='eventos_gasto_cancelar',
        replacement='k9_finanzas_gasto_cancelar',
        empresa=empresa,
        evento=gasto.evento,
        route_name='k9_evento_finanzas',
    )


@login_required(login_url='/login/')
@require_POST
def gasto_archivar(request, empresa_slug, gasto_id):
    empresa = _empresa(request, empresa_slug)
    gasto = _gasto(empresa, gasto_id)
    _exigir_finanzas(request.user, gasto.evento)
    return _bloquear_lifecycle_legacy(
        request,
        endpoint='eventos_gasto_archivar',
        replacement='k9_finanzas_gasto_archivar',
        empresa=empresa,
        evento=gasto.evento,
        route_name='k9_evento_finanzas',
    )


@login_required(login_url='/login/')
@require_POST
def gasto_desarchivar(request, empresa_slug, gasto_id):
    empresa = _empresa(request, empresa_slug)
    gasto = _gasto(empresa, gasto_id)
    _exigir_finanzas(request.user, gasto.evento)
    return _bloquear_lifecycle_legacy(
        request,
        endpoint='eventos_gasto_desarchivar',
        replacement='k9_finanzas_gasto_restaurar',
        empresa=empresa,
        evento=gasto.evento,
        route_name='k9_evento_finanzas',
    )


@login_required(login_url='/login/')
@require_POST
def pago_anular(request, empresa_slug, pago_id):
    empresa = _empresa(request, empresa_slug)
    pago = _pago(empresa, pago_id)
    evento = pago.gasto.evento
    _exigir_finanzas(request.user, evento)
    return _bloquear_lifecycle_legacy(
        request,
        endpoint='eventos_pago_anular',
        replacement='k9_finanzas_pago_anular',
        empresa=empresa,
        evento=evento,
        route_name='k9_evento_finanzas',
    )
