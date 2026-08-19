from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from django.urls import reverse

from core.services.app_context import build_app_context
from core.services.authorization import Actions, usuario_puede_evento, usuario_tiene_permiso
from core.services.permisos import roles_usuario_empresa, usuario_es_dirtec_operativo
from core.services.tenant_context import validar_slug_tenant
from core.services.return_context import request_return_to, safe_return_to
from invitaciones.models import EventoBoda

from .event_domain import (
    actualizar_datos_evento_generico,
    archivar_evento,
    cancelar_evento,
    crear_evento_generico,
    eliminar_evento_error,
    evaluar_eliminacion_evento,
    finalizar_evento,
    purgar_evento_archivado,
    restaurar_evento,
    usuario_puede_purgar_evento,
)
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


def _return_context(request, empresa, *, default=None):
    return request_return_to(
        request,
        empresa=empresa,
        default=default,
    )


def _url_with_return(url, return_to):
    from urllib.parse import urlencode
    if not return_to:
        return url
    separator = "&" if "?" in url else "?"
    return f"{url}{separator}{urlencode({'return_to': return_to})}"


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

    return_to = _return_context(request, empresa)
    context = _app_context(request, empresa, title="Eventos")
    context.update(
        {
            "eventos": qs,
            "estado_filtro": estado,
            "busqueda": q,
            "puede_crear": usuario_tiene_permiso(request.user, Actions.EVENT_CREATE, empresa=empresa),
            "return_to": return_to,
        }
    )
    return render(request, "eventos/workspace/evento_list.html", context)


@login_required(login_url="/login/")
def evento_create(request, empresa_slug):
    tenant, _roles = _contexto_empresa(request, empresa_slug)
    empresa = tenant.empresa
    return_to = _return_context(request, empresa)

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
            destino = reverse(
                "k9_evento_resumen",
                kwargs={"empresa_slug": empresa.slug, "evento_id": evento.id},
            )
            return redirect(_url_with_return(destino, return_to))

    context = _app_context(request, empresa, title="Nuevo evento")
    context.update(
        {
            "form": form,
            "modo": "crear",
            "cancel_url": return_to,
            "return_to": return_to,
        }
    )
    return render(request, "eventos/workspace/evento_form.html", context)


@login_required(login_url="/login/")
def evento_resumen(request, empresa_slug, evento_id):
    tenant, _roles = _contexto_empresa(request, empresa_slug)
    empresa = tenant.empresa
    evento = _evento_visible(request.user, empresa, evento_id)
    return_to = _return_context(request, empresa)

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
            "return_to": return_to,
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
    return_to = _return_context(request, empresa)

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
            destino = reverse(
                "k9_evento_datos",
                kwargs={"empresa_slug": empresa.slug, "evento_id": evento.id},
            )
            return redirect(_url_with_return(destino, return_to))

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
            "cancel_url": _url_with_return(
                reverse(
                    "k9_evento_resumen",
                    kwargs={"empresa_slug": empresa.slug, "evento_id": evento.id},
                ),
                return_to,
            ),
            "return_to": return_to,
        }
    )
    return render(request, "eventos/workspace/evento_form.html", context)


@login_required(login_url="/login/")
def evento_configuracion(request, empresa_slug, evento_id):
    tenant, _roles = _contexto_empresa(request, empresa_slug)
    empresa = tenant.empresa
    evento = _evento_visible(request.user, empresa, evento_id)
    return_to = _return_context(request, empresa)

    evaluacion = evaluar_eliminacion_evento(evento)
    context = _app_context(
        request,
        empresa,
        title=evento.titulo_evento,
        section="Event Workspace",
    )
    context.update(
        {
            "evento": evento,
            "workspace_active": "configuracion",
            "puede_editar": usuario_puede_evento(request.user, evento, Actions.EVENT_EDIT),
            "puede_eliminar_error": evaluacion.permitido
                and usuario_puede_evento(request.user, evento, Actions.EVENT_EDIT),
            "evaluacion_eliminacion": evaluacion,
            "puede_purgar": usuario_puede_purgar_evento(request.user, evento),
            "return_to": return_to,
        }
    )
    return render(request, "eventos/workspace/configuracion.html", context)


@require_POST
@login_required(login_url="/login/")
def evento_finalizar(request, empresa_slug, evento_id):
    tenant, _roles = _contexto_empresa(request, empresa_slug)
    evento = _evento_visible(request.user, tenant.empresa, evento_id, action=Actions.EVENT_EDIT)
    try:
        finalizar_evento(evento, usuario=request.user, request=request)
    except ValidationError as exc:
        messages.error(request, " ".join(exc.messages))
    else:
        messages.success(request, "Evento finalizado. El historial permanece disponible.")
    destino = reverse(
        "k9_evento_configuracion",
        kwargs={"empresa_slug": tenant.empresa.slug, "evento_id": evento.id},
    )
    return redirect(_url_with_return(destino, _return_context(request, tenant.empresa)))


@require_POST
@login_required(login_url="/login/")
def evento_cancelar(request, empresa_slug, evento_id):
    tenant, _roles = _contexto_empresa(request, empresa_slug)
    evento = _evento_visible(request.user, tenant.empresa, evento_id, action=Actions.EVENT_EDIT)
    try:
        cancelar_evento(
            evento,
            usuario=request.user,
            motivo=request.POST.get("motivo", ""),
            request=request,
        )
    except ValidationError as exc:
        messages.error(request, " ".join(exc.messages))
    else:
        messages.success(request, "Evento cancelado. No se eliminó ningún historial.")
    destino = reverse(
        "k9_evento_configuracion",
        kwargs={"empresa_slug": tenant.empresa.slug, "evento_id": evento.id},
    )
    return redirect(_url_with_return(destino, _return_context(request, tenant.empresa)))


@require_POST
@login_required(login_url="/login/")
def evento_archivar(request, empresa_slug, evento_id):
    tenant, _roles = _contexto_empresa(request, empresa_slug)
    evento = _evento_visible(request.user, tenant.empresa, evento_id, action=Actions.EVENT_EDIT)
    archivar_evento(evento, usuario=request.user, request=request)
    messages.success(request, "Evento archivado.")
    destino = reverse(
        "k9_evento_configuracion",
        kwargs={"empresa_slug": tenant.empresa.slug, "evento_id": evento.id},
    )
    return redirect(_url_with_return(destino, _return_context(request, tenant.empresa)))


@require_POST
@login_required(login_url="/login/")
def evento_restaurar(request, empresa_slug, evento_id):
    tenant, _roles = _contexto_empresa(request, empresa_slug)
    evento = _evento_visible(request.user, tenant.empresa, evento_id, action=Actions.EVENT_EDIT)
    restaurar_evento(evento, usuario=request.user, request=request)
    messages.success(request, "Evento restaurado.")
    destino = reverse(
        "k9_evento_configuracion",
        kwargs={"empresa_slug": tenant.empresa.slug, "evento_id": evento.id},
    )
    return redirect(_url_with_return(destino, _return_context(request, tenant.empresa)))


@require_POST
@login_required(login_url="/login/")
def evento_eliminar_error(request, empresa_slug, evento_id):
    tenant, _roles = _contexto_empresa(request, empresa_slug)
    evento = _evento_visible(request.user, tenant.empresa, evento_id, action=Actions.EVENT_EDIT)

    if (request.POST.get("confirmacion") or "").strip().upper() != "ELIMINAR":
        messages.error(request, 'Escribe ELIMINAR para confirmar.')
        destino = reverse(
            "k9_evento_configuracion",
            kwargs={"empresa_slug": tenant.empresa.slug, "evento_id": evento.id},
        )
        return redirect(_url_with_return(destino, _return_context(request, tenant.empresa)))

    try:
        eliminado = eliminar_evento_error(evento, usuario=request.user, request=request)
    except ValidationError as exc:
        messages.error(request, " ".join(exc.messages))
        destino = reverse(
            "k9_evento_configuracion",
            kwargs={"empresa_slug": tenant.empresa.slug, "evento_id": evento.id},
        )
        return redirect(_url_with_return(destino, _return_context(request, tenant.empresa)))

    messages.success(request, f'Evento "{eliminado["nombre"]}" eliminado porque no tenía historial protegido.')
    return redirect(_return_context(request, tenant.empresa))


@require_POST
@login_required(login_url="/login/")
def evento_purgar(request, empresa_slug, evento_id):
    tenant, _roles = _contexto_empresa(request, empresa_slug)
    evento = _evento_visible(request.user, tenant.empresa, evento_id)

    if (request.POST.get("confirmacion") or "").strip().upper() != "PURGAR":
        messages.error(request, 'Escribe PURGAR para confirmar.')
        destino = reverse(
            "k9_evento_configuracion",
            kwargs={"empresa_slug": tenant.empresa.slug, "evento_id": evento.id},
        )
        return redirect(_url_with_return(destino, _return_context(request, tenant.empresa)))

    try:
        eliminado = purgar_evento_archivado(evento, usuario=request.user, request=request)
    except (ValidationError, PermissionDenied) as exc:
        if isinstance(exc, ValidationError):
            messages.error(request, " ".join(exc.messages))
        else:
            raise
        destino = reverse(
            "k9_evento_configuracion",
            kwargs={"empresa_slug": tenant.empresa.slug, "evento_id": evento.id},
        )
        return redirect(_url_with_return(destino, _return_context(request, tenant.empresa)))

    messages.success(request, f'Evento "{eliminado["nombre"]}" purgado permanentemente.')
    return redirect(_return_context(request, tenant.empresa))
