from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from core.services.authorization import Actions, usuario_puede_evento, usuario_tiene_permiso
from core.services.permisos import roles_usuario_empresa, usuario_es_dirtec_operativo
from core.services.tenant_context import validar_slug_tenant
from paquetes.models import PropuestaEvento

from .models import ContratoEvento
from .services import (
    generar_contrato_v2_desde_propuesta,
    leer_contrato_interno,
    leer_contrato_publico,
    materializar_servicios_contrato_v2,
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
    try:
        contrato = generar_contrato_v2_desde_propuesta(propuesta.id, user=request.user)
        messages.success(request, 'Contrato comercial generado.')
        return redirect('eventos_contrato_detail', empresa_slug=empresa.slug, contrato_id=contrato.id)
    except ValidationError as exc:
        messages.error(request, exc.messages[0] if hasattr(exc, 'messages') else str(exc))
        return redirect(
            'paquetes_propuesta_editor',
            empresa_slug=empresa.slug,
            evento_id=propuesta.evento_id,
            propuesta_id=propuesta.id,
        )


@login_required(login_url='/login/')
@require_POST
def contrato_materializar_servicios(request, empresa_slug, contrato_id):
    context = _eventos_context(request, empresa_slug)
    empresa = context.empresa
    contrato = get_object_or_404(_contratos_empresa(empresa), pk=contrato_id)
    if not usuario_puede_evento(request.user, contrato.evento, Actions.EVENT_OPERATIONS):
        raise PermissionDenied('No tienes permiso para preparar la operacion de este contrato.')
    try:
        resultado = materializar_servicios_contrato_v2(contrato.id, user=request.user)
        messages.success(
            request,
            f"Operacion preparada: {resultado['creados']} servicios nuevos, {resultado['actualizados']} actualizados.",
        )
    except ValidationError as exc:
        messages.error(request, exc.messages[0] if hasattr(exc, 'messages') else str(exc))
    return redirect('eventos_contrato_detail', empresa_slug=empresa.slug, contrato_id=contrato.id)


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
