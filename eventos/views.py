from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from core.services.authorization import Actions, usuario_puede_evento, usuario_tiene_permiso
from core.services.permisos import roles_usuario_empresa, usuario_es_dirtec_operativo
from core.services.runtime_guardrails import block_replaced_legacy_post
from core.services.tenant_context import validar_slug_tenant
from paquetes.models import PropuestaEvento

from .models import ContratoEvento
from .services import (
    leer_contrato_interno,
    leer_contrato_publico,
)


def _eventos_context(request, empresa_slug):
    return validar_slug_tenant(request, empresa_slug)


def _dashboard_url(user, empresa):
    if usuario_es_dirtec_operativo(user):
        return reverse('dirtec_dashboard')
    roles = roles_usuario_empresa(user, empresa)
    if roles.intersection({'ADMIN_EMPRESA', 'VENTAS'}):
        return reverse('empresa_dashboard', kwargs={'empresa_slug': empresa.slug})
    if 'WEDDING_PLANNER' in roles:
        return reverse('planner_dashboard_empresa', kwargs={'empresa_slug': empresa.slug})
    return None


def _es_cliente_evento(user, evento):
    return bool(
        usuario_tiene_permiso(user, Actions.CLIENT_PORTAL, empresa=evento.empresa)
        and evento.clientes.filter(id=user.id).exists()
    )


def _contratos_empresa(empresa):
    return ContratoEvento.objects.filter(evento__empresa=empresa).select_related(
        'evento',
        'evento__empresa',
        'propuesta_origen',
    )


@login_required(login_url='/login/')
@require_POST
def contrato_generar_desde_propuesta(request, empresa_slug, propuesta_id):
    context = _eventos_context(request, empresa_slug)
    empresa = context.empresa
    propuesta = get_object_or_404(
        PropuestaEvento.objects.select_related('empresa', 'evento'),
        empresa=empresa,
        pk=propuesta_id,
    )
    if not usuario_puede_evento(request.user, propuesta.evento, Actions.EVENT_EDIT):
        raise PermissionDenied('No tienes permiso para contratar esta propuesta.')
    return block_replaced_legacy_post(
        request,
        endpoint='eventos_contrato_generar',
        replacement='k9_evento_comercial:generar_contrato',
        redirect_to=f"{reverse('k9_evento_comercial', kwargs={'empresa_slug': empresa.slug, 'evento_id': propuesta.evento_id})}?propuesta={propuesta.id}",
        empresa=empresa,
        evento=propuesta.evento,
    )


@login_required(login_url='/login/')
@require_POST
def contrato_materializar_servicios(request, empresa_slug, contrato_id):
    context = _eventos_context(request, empresa_slug)
    empresa = context.empresa
    contrato = get_object_or_404(_contratos_empresa(empresa), pk=contrato_id)
    if not usuario_puede_evento(request.user, contrato.evento, Actions.EVENT_OPERATIONS):
        raise PermissionDenied('No tienes permiso para preparar la operacion de este contrato.')
    propuesta_id = contrato.propuesta_origen_id
    redirect_to = reverse(
        'k9_evento_comercial',
        kwargs={'empresa_slug': empresa.slug, 'evento_id': contrato.evento_id},
    )
    if propuesta_id:
        redirect_to = f"{redirect_to}?propuesta={propuesta_id}"
    return block_replaced_legacy_post(
        request,
        endpoint='eventos_contrato_materializar',
        replacement='k9_evento_comercial:materializar_contrato',
        redirect_to=redirect_to,
        empresa=empresa,
        evento=contrato.evento,
    )


@login_required(login_url='/login/')
def contrato_detail(request, empresa_slug, contrato_id):
    context = _eventos_context(request, empresa_slug)
    empresa = context.empresa
    contrato = get_object_or_404(_contratos_empresa(empresa), pk=contrato_id)
    evento = contrato.evento
    if not usuario_puede_evento(request.user, evento, Actions.EVENT_VIEW):
        raise PermissionDenied('No tienes permiso para ver este contrato.')

    es_cliente = _es_cliente_evento(request.user, evento)
    puede_materializar = usuario_puede_evento(request.user, evento, Actions.EVENT_OPERATIONS)
    contrato_data = leer_contrato_publico(contrato) if es_cliente else leer_contrato_interno(contrato)
    return render(
        request,
        'eventos/contrato_detail.html',
        {
            'empresa': empresa,
            'contrato': contrato,
            'contrato_data': contrato_data,
            'dashboard_url': _dashboard_url(request.user, empresa),
            'es_cliente': es_cliente,
            'puede_materializar': puede_materializar,
            'servicios_materializados_count': contrato.servicios_materializados.count(),
        },
    )
