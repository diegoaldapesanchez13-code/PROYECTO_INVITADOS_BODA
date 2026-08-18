"""Endpoints seguros para ciclo de vida operativo K9.8B.

K9.8A define el dominio (cancelar/archivar/desarchivar/anular). Este modulo
expone exclusivamente acciones POST tenant-aware y reutiliza la matriz central
de autorizacion. No elimina registros fisicamente.
"""

from urllib.parse import urlencode

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views.decorators.http import require_POST

from core.services.authorization import Actions, usuario_puede_evento
from core.services.ciclo_vida_operativo import (
    anular_pago_evento,
    archivar_actividad_itinerario,
    archivar_documento_evento,
    archivar_gasto_evento,
    archivar_servicio_evento,
    archivar_tarea_evento,
    cancelar_actividad_itinerario,
    cancelar_gasto_evento,
    cancelar_servicio_evento,
    cancelar_tarea_evento,
    desarchivar_actividad_itinerario,
    desarchivar_documento_evento,
    desarchivar_gasto_evento,
    desarchivar_servicio_evento,
    desarchivar_tarea_evento,
)
from core.services.permisos import roles_usuario_empresa, usuario_es_dirtec_operativo
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


def _destino_dashboard(user, empresa, evento, *, tab='operacion'):
    if usuario_es_dirtec_operativo(user):
        base = reverse('dirtec_dashboard')
    else:
        roles = roles_usuario_empresa(user, empresa)
        if roles.intersection({'ADMIN_EMPRESA', 'VENTAS'}):
            base = reverse('empresa_dashboard', kwargs={'empresa_slug': empresa.slug})
        elif 'WEDDING_PLANNER' in roles:
            base = reverse('planner_dashboard_empresa', kwargs={'empresa_slug': empresa.slug})
        else:
            base = reverse('redirigir_por_rol')
    query = urlencode({'evento': evento.id, 'tab': tab})
    return f'{base}?{query}'


def _mensaje_error(exc):
    if hasattr(exc, 'messages') and exc.messages:
        return exc.messages[0]
    return str(exc)


def _ejecutar(request, empresa, evento, funcion, *, exito, tab='operacion', **kwargs):
    try:
        funcion(actor=request.user, request=request, **kwargs)
        messages.success(request, exito)
    except ValidationError as exc:
        messages.error(request, _mensaje_error(exc))
    return redirect(_destino_dashboard(request.user, empresa, evento, tab=tab))


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
    return _ejecutar(
        request, empresa, servicio.evento, cancelar_servicio_evento,
        exito='Servicio cancelado sin eliminar su historial.',
        servicio=servicio,
        motivo=request.POST.get('motivo'),
    )


@login_required(login_url='/login/')
@require_POST
def servicio_archivar(request, empresa_slug, servicio_id):
    empresa = _empresa(request, empresa_slug)
    servicio = _servicio(empresa, servicio_id)
    _exigir_operacion(request.user, servicio.evento)
    return _ejecutar(
        request, empresa, servicio.evento, archivar_servicio_evento,
        exito='Servicio archivado.', servicio=servicio,
    )


@login_required(login_url='/login/')
@require_POST
def servicio_desarchivar(request, empresa_slug, servicio_id):
    empresa = _empresa(request, empresa_slug)
    servicio = _servicio(empresa, servicio_id)
    _exigir_operacion(request.user, servicio.evento)
    return _ejecutar(
        request, empresa, servicio.evento, desarchivar_servicio_evento,
        exito='Servicio restaurado del archivo.', servicio=servicio,
    )


@login_required(login_url='/login/')
@require_POST
def tarea_cancelar(request, empresa_slug, tarea_id):
    empresa = _empresa(request, empresa_slug)
    tarea = _tarea(empresa, tarea_id)
    _exigir_operacion(request.user, tarea.evento)
    return _ejecutar(
        request, empresa, tarea.evento, cancelar_tarea_evento,
        exito='Tarea cancelada sin perder historial.',
        tarea=tarea,
        motivo=request.POST.get('motivo'),
    )


@login_required(login_url='/login/')
@require_POST
def tarea_archivar(request, empresa_slug, tarea_id):
    empresa = _empresa(request, empresa_slug)
    tarea = _tarea(empresa, tarea_id)
    _exigir_operacion(request.user, tarea.evento)
    return _ejecutar(
        request, empresa, tarea.evento, archivar_tarea_evento,
        exito='Tarea archivada.', tarea=tarea,
    )


@login_required(login_url='/login/')
@require_POST
def tarea_desarchivar(request, empresa_slug, tarea_id):
    empresa = _empresa(request, empresa_slug)
    tarea = _tarea(empresa, tarea_id)
    _exigir_operacion(request.user, tarea.evento)
    return _ejecutar(
        request, empresa, tarea.evento, desarchivar_tarea_evento,
        exito='Tarea restaurada del archivo.', tarea=tarea,
    )


@login_required(login_url='/login/')
@require_POST
def actividad_cancelar(request, empresa_slug, actividad_id):
    empresa = _empresa(request, empresa_slug)
    actividad = _actividad(empresa, actividad_id)
    _exigir_operacion(request.user, actividad.evento)
    return _ejecutar(
        request, empresa, actividad.evento, cancelar_actividad_itinerario,
        exito='Actividad cancelada sin perder historial.',
        actividad=actividad,
        motivo=request.POST.get('motivo'),
    )


@login_required(login_url='/login/')
@require_POST
def actividad_archivar(request, empresa_slug, actividad_id):
    empresa = _empresa(request, empresa_slug)
    actividad = _actividad(empresa, actividad_id)
    _exigir_operacion(request.user, actividad.evento)
    return _ejecutar(
        request, empresa, actividad.evento, archivar_actividad_itinerario,
        exito='Actividad archivada.', actividad=actividad,
    )


@login_required(login_url='/login/')
@require_POST
def actividad_desarchivar(request, empresa_slug, actividad_id):
    empresa = _empresa(request, empresa_slug)
    actividad = _actividad(empresa, actividad_id)
    _exigir_operacion(request.user, actividad.evento)
    return _ejecutar(
        request, empresa, actividad.evento, desarchivar_actividad_itinerario,
        exito='Actividad restaurada del archivo.', actividad=actividad,
    )


@login_required(login_url='/login/')
@require_POST
def documento_archivar(request, empresa_slug, documento_id):
    empresa = _empresa(request, empresa_slug)
    documento = _documento(empresa, documento_id)
    _exigir_operacion(request.user, documento.evento)
    return _ejecutar(
        request, empresa, documento.evento, archivar_documento_evento,
        exito='Documento archivado sin eliminar el archivo.',
        documento=documento,
        motivo=request.POST.get('motivo'),
    )


@login_required(login_url='/login/')
@require_POST
def documento_desarchivar(request, empresa_slug, documento_id):
    empresa = _empresa(request, empresa_slug)
    documento = _documento(empresa, documento_id)
    _exigir_operacion(request.user, documento.evento)
    return _ejecutar(
        request, empresa, documento.evento, desarchivar_documento_evento,
        exito='Documento restaurado del archivo.', documento=documento,
    )


@login_required(login_url='/login/')
@require_POST
def gasto_cancelar(request, empresa_slug, gasto_id):
    empresa = _empresa(request, empresa_slug)
    gasto = _gasto(empresa, gasto_id)
    _exigir_finanzas(request.user, gasto.evento)
    return _ejecutar(
        request, empresa, gasto.evento, cancelar_gasto_evento,
        exito='Gasto cancelado sin eliminar su historial.',
        tab='finanzas',
        gasto=gasto,
        motivo=request.POST.get('motivo'),
    )


@login_required(login_url='/login/')
@require_POST
def gasto_archivar(request, empresa_slug, gasto_id):
    empresa = _empresa(request, empresa_slug)
    gasto = _gasto(empresa, gasto_id)
    _exigir_finanzas(request.user, gasto.evento)
    return _ejecutar(
        request, empresa, gasto.evento, archivar_gasto_evento,
        exito='Gasto archivado.', tab='finanzas', gasto=gasto,
    )


@login_required(login_url='/login/')
@require_POST
def gasto_desarchivar(request, empresa_slug, gasto_id):
    empresa = _empresa(request, empresa_slug)
    gasto = _gasto(empresa, gasto_id)
    _exigir_finanzas(request.user, gasto.evento)
    return _ejecutar(
        request, empresa, gasto.evento, desarchivar_gasto_evento,
        exito='Gasto restaurado del archivo.', tab='finanzas', gasto=gasto,
    )


@login_required(login_url='/login/')
@require_POST
def pago_anular(request, empresa_slug, pago_id):
    empresa = _empresa(request, empresa_slug)
    pago = _pago(empresa, pago_id)
    evento = pago.gasto.evento
    _exigir_finanzas(request.user, evento)
    return _ejecutar(
        request, empresa, evento, anular_pago_evento,
        exito='Pago operativo anulado sin eliminar su registro.',
        tab='finanzas',
        pago=pago,
        motivo=request.POST.get('motivo'),
    )
