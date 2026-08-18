from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from core.secure_files import _file_response
from core.services.permisos import roles_usuario_empresa, usuario_es_dirtec_operativo
from core.services.tenant_context import validar_slug_tenant
from eventos.models import ContratoEvento
from invitaciones.models import EventoBoda

from .forms import (
    PaqueteComercialForm,
    PaqueteMediaComercialForm,
    PaqueteServicioForm,
    PropuestaEventoForm,
    PropuestaLineaForm,
)
from .models import PaqueteMediaComercial, PaqueteServicio, PropuestaLinea
from .services import (
    actualizar_totales_propuesta,
    calcular_propuesta,
    puede_editar_propuesta,
    puede_gestionar_paquetes,
    puede_ver_paquetes,
    paquetes_empresa_qs,
    propuestas_empresa_qs,
)


def _paquetes_context(request, empresa_slug):
    context = validar_slug_tenant(request, empresa_slug)
    empresa = context.empresa
    if not puede_ver_paquetes(request.user, empresa):
        raise PermissionDenied('No tienes permiso para consultar paquetes.')
    return context


def _dashboard_url(user, empresa):
    if usuario_es_dirtec_operativo(user):
        return reverse('dirtec_dashboard')
    roles = roles_usuario_empresa(user, empresa)
    if roles.intersection({'ADMIN_EMPRESA', 'VENTAS'}):
        return reverse('empresa_dashboard', kwargs={'empresa_slug': empresa.slug})
    if 'WEDDING_PLANNER' in roles:
        return reverse('planner_dashboard_empresa', kwargs={'empresa_slug': empresa.slug})
    return None


def _template_context(request, empresa, **extra):
    context = {
        'empresa': empresa,
        'dashboard_url': _dashboard_url(request.user, empresa),
    }
    context.update(extra)
    return context


def _evento_empresa(empresa, evento_id):
    return get_object_or_404(
        EventoBoda.objects.select_related('empresa', 'sede', 'wedding_planner'),
        empresa=empresa,
        pk=evento_id,
    )


@login_required(login_url='/login/')
def paquete_list(request, empresa_slug):
    context = _paquetes_context(request, empresa_slug)
    empresa = context.empresa
    paquetes = paquetes_empresa_qs(empresa)

    busqueda = (request.GET.get('q') or '').strip()
    estado = request.GET.get('estado') or ''
    if busqueda:
        paquetes = paquetes.filter(Q(nombre__icontains=busqueda) | Q(descripcion__icontains=busqueda))
    if estado == 'activo':
        paquetes = paquetes.filter(activo=True)
    elif estado == 'inactivo':
        paquetes = paquetes.filter(activo=False)

    paginator = Paginator(paquetes, 12)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(
        request,
        'paquetes/paquete_list.html',
        _template_context(
            request,
            empresa,
            paquetes=page_obj.object_list,
            page_obj=page_obj,
            busqueda=busqueda,
            estado=estado,
            puede_gestionar=puede_gestionar_paquetes(request.user, empresa),
        ),
    )


@login_required(login_url='/login/')
def paquete_create(request, empresa_slug):
    context = _paquetes_context(request, empresa_slug)
    empresa = context.empresa
    if not puede_gestionar_paquetes(request.user, empresa):
        raise PermissionDenied('No tienes permiso para crear paquetes.')
    form = PaqueteComercialForm(request.POST or None, request.FILES or None, empresa=empresa)
    if request.method == 'POST' and form.is_valid():
        paquete = form.save()
        messages.success(request, 'Paquete comercial creado.')
        return redirect('paquetes_paquete_detail', empresa_slug=empresa.slug, paquete_id=paquete.id)
    return render(
        request,
        'paquetes/paquete_form.html',
        _template_context(request, empresa, form=form, modo='crear'),
    )


@login_required(login_url='/login/')
def paquete_update(request, empresa_slug, paquete_id):
    context = _paquetes_context(request, empresa_slug)
    empresa = context.empresa
    if not puede_gestionar_paquetes(request.user, empresa):
        raise PermissionDenied('No tienes permiso para editar paquetes.')
    paquete = get_object_or_404(paquetes_empresa_qs(empresa), pk=paquete_id)
    form = PaqueteComercialForm(request.POST or None, request.FILES or None, instance=paquete, empresa=empresa)
    if request.method == 'POST' and form.is_valid():
        paquete = form.save()
        messages.success(request, 'Paquete comercial actualizado.')
        return redirect('paquetes_paquete_detail', empresa_slug=empresa.slug, paquete_id=paquete.id)
    return render(
        request,
        'paquetes/paquete_form.html',
        _template_context(request, empresa, form=form, paquete=paquete, modo='editar'),
    )


@login_required(login_url='/login/')
def paquete_detail(request, empresa_slug, paquete_id):
    context = _paquetes_context(request, empresa_slug)
    empresa = context.empresa
    paquete = get_object_or_404(paquetes_empresa_qs(empresa), pk=paquete_id)
    puede_gestionar = puede_gestionar_paquetes(request.user, empresa)
    return render(
        request,
        'paquetes/paquete_detail.html',
        _template_context(
            request,
            empresa,
            paquete=paquete,
            servicio_form=PaqueteServicioForm(paquete=paquete),
            media_form=PaqueteMediaComercialForm(),
            dto_incluidos=calcular_propuesta,
            puede_gestionar=puede_gestionar,
        ),
    )


@login_required(login_url='/login/')
@require_POST
def paquete_servicio_create(request, empresa_slug, paquete_id):
    context = _paquetes_context(request, empresa_slug)
    empresa = context.empresa
    if not puede_gestionar_paquetes(request.user, empresa):
        raise PermissionDenied('No tienes permiso para modificar paquetes.')
    paquete = get_object_or_404(paquetes_empresa_qs(empresa), pk=paquete_id)
    form = PaqueteServicioForm(request.POST, paquete=paquete)
    if form.is_valid():
        try:
            form.save()
            messages.success(request, 'Servicio incluido agregado.')
        except ValidationError as exc:
            messages.error(request, exc.messages[0] if hasattr(exc, 'messages') else str(exc))
    else:
        messages.error(request, 'No se pudo agregar el servicio. Revisa los datos.')
    return redirect('paquetes_paquete_detail', empresa_slug=empresa.slug, paquete_id=paquete.id)


@login_required(login_url='/login/')
@require_POST
def paquete_media_create(request, empresa_slug, paquete_id):
    context = _paquetes_context(request, empresa_slug)
    empresa = context.empresa
    if not puede_gestionar_paquetes(request.user, empresa):
        raise PermissionDenied('No tienes permiso para modificar media de paquetes.')
    paquete = get_object_or_404(paquetes_empresa_qs(empresa), pk=paquete_id)
    form = PaqueteMediaComercialForm(request.POST, request.FILES)
    if form.is_valid():
        media = form.save(commit=False)
        media.paquete = paquete
        try:
            media.full_clean()
            media.save()
            messages.success(request, 'Media comercial agregada.')
        except ValidationError as exc:
            messages.error(request, exc.messages[0] if hasattr(exc, 'messages') else str(exc))
    else:
        messages.error(request, 'No se pudo agregar la media comercial.')
    return redirect('paquetes_paquete_detail', empresa_slug=empresa.slug, paquete_id=paquete.id)


@login_required(login_url='/login/')
def paquete_portada(request, empresa_slug, paquete_id):
    context = _paquetes_context(request, empresa_slug)
    paquete = get_object_or_404(paquetes_empresa_qs(context.empresa), pk=paquete_id)
    return _file_response(paquete.portada)


@login_required(login_url='/login/')
def paquete_pdf(request, empresa_slug, paquete_id):
    context = _paquetes_context(request, empresa_slug)
    paquete = get_object_or_404(paquetes_empresa_qs(context.empresa), pk=paquete_id)
    return _file_response(paquete.pdf_comercial, download=True)


@login_required(login_url='/login/')
def paquete_media_download(request, empresa_slug, paquete_id, media_id):
    context = _paquetes_context(request, empresa_slug)
    paquete = get_object_or_404(paquetes_empresa_qs(context.empresa), pk=paquete_id)
    media = get_object_or_404(PaqueteMediaComercial, paquete=paquete, pk=media_id)
    return _file_response(media.archivo, download=media.tipo == 'PDF')


@login_required(login_url='/login/')
def propuesta_editor(request, empresa_slug, evento_id, propuesta_id=None):
    context = _paquetes_context(request, empresa_slug)
    empresa = context.empresa
    evento = _evento_empresa(empresa, evento_id)
    if not puede_editar_propuesta(request.user, evento):
        raise PermissionDenied('No tienes permiso para preparar propuestas de este evento.')

    propuesta = None
    if propuesta_id:
        propuesta = get_object_or_404(propuestas_empresa_qs(empresa), evento=evento, pk=propuesta_id)

    if request.method == 'POST' and request.POST.get('accion') == 'guardar_propuesta':
        form = PropuestaEventoForm(request.POST, instance=propuesta, empresa=empresa, evento=evento)
        if form.is_valid():
            propuesta = form.save(commit=False)
            if not propuesta.pk:
                propuesta.created_by = request.user
            propuesta.updated_by = request.user
            propuesta.full_clean()
            propuesta.save()
            actualizar_totales_propuesta(propuesta, user=request.user)
            messages.success(request, 'Propuesta guardada.')
            return redirect(
                'paquetes_propuesta_editor',
                empresa_slug=empresa.slug,
                evento_id=evento.id,
                propuesta_id=propuesta.id,
            )
    else:
        form = PropuestaEventoForm(instance=propuesta, empresa=empresa, evento=evento)

    linea_form = PropuestaLineaForm(propuesta=propuesta) if propuesta else None
    dto = calcular_propuesta(propuesta) if propuesta else None

    if request.method == 'POST' and request.POST.get('accion') == 'agregar_linea':
        if not propuesta:
            raise PermissionDenied('Guarda la propuesta antes de agregar lineas.')
        linea_form = PropuestaLineaForm(request.POST, propuesta=propuesta)
        if linea_form.is_valid():
            linea_form.save()
            actualizar_totales_propuesta(propuesta, user=request.user)
            messages.success(request, 'Linea agregada a la propuesta.')
            return redirect(
                'paquetes_propuesta_editor',
                empresa_slug=empresa.slug,
                evento_id=evento.id,
                propuesta_id=propuesta.id,
            )
        dto = calcular_propuesta(propuesta)

    propuestas = propuestas_empresa_qs(empresa).filter(evento=evento)
    contrato_existente = None
    if propuesta:
        contrato_existente = ContratoEvento.objects.filter(propuesta_origen=propuesta).first()
    return render(
        request,
        'paquetes/propuesta_editor.html',
        _template_context(
            request,
            empresa,
            evento=evento,
            propuesta=propuesta,
            propuestas=propuestas,
            form=form,
            linea_form=linea_form,
            dto=dto,
            contrato_existente=contrato_existente,
        ),
    )


@login_required(login_url='/login/')
@require_POST
def propuesta_linea_toggle(request, empresa_slug, evento_id, propuesta_id, linea_id):
    context = _paquetes_context(request, empresa_slug)
    empresa = context.empresa
    evento = _evento_empresa(empresa, evento_id)
    propuesta = get_object_or_404(propuestas_empresa_qs(empresa), evento=evento, pk=propuesta_id)
    if not puede_editar_propuesta(request.user, propuesta):
        raise PermissionDenied('No tienes permiso para modificar esta propuesta.')
    linea = get_object_or_404(PropuestaLinea, propuesta=propuesta, pk=linea_id)
    linea.activo = not linea.activo
    linea.save(update_fields=['activo', 'updated_at'])
    actualizar_totales_propuesta(propuesta, user=request.user)
    messages.success(request, 'Linea reactivada.' if linea.activo else 'Linea retirada de la propuesta.')
    return redirect(
        'paquetes_propuesta_editor',
        empresa_slug=empresa.slug,
        evento_id=evento.id,
        propuesta_id=propuesta.id,
    )
