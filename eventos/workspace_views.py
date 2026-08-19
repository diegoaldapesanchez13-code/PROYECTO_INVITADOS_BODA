from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from core.services.app_context import build_app_context
from core.services.authorization import Actions, usuario_puede_evento, usuario_tiene_permiso
from core.services.permisos import roles_usuario_empresa, usuario_es_dirtec_operativo
from core.services.tenant_context import validar_slug_tenant
from invitaciones.models import EventoBoda

from .event_domain import crear_evento_generico, actualizar_datos_evento_generico
from .forms import EventoCreateForm, EventoEditForm


BACKOFFICE_ROLES = {"ADMIN_EMPRESA", "VENTAS", "WEDDING_PLANNER"}


def _contexto_empresa(request, empresa_slug):
    tenant = validar_slug_tenant(request, empresa_slug)
    roles = roles_usuario_empresa(request.user, tenant.empresa)
    if not tenant.es_dirtec and not roles.intersection(BACKOFFICE_ROLES):
        raise PermissionDenied("No tienes acceso al espacio de gestión de eventos.")
    return tenant, roles


def _eventos_visibles(user, empresa, roles):
    qs = EventoBoda.objects.filter(empresa=empresa).select_related(
        "empresa",
        "sede",
        "wedding_planner",
    ).prefetch_related("clientes")

    if usuario_es_dirtec_operativo(user) or roles.intersection({"ADMIN_EMPRESA", "VENTAS"}):
        return qs
    if "WEDDING_PLANNER" in roles:
        return qs.filter(wedding_planner=user)
    return qs.none()


def _evento_visible(user, empresa, evento_id, *, action=Actions.EVENT_VIEW):
    evento = get_object_or_404(
        EventoBoda.objects.select_related("empresa", "sede", "wedding_planner").prefetch_related("clientes"),
        empresa=empresa,
        pk=evento_id,
    )
    if not usuario_puede_evento(user, evento, action):
        raise PermissionDenied("No tienes permiso para acceder a este evento.")
    return evento


def _app_context(request, empresa, *, title, section="Eventos"):
    return build_app_context(
        request,
        empresa=empresa,
        page_title=title,
        section_label=section,
        active_key="eventos",
    )


@login_required(login_url="/login/")
def evento_list(request, empresa_slug):
    tenant, roles = _contexto_empresa(request, empresa_slug)
    empresa = tenant.empresa

    qs = _eventos_visibles(request.user, empresa, roles)

    estado = (request.GET.get("estado") or "ACTIVOS").strip().upper()
    q = (request.GET.get("q") or "").strip()

    if estado == "ARCHIVADOS":
        qs = qs.filter(estado="ARCHIVADO")
    elif estado == "CANCELADOS":
        qs = qs.filter(estado="CANCELADO")
    elif estado == "FINALIZADOS":
        qs = qs.filter(estado="FINALIZADO")
    elif estado == "BORRADORES":
        qs = qs.filter(estado="BORRADOR")
    else:
        qs = qs.exclude(estado__in={"ARCHIVADO", "CANCELADO", "FINALIZADO"})

    if q:
        qs = qs.filter(
            Q(nombre_evento__icontains=q)
            | Q(nombre_principal__icontains=q)
            | Q(nombre_secundario__icontains=q)
        )

    qs = qs.order_by("fecha_inicio", "-fecha_creacion")

    context = _app_context(request, empresa, title="Eventos")
    context.update(
        {
            "eventos": qs,
            "estado_filtro": estado,
            "busqueda": q,
            "puede_crear": usuario_tiene_permiso(request.user, Actions.EVENT_CREATE, empresa=empresa),
        }
    )
    return render(request, "eventos/workspace/evento_list.html", context)


@login_required(login_url="/login/")
def evento_create(request, empresa_slug):
    tenant, _roles = _contexto_empresa(request, empresa_slug)
    empresa = tenant.empresa

    if not usuario_tiene_permiso(request.user, Actions.EVENT_CREATE, empresa=empresa):
        raise PermissionDenied("No tienes permiso para crear eventos.")

    form = EventoCreateForm(
        request.POST or None,
        empresa=empresa,
        user=request.user,
    )

    if request.method == "POST" and form.is_valid():
        try:
            evento = crear_evento_generico(
                empresa=empresa,
                usuario=request.user,
                nombre_evento=form.cleaned_data["nombre_evento"],
                tipo_evento=form.cleaned_data.get("tipo_evento") or "OTRO",
                fecha_inicio=form.cleaned_data.get("fecha_inicio"),
                fecha_fin=form.cleaned_data.get("fecha_fin"),
                cliente=form.cleaned_data.get("cliente"),
                planner=form.cleaned_data.get("planner"),
                sede=form.cleaned_data.get("sede"),
                request=request,
            )
        except ValidationError as exc:
            form.add_error(None, exc)
        else:
            messages.success(request, "Evento creado. Puedes completar los datos cuando los tengas.")
            return redirect(
                "k9_evento_resumen",
                empresa_slug=empresa.slug,
                evento_id=evento.id,
            )

    context = _app_context(request, empresa, title="Nuevo evento")
    context.update(
        {
            "form": form,
            "modo": "crear",
            "cancel_url": reverse("k9_evento_list", kwargs={"empresa_slug": empresa.slug}),
        }
    )
    return render(request, "eventos/workspace/evento_form.html", context)


@login_required(login_url="/login/")
def evento_resumen(request, empresa_slug, evento_id):
    tenant, _roles = _contexto_empresa(request, empresa_slug)
    empresa = tenant.empresa
    evento = _evento_visible(request.user, empresa, evento_id)

    context = _app_context(
        request,
        empresa,
        title=evento.titulo_evento,
        section="Event Workspace",
    )
    context.update(
        {
            "evento": evento,
            "workspace_active": "resumen",
            "puede_editar": usuario_puede_evento(request.user, evento, Actions.EVENT_EDIT),
        }
    )
    return render(request, "eventos/workspace/resumen.html", context)


@login_required(login_url="/login/")
def evento_datos(request, empresa_slug, evento_id):
    tenant, _roles = _contexto_empresa(request, empresa_slug)
    empresa = tenant.empresa
    evento = _evento_visible(
        request.user,
        empresa,
        evento_id,
        action=Actions.EVENT_EDIT,
    )

    form = EventoEditForm(
        request.POST or None,
        evento=evento,
        empresa=empresa,
        user=request.user,
    )

    if request.method == "POST" and form.is_valid():
        try:
            actualizar_datos_evento_generico(
                evento,
                usuario=request.user,
                nombre_evento=form.cleaned_data["nombre_evento"],
                tipo_evento=form.cleaned_data.get("tipo_evento") or "OTRO",
                fecha_inicio=form.cleaned_data.get("fecha_inicio"),
                fecha_fin=form.cleaned_data.get("fecha_fin"),
                sede_marker=True,
                sede=form.cleaned_data.get("sede"),
                planner_marker=True,
                planner=form.cleaned_data.get("planner"),
                cliente_marker=True,
                cliente=form.cleaned_data.get("cliente"),
                request=request,
            )
        except ValidationError as exc:
            form.add_error(None, exc)
        else:
            messages.success(request, "Datos del evento actualizados.")
            # Regla K9: guardar conserva el contexto exacto del módulo Datos.
            return redirect(
                "k9_evento_datos",
                empresa_slug=empresa.slug,
                evento_id=evento.id,
            )

    context = _app_context(
        request,
        empresa,
        title=evento.titulo_evento,
        section="Event Workspace",
    )
    context.update(
        {
            "evento": evento,
            "form": form,
            "modo": "editar",
            "workspace_active": "datos",
            "cancel_url": reverse(
                "k9_evento_resumen",
                kwargs={"empresa_slug": empresa.slug, "evento_id": evento.id},
            ),
        }
    )
    return render(request, "eventos/workspace/evento_form.html", context)
