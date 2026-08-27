from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from catalogo.models import ProveedorServicioCatalogo, ServicioCatalogo
from core.services.app_context import build_app_context
from core.services.authorization import Actions, usuario_tiene_permiso
from core.services.limites_plan import (
    LimitePlanExcedido,
    resumen_uso_plan,
    validar_limite_clientes,
    validar_limite_planners,
    validar_limite_usuarios,
)
from core.services.permisos import roles_usuario_empresa
from core.services.tenant_context import validar_slug_tenant
from invitaciones.company_user_services import (
    actualizar_usuario_empresa_dashboard,
    crear_o_actualizar_usuario_empresa,
    desactivar_usuario_empresa_dashboard,
    eliminar_usuario_empresa_dashboard,
)
from invitaciones.models import EventoBoda
from invitaciones.shared_dashboard_services import limpiar_texto
from invitaciones.views import (
    actualizar_proveedor_empresa_dashboard,
    crear_cliente_empresa_dashboard,
    eliminar_proveedor_empresa_dashboard,
    sincronizar_acceso_proveedor,
    usuario_empresa_existente_activo,
)
from organizaciones.models import MembresiaEmpresa, SedeEvento
from proveedores.models import Proveedor, ServicioEvento


COMPANY_ROLES = {"ADMIN_EMPRESA", "VENTAS"}
TEAM_ROLES = {"ADMIN_EMPRESA", "VENTAS", "WEDDING_PLANNER"}


def _company_context(request, empresa_slug, *, active_key, page_title):
    tenant = validar_slug_tenant(request, empresa_slug, roles=COMPANY_ROLES)
    empresa = tenant.empresa
    context = build_app_context(
        request,
        empresa=empresa,
        page_title=page_title,
        section_label=empresa.nombre_comercial,
        active_key=active_key,
    )
    context.update(
        {
            "roles_usuario_actual": roles_usuario_empresa(request.user, empresa),
            "puede_usuarios": usuario_tiene_permiso(
                request.user,
                Actions.COMPANY_MANAGE_USERS,
                empresa=empresa,
            ),
            "puede_catalogos": usuario_tiene_permiso(
                request.user,
                Actions.COMPANY_MANAGE_CATALOGS,
                empresa=empresa,
            ),
        }
    )
    return empresa, context


def _redirect_to(name, empresa):
    return redirect(reverse(name, kwargs={"empresa_slug": empresa.slug}))


def _limit_error(request, exc):
    messages.error(request, str(exc))


def _validar_password_acceso(request, *, requerido=False):
    """
    New company accounts must receive a known password.
    Existing accounts keep their current password when both fields are blank.
    """
    password = (request.POST.get("password_usuario") or "").strip()
    confirmar = (request.POST.get("password_usuario_confirmar") or "").strip()

    if requerido and not password:
        messages.error(request, "Define una contraseña para la nueva cuenta.")
        return False

    if not password and not confirmar:
        return True

    if len(password) < 8:
        messages.error(request, "La contraseña debe tener al menos 8 caracteres.")
        return False

    if password != confirmar:
        messages.error(request, "La confirmación de contraseña no coincide.")
        return False

    return True


def _eventos_empresa(empresa):
    return EventoBoda.objects.filter(empresa=empresa).select_related("sede", "wedding_planner")


@login_required(login_url="/login/")
def company_clientes(request, empresa_slug):
    empresa, context = _company_context(
        request,
        empresa_slug,
        active_key="clientes",
        page_title="Clientes",
    )

    if request.method == "POST":
        if not context["puede_usuarios"]:
            raise PermissionDenied("No tienes permiso para gestionar clientes.")
        accion = request.POST.get("accion")
        if accion == "crear_cliente":
            username = limpiar_texto(request, "username_usuario")
            if not _validar_password_acceso(request, requerido=True):
                return _redirect_to("empresa_clientes", empresa)
            try:
                if not usuario_empresa_existente_activo(empresa, username):
                    validar_limite_usuarios(empresa)
                if not usuario_empresa_existente_activo(empresa, username, "CLIENTE"):
                    validar_limite_clientes(empresa)
            except LimitePlanExcedido as exc:
                _limit_error(request, exc)
            else:
                crear_cliente_empresa_dashboard(request, empresa)
        elif accion == "editar_usuario_empresa":
            if not _validar_password_acceso(request, requerido=False):
                return _redirect_to("empresa_clientes", empresa)
            actualizar_usuario_empresa_dashboard(request, empresa)
        elif accion == "desactivar_usuario_empresa":
            desactivar_usuario_empresa_dashboard(request, empresa)
        elif accion == "eliminar_usuario_empresa":
            eliminar_usuario_empresa_dashboard(request, empresa)
        return _redirect_to("empresa_clientes", empresa)

    clientes = (
        MembresiaEmpresa.objects.filter(empresa=empresa, rol="CLIENTE")
        .select_related("usuario")
        .annotate(
            eventos_count=Count(
                "usuario__eventos_cliente",
                filter=Q(usuario__eventos_cliente__empresa=empresa),
                distinct=True,
            )
        )
        .order_by("-activo", "usuario__first_name", "usuario__username")
    )
    busqueda = (request.GET.get("q") or "").strip()
    if busqueda:
        clientes = clientes.filter(
            Q(usuario__username__icontains=busqueda)
            | Q(usuario__first_name__icontains=busqueda)
            | Q(usuario__last_name__icontains=busqueda)
            | Q(usuario__email__icontains=busqueda)
        )

    context.update(
        {
            "clientes": clientes,
            "busqueda": busqueda,
            "eventos_activos": _eventos_empresa(empresa).filter(activo=True).order_by("-fecha_inicio"),
        }
    )
    return render(request, "eventos/company_workspace/clientes.html", context)


@login_required(login_url="/login/")
def company_equipo(request, empresa_slug):
    empresa, context = _company_context(
        request,
        empresa_slug,
        active_key="equipo",
        page_title="Equipo",
    )

    if request.method == "POST":
        if not context["puede_usuarios"]:
            raise PermissionDenied("No tienes permiso para gestionar equipo.")
        accion = request.POST.get("accion")
        if accion == "crear_planner":
            username = limpiar_texto(request, "username_usuario")
            if not _validar_password_acceso(request, requerido=True):
                return _redirect_to("empresa_equipo", empresa)
            rol = request.POST.get("rol_usuario") or "WEDDING_PLANNER"
            try:
                if not usuario_empresa_existente_activo(empresa, username):
                    validar_limite_usuarios(empresa)
                if rol == "WEDDING_PLANNER" and not usuario_empresa_existente_activo(
                    empresa,
                    username,
                    "WEDDING_PLANNER",
                ):
                    validar_limite_planners(empresa)
            except LimitePlanExcedido as exc:
                _limit_error(request, exc)
            else:
                crear_o_actualizar_usuario_empresa(request, empresa, "WEDDING_PLANNER")
        elif accion == "editar_usuario_empresa":
            if not _validar_password_acceso(request, requerido=False):
                return _redirect_to("empresa_equipo", empresa)
            actualizar_usuario_empresa_dashboard(request, empresa)
        elif accion == "desactivar_usuario_empresa":
            desactivar_usuario_empresa_dashboard(request, empresa)
        elif accion == "eliminar_usuario_empresa":
            eliminar_usuario_empresa_dashboard(request, empresa)
        return _redirect_to("empresa_equipo", empresa)

    membresias = (
        MembresiaEmpresa.objects.filter(empresa=empresa, rol__in=TEAM_ROLES)
        .select_related("usuario")
        .annotate(
            eventos_planeados_count=Count(
                "usuario__eventos_planeados",
                filter=Q(usuario__eventos_planeados__empresa=empresa),
                distinct=True,
            )
        )
        .order_by("-activo", "rol", "usuario__first_name", "usuario__username")
    )
    busqueda = (request.GET.get("q") or "").strip()
    if busqueda:
        membresias = membresias.filter(
            Q(usuario__username__icontains=busqueda)
            | Q(usuario__first_name__icontains=busqueda)
            | Q(usuario__last_name__icontains=busqueda)
            | Q(usuario__email__icontains=busqueda)
            | Q(rol__icontains=busqueda)
        )

    context.update(
        {
            "membresias_equipo": membresias,
            "roles_equipo": [item for item in MembresiaEmpresa.ROLES if item[0] in TEAM_ROLES],
            "busqueda": busqueda,
        }
    )
    return render(request, "eventos/company_workspace/equipo.html", context)


@login_required(login_url="/login/")
def company_proveedores(request, empresa_slug):
    empresa, context = _company_context(
        request,
        empresa_slug,
        active_key="proveedores",
        page_title="Proveedores",
    )

    if request.method == "POST":
        if not context["puede_catalogos"]:
            raise PermissionDenied("No tienes permiso para gestionar proveedores.")
        accion = request.POST.get("accion")
        if accion == "crear_proveedor":
            nombre = limpiar_texto(request, "nombre_proveedor")
            username_portal = limpiar_texto(request, "username_usuario")
            if username_portal and not _validar_password_acceso(request, requerido=True):
                return _redirect_to("empresa_proveedores", empresa)
            if nombre:
                proveedor = Proveedor.objects.create(
                    empresa=empresa,
                    nombre_comercial=nombre,
                    tipo_proveedor=request.POST.get("tipo_proveedor") or "OTROS",
                    nombre_contacto=limpiar_texto(request, "contacto_proveedor"),
                    telefono=limpiar_texto(request, "telefono_proveedor"),
                    correo=limpiar_texto(request, "correo_proveedor"),
                    contacto_operativo=limpiar_texto(request, "contacto_operativo_proveedor"),
                    telefono_operativo=limpiar_texto(request, "telefono_operativo_proveedor"),
                    correo_operativo=limpiar_texto(request, "correo_operativo_proveedor"),
                    visible_para_wedding_planners=(
                        request.POST.get("visible_wedding_planners_proveedor", "on") == "on"
                    ),
                    rfc=limpiar_texto(request, "rfc_proveedor"),
                    datos_bancarios=limpiar_texto(request, "datos_bancarios_proveedor"),
                    notas_privadas=limpiar_texto(request, "notas_privadas_proveedor"),
                    activo=True,
                )
                sincronizar_acceso_proveedor(request, empresa, proveedor)
        elif accion == "editar_proveedor":
            if not _validar_password_acceso(request, requerido=False):
                return _redirect_to("empresa_proveedores", empresa)
            actualizar_proveedor_empresa_dashboard(request, empresa)
        elif accion == "desactivar_proveedor":
            proveedor = get_object_or_404(
                Proveedor,
                empresa=empresa,
                id=request.POST.get("proveedor_id"),
            )
            proveedor.activo = False
            proveedor.save(update_fields=["activo"])
        elif accion == "eliminar_proveedor":
            eliminar_proveedor_empresa_dashboard(request, empresa)
        return _redirect_to("empresa_proveedores", empresa)

    proveedores = (
        Proveedor.objects.filter(empresa=empresa)
        .select_related("usuario")
        .annotate(
            servicios_evento_count=Count("servicios_evento", distinct=True),
            servicios_catalogo_count=Count("servicios_catalogo_k9", distinct=True),
        )
        .order_by("-activo", "nombre_comercial")
    )
    busqueda = (request.GET.get("q") or "").strip()
    if busqueda:
        proveedores = proveedores.filter(
            Q(nombre_comercial__icontains=busqueda)
            | Q(nombre_contacto__icontains=busqueda)
            | Q(contacto_operativo__icontains=busqueda)
            | Q(correo__icontains=busqueda)
            | Q(telefono__icontains=busqueda)
        )

    context.update(
        {
            "proveedores": proveedores,
            "tipos_proveedor": Proveedor.TIPOS,
            "busqueda": busqueda,
        }
    )
    return render(request, "eventos/company_workspace/proveedores.html", context)


@login_required(login_url="/login/")
def company_configuracion(request, empresa_slug):
    empresa, context = _company_context(
        request,
        empresa_slug,
        active_key="configuracion",
        page_title="Configuracion",
    )

    eventos = _eventos_empresa(empresa)
    context.update(
        {
            "uso_plan": resumen_uso_plan(empresa),
            "sedes": SedeEvento.objects.filter(empresa=empresa).order_by("-activa", "nombre"),
            "membresias": MembresiaEmpresa.objects.filter(empresa=empresa).select_related("usuario"),
            "proveedores_count": Proveedor.objects.filter(empresa=empresa).count(),
            "catalogo_count": ServicioCatalogo.objects.filter(empresa=empresa).count(),
            "relaciones_catalogo_count": ProveedorServicioCatalogo.objects.filter(
                proveedor__empresa=empresa,
                servicio_catalogo__empresa=empresa,
            ).count(),
            "servicios_evento_count": ServicioEvento.objects.filter(evento__empresa=empresa).count(),
            "eventos_activos_count": eventos.exclude(
                estado__in={"ARCHIVADO", "CANCELADO", "FINALIZADO"}
            ).count(),
        }
    )
    return render(request, "eventos/company_workspace/configuracion.html", context)
