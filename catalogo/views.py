from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from core.services.permisos import roles_usuario_empresa, usuario_es_dirtec_operativo
from core.services.tenant_context import validar_slug_tenant
from core.secure_files import _file_response
from proveedores.models import Proveedor

from .forms import ProveedorServiciosCatalogoForm, ServicioCatalogoArchivoForm, ServicioCatalogoForm
from .models import ProveedorServicioCatalogo, ServicioCatalogo, ServicioCatalogoArchivo
from .services import (
    puede_gestionar_catalogo,
    puede_ver_catalogo,
    proveedores_disponibles_para_servicio,
    relaciones_proveedor_servicio_qs,
)


def _catalogo_context(request, empresa_slug):
    context = validar_slug_tenant(request, empresa_slug)
    empresa = context.empresa
    if not puede_ver_catalogo(request.user, empresa):
        raise PermissionDenied('No tienes permiso para consultar este catalogo.')
    return context


def _servicios_empresa(empresa):
    return ServicioCatalogo.objects.filter(empresa=empresa).prefetch_related('archivos')


def _proveedor_empresa(empresa, proveedor_id):
    return get_object_or_404(Proveedor.objects.select_related('empresa'), empresa=empresa, pk=proveedor_id)


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


@login_required(login_url='/login/')
def servicio_list(request, empresa_slug):
    context = _catalogo_context(request, empresa_slug)
    empresa = context.empresa
    servicios = _servicios_empresa(empresa)

    busqueda = (request.GET.get('q') or '').strip()
    categoria = request.GET.get('categoria') or ''
    estado = request.GET.get('estado') or ''
    if busqueda:
        servicios = servicios.filter(Q(nombre__icontains=busqueda) | Q(descripcion__icontains=busqueda))
    if categoria in dict(ServicioCatalogo.CATEGORIAS):
        servicios = servicios.filter(categoria=categoria)
    if estado == 'activo':
        servicios = servicios.filter(activo=True)
    elif estado == 'inactivo':
        servicios = servicios.filter(activo=False)

    paginator = Paginator(servicios, 12)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(
        request,
        'catalogo/servicio_list.html',
        _template_context(
            request,
            empresa,
            page_obj=page_obj,
            servicios=page_obj.object_list,
            categorias=ServicioCatalogo.CATEGORIAS,
            estado=estado,
            categoria=categoria,
            busqueda=busqueda,
            puede_gestionar=puede_gestionar_catalogo(request.user, empresa),
        ),
    )


@login_required(login_url='/login/')
def servicio_detail(request, empresa_slug, servicio_id):
    context = _catalogo_context(request, empresa_slug)
    empresa = context.empresa
    servicio = get_object_or_404(_servicios_empresa(empresa), pk=servicio_id)
    return render(
        request,
        'catalogo/servicio_detail.html',
        _template_context(
            request,
            empresa,
            servicio=servicio,
            archivos=servicio.archivos.all(),
            archivo_form=ServicioCatalogoArchivoForm(),
            proveedores_servicio=proveedores_disponibles_para_servicio(servicio),
            puede_gestionar=puede_gestionar_catalogo(request.user, empresa),
        ),
    )


@login_required(login_url='/login/')
def servicio_create(request, empresa_slug):
    context = _catalogo_context(request, empresa_slug)
    empresa = context.empresa
    if not puede_gestionar_catalogo(request.user, empresa):
        raise PermissionDenied('No tienes permiso para crear servicios de catalogo.')
    form = ServicioCatalogoForm(request.POST or None, request.FILES or None, empresa=empresa)
    if request.method == 'POST' and form.is_valid():
        servicio = form.save()
        messages.success(request, 'Servicio agregado al catalogo.')
        return redirect('catalogo_servicio_detail', empresa_slug=empresa.slug, servicio_id=servicio.id)
    return render(request, 'catalogo/servicio_form.html', _template_context(request, empresa, form=form, modo='crear'))


@login_required(login_url='/login/')
def servicio_update(request, empresa_slug, servicio_id):
    context = _catalogo_context(request, empresa_slug)
    empresa = context.empresa
    if not puede_gestionar_catalogo(request.user, empresa):
        raise PermissionDenied('No tienes permiso para editar servicios de catalogo.')
    servicio = get_object_or_404(_servicios_empresa(empresa), pk=servicio_id)
    form = ServicioCatalogoForm(request.POST or None, request.FILES or None, instance=servicio, empresa=empresa)
    if request.method == 'POST' and form.is_valid():
        servicio = form.save()
        messages.success(request, 'Servicio de catalogo actualizado.')
        return redirect('catalogo_servicio_detail', empresa_slug=empresa.slug, servicio_id=servicio.id)
    return render(
        request,
        'catalogo/servicio_form.html',
        _template_context(request, empresa, form=form, servicio=servicio, modo='editar'),
    )


@login_required(login_url='/login/')
@require_POST
def servicio_toggle(request, empresa_slug, servicio_id):
    context = _catalogo_context(request, empresa_slug)
    empresa = context.empresa
    if not puede_gestionar_catalogo(request.user, empresa):
        raise PermissionDenied('No tienes permiso para cambiar el estado del catalogo.')
    servicio = get_object_or_404(_servicios_empresa(empresa), pk=servicio_id)
    servicio.activo = not servicio.activo
    servicio.save(update_fields=['activo', 'updated_at'])
    messages.success(request, 'Servicio activado.' if servicio.activo else 'Servicio desactivado.')
    return redirect('catalogo_servicio_detail', empresa_slug=empresa.slug, servicio_id=servicio.id)


@login_required(login_url='/login/')
@require_POST
def archivo_create(request, empresa_slug, servicio_id):
    context = _catalogo_context(request, empresa_slug)
    empresa = context.empresa
    if not puede_gestionar_catalogo(request.user, empresa):
        raise PermissionDenied('No tienes permiso para agregar archivos al catalogo.')
    servicio = get_object_or_404(_servicios_empresa(empresa), pk=servicio_id)
    form = ServicioCatalogoArchivoForm(request.POST, request.FILES)
    if form.is_valid():
        archivo = form.save(commit=False)
        archivo.servicio = servicio
        try:
            archivo.full_clean()
            archivo.save()
            messages.success(request, 'Archivo agregado al servicio.')
        except ValidationError as exc:
            form.add_error(None, exc)
            messages.error(request, 'No se pudo agregar el archivo. Verifica tipo y formato.')
    else:
        messages.error(request, 'No se pudo agregar el archivo. Verifica tipo y formato.')
    return redirect('catalogo_servicio_detail', empresa_slug=empresa.slug, servicio_id=servicio.id)


@login_required(login_url='/login/')
def servicio_imagen(request, empresa_slug, servicio_id):
    context = _catalogo_context(request, empresa_slug)
    servicio = get_object_or_404(_servicios_empresa(context.empresa), pk=servicio_id)
    return _file_response(servicio.imagen_principal)


@login_required(login_url='/login/')
def archivo_download(request, empresa_slug, servicio_id, archivo_id):
    context = _catalogo_context(request, empresa_slug)
    servicio = get_object_or_404(_servicios_empresa(context.empresa), pk=servicio_id)
    archivo = get_object_or_404(ServicioCatalogoArchivo, pk=archivo_id, servicio=servicio)
    return _file_response(archivo.archivo)


@login_required(login_url='/login/')
def proveedor_servicios(request, empresa_slug, proveedor_id):
    context = _catalogo_context(request, empresa_slug)
    empresa = context.empresa
    proveedor = _proveedor_empresa(empresa, proveedor_id)
    puede_gestionar = puede_gestionar_catalogo(request.user, empresa)

    if request.method == 'POST':
        if not puede_gestionar:
            raise PermissionDenied('No tienes permiso para modificar servicios del proveedor.')
        form = ProveedorServiciosCatalogoForm(request.POST, proveedor=proveedor)
        if form.is_valid():
            notas = form.cleaned_data.get('notas') or ''
            total = 0
            for servicio in form.cleaned_data['servicios']:
                relacion, _ = ProveedorServicioCatalogo.objects.update_or_create(
                    proveedor=proveedor,
                    servicio_catalogo=servicio,
                    defaults={'activo': True, 'notas': notas},
                )
                relacion.full_clean()
                total += 1
            messages.success(request, f'Servicios asociados: {total}.')
            return redirect('catalogo_proveedor_servicios', empresa_slug=empresa.slug, proveedor_id=proveedor.id)
    else:
        form = ProveedorServiciosCatalogoForm(proveedor=proveedor)

    relaciones = relaciones_proveedor_servicio_qs(empresa).filter(proveedor=proveedor)
    busqueda = (request.GET.get('q') or '').strip()
    if busqueda:
        relaciones = relaciones.filter(
            Q(servicio_catalogo__nombre__icontains=busqueda)
            | Q(servicio_catalogo__descripcion__icontains=busqueda)
            | Q(notas__icontains=busqueda)
        )

    return render(
        request,
        'catalogo/proveedor_servicios.html',
        _template_context(
            request,
            empresa,
            proveedor=proveedor,
            relaciones=relaciones,
            form=form,
            busqueda=busqueda,
            puede_gestionar=puede_gestionar,
        ),
    )


@login_required(login_url='/login/')
@require_POST
def proveedor_servicio_toggle(request, empresa_slug, proveedor_id, relacion_id):
    context = _catalogo_context(request, empresa_slug)
    empresa = context.empresa
    if not puede_gestionar_catalogo(request.user, empresa):
        raise PermissionDenied('No tienes permiso para cambiar servicios del proveedor.')
    proveedor = _proveedor_empresa(empresa, proveedor_id)
    relacion = get_object_or_404(relaciones_proveedor_servicio_qs(empresa), proveedor=proveedor, pk=relacion_id)
    relacion.activo = not relacion.activo
    relacion.save(update_fields=['activo', 'updated_at'])
    messages.success(request, 'Relacion activada.' if relacion.activo else 'Relacion desactivada.')
    return redirect('catalogo_proveedor_servicios', empresa_slug=empresa.slug, proveedor_id=proveedor.id)
