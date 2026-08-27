from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.http import HttpResponse
from django.views.decorators.http import require_GET, require_POST
from core.services.permisos import usuario_es_dirtec_operativo

from auditoria.models import RegistroAuditoria
from django.urls import reverse

from core.services.app_context import build_app_context
from core.services.authorization import Actions, usuario_puede_evento, usuario_tiene_permiso
from core.services.permisos import roles_usuario_empresa, usuario_es_dirtec_operativo
from core.services.tenant_context import validar_slug_tenant
from core.services.return_context import request_return_to, safe_return_to
from invitaciones.models import DisenoInvitacion, EventoBoda, Grupoinvitacion
from invitaciones.rsvp_control import obtener_configuracion_rsvp
from invitaciones.guest_analytics import resumen_invitados_evento
from mesas.models import Mesa

from .event_domain import (
    actualizar_datos_evento_generico,
    archivar_evento,
    cancelar_evento,
    crear_evento_generico,
    eliminar_evento_error,
    evaluar_eliminacion_evento,
    evaluar_purga_evento,
    finalizar_evento,
    purgar_evento_archivado,
    restaurar_evento,
    usuario_puede_purgar_evento,
)
from .forms import EventoCreateForm, EventoEditForm
from .data_lifecycle import (
    autorizar_purga_historica,
    confirmar_respaldo_externo,
    evaluar_ciclo_datos_evento,
    ejecutar_purga_historica,
    generar_expediente_purge_ready,
    generar_expediente_estructurado,
)
from .models import ExpedienteHistoricoEvento
from .workspace_navigation import build_workspace_tabs
from .workspace_summary import construir_resumen_workspace


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


def _workspace_context(request, *, empresa, evento, active_key):
    return build_workspace_tabs(
        user=request.user,
        empresa=empresa,
        evento=evento,
        active_key=active_key,
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
            "base_template": "core/app/base.html",
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
            "workspace_navigation": _workspace_context(
                request,
                empresa=empresa,
                evento=evento,
                active_key="resumen",
            ),
        }
    )
    context.update(construir_resumen_workspace(evento=evento, user=request.user))
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
            "base_template": "eventos/workspace/base.html",
            "workspace_active": "datos",
            "cancel_url": _url_with_return(
                reverse(
                    "k9_evento_resumen",
                    kwargs={"empresa_slug": empresa.slug, "evento_id": evento.id},
                ),
                return_to,
            ),
            "return_to": return_to,
            "workspace_navigation": _workspace_context(
                request,
                empresa=empresa,
                evento=evento,
                active_key="datos",
            ),
        }
    )
    return render(request, "eventos/workspace/evento_form.html", context)


@login_required(login_url="/login/")
def evento_invitacion(request, empresa_slug, evento_id):
    """Centro operativo de invitación; Builder permanece como runtime especializado."""
    tenant, _roles = _contexto_empresa(request, empresa_slug)
    empresa = tenant.empresa
    evento = _evento_visible(request.user, empresa, evento_id)
    return_to = _return_context(request, empresa)

    grupos = list(
        Grupoinvitacion.objects
        .filter(evento=evento)
        .prefetch_related("invitados")
        .order_by("nombre_grupo", "id")
    )
    diseno = DisenoInvitacion.objects.filter(evento=evento).first()
    rsvp_config = obtener_configuracion_rsvp(evento)

    puede_builder = usuario_puede_evento(
        request.user,
        evento,
        Actions.EVENT_BUILDER,
    )
    publicado = bool(
        diseno
        and diseno.documento_builder_publicado
    )
    tiene_borrador = bool(
        diseno
        and diseno.documento_builder_borrador
    )

    total_personas = sum(
        len(list(grupo.invitados.all()))
        for grupo in grupos
    )
    grupos_preparados = sum(
        1
        for grupo in grupos
        if grupo.estado_envio != "PENDIENTE"
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
            "workspace_active": "invitacion",
            "puede_editar": usuario_puede_evento(
                request.user,
                evento,
                Actions.EVENT_EDIT,
            ),
            "puede_builder": puede_builder,
            "diseno": diseno,
            "publicado": publicado,
            "tiene_borrador": tiene_borrador,
            "grupos": grupos,
            "grupo_preview": grupos[0] if grupos else None,
            "total_personas": total_personas,
            "grupos_preparados": grupos_preparados,
            "rsvp_config": rsvp_config,
            "return_to": return_to,
            "workspace_navigation": _workspace_context(
                request,
                empresa=empresa,
                evento=evento,
                active_key="invitacion",
            ),
        }
    )
    return render(
        request,
        "eventos/workspace/invitacion.html",
        context,
    )


@login_required(login_url="/login/")
def evento_mesas(request, empresa_slug, evento_id):
    """Centro K9 para Mesas; el plano visual existente sigue siendo especializado."""
    tenant, _roles = _contexto_empresa(request, empresa_slug)
    empresa = tenant.empresa
    evento = _evento_visible(
        request.user,
        empresa,
        evento_id,
        action=Actions.EVENT_TABLES,
    )
    return_to = _return_context(request, empresa)

    mesas = list(
        Mesa.objects
        .filter(evento=evento)
        .select_related("mesero")
        .prefetch_related("asignaciones__invitado__grupo")
        .order_by("numero", "nombre")
    )

    capacidad_total = sum(mesa.capacidad for mesa in mesas)
    ocupados = sum(mesa.lugares_ocupados for mesa in mesas)
    disponibles = max(capacidad_total - ocupados, 0)
    mesas_excedidas = sum(1 for mesa in mesas if mesa.excedida)
    invitados_metricas = resumen_invitados_evento(
        evento,
        incluir_mesas=True,
    )

    from urllib.parse import urlencode
    k9_url = reverse(
        "k9_evento_mesas",
        kwargs={
            "empresa_slug": empresa.slug,
            "evento_id": evento.id,
        },
    )
    plano_url = (
        f"{reverse('mesas_visual')}?"
        + urlencode(
            {
                "evento": evento.id,
                "return_to": k9_url,
            }
        )
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
            "workspace_active": "mesas",
            "mesas": mesas,
            "total_mesas": len(mesas),
            "capacidad_total": capacidad_total,
            "lugares_ocupados": ocupados,
            "lugares_disponibles": disponibles,
            "mesas_excedidas": mesas_excedidas,
            "confirmados_sin_mesa": invitados_metricas[
                "confirmados_sin_mesa"
            ],
            "plano_url": plano_url,
            "return_to": return_to,
            "workspace_navigation": _workspace_context(
                request,
                empresa=empresa,
                evento=evento,
                active_key="mesas",
            ),
        }
    )
    return render(
        request,
        "eventos/workspace/mesas.html",
        context,
    )


@login_required(login_url="/login/")
@require_GET
def evento_actividad(request, empresa_slug, evento_id):
    """Historial de auditoría existente del evento, expuesto como superficie K9 de solo lectura."""
    tenant, _roles = _contexto_empresa(request, empresa_slug)
    empresa = tenant.empresa
    evento = _evento_visible(
        request.user,
        empresa,
        evento_id,
        action=Actions.EVENT_VIEW,
    )
    return_to = _return_context(request, empresa)

    registros = (
        RegistroAuditoria.objects
        .filter(empresa=empresa, evento=evento)
        .select_related("usuario")
    )

    q = (request.GET.get("q") or "").strip()
    modelo = (request.GET.get("modelo") or "").strip()
    accion = (request.GET.get("accion") or "").strip()

    if q:
        registros = registros.filter(
            Q(descripcion__icontains=q)
            | Q(accion__icontains=q)
            | Q(modelo__icontains=q)
            | Q(objeto_id__icontains=q)
            | Q(usuario__username__icontains=q)
            | Q(usuario__first_name__icontains=q)
            | Q(usuario__last_name__icontains=q)
        )
    if modelo:
        registros = registros.filter(modelo=modelo)
    if accion:
        registros = registros.filter(accion=accion)

    modelos = list(
        RegistroAuditoria.objects
        .filter(empresa=empresa, evento=evento)
        .exclude(modelo="")
        .values_list("modelo", flat=True)
        .distinct()
        .order_by("modelo")
    )
    acciones = list(
        RegistroAuditoria.objects
        .filter(empresa=empresa, evento=evento)
        .exclude(accion="")
        .values_list("accion", flat=True)
        .distinct()
        .order_by("accion")
    )

    total_registros = registros.count()
    registros = registros[:250]

    context = _app_context(
        request,
        empresa,
        title=evento.titulo_evento,
        section="Event Workspace",
    )
    context.update(
        {
            "evento": evento,
            "workspace_active": "actividad",
            "registros": registros,
            "total_registros": total_registros,
            "modelos_actividad": modelos,
            "acciones_actividad": acciones,
            "actividad_q": q,
            "actividad_modelo": modelo,
            "actividad_accion": accion,
            "return_to": return_to,
            "workspace_navigation": _workspace_context(
                request,
                empresa=empresa,
                evento=evento,
                active_key="actividad",
            ),
        }
    )
    return render(
        request,
        "eventos/workspace/actividad.html",
        context,
    )


@login_required(login_url="/login/")
def evento_configuracion(request, empresa_slug, evento_id):
    tenant, _roles = _contexto_empresa(request, empresa_slug)
    empresa = tenant.empresa
    evento = _evento_visible(request.user, empresa, evento_id)
    return_to = _return_context(request, empresa)

    evaluacion = evaluar_eliminacion_evento(evento)
    evaluacion_purga = evaluar_purga_evento(evento)
    ciclo_datos = evaluar_ciclo_datos_evento(evento)
    ultimo_expediente = ExpedienteHistoricoEvento.objects.filter(
        empresa=empresa,
        evento_id_snapshot=evento.id,
    ).order_by("-generado_en", "-id").first()
    expediente_purge_ready = ExpedienteHistoricoEvento.objects.filter(
        empresa=empresa,
        evento_id_snapshot=evento.id,
        formato="K9_D6_PURGE_READY_V3",
    ).order_by("-generado_en", "-id").first()
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
            "evaluacion_purga": evaluacion_purga,
            "ciclo_datos": ciclo_datos,
            "ultimo_expediente": ultimo_expediente,
            "expediente_purge_ready": expediente_purge_ready,
            "puede_exportar_expediente": ciclo_datos["exportable"]
                and usuario_puede_evento(request.user, evento, Actions.EVENT_EDIT),
            "puede_confirmar_respaldo": bool(ciclo_datos.get("expediente_para_retencion"))
                and usuario_puede_evento(request.user, evento, Actions.EVENT_EDIT),
            "puede_autorizar_purga_historica": usuario_es_dirtec_operativo(request.user),
            "puede_purgar": usuario_puede_purgar_evento(request.user, evento),
            "return_to": return_to,
            "workspace_navigation": _workspace_context(
                request,
                empresa=empresa,
                evento=evento,
                active_key="configuracion",
            ),
        }
    )
    return render(request, "eventos/workspace/configuracion.html", context)




@require_GET
@login_required(login_url="/login/")
def evento_exportar_expediente_purge_ready(
    request,
    empresa_slug,
    evento_id,
):
    tenant, _roles = _contexto_empresa(request, empresa_slug)
    evento = _evento_visible(
        request.user,
        tenant.empresa,
        evento_id,
        action=Actions.EVENT_EDIT,
    )
    try:
        content, receipt = generar_expediente_purge_ready(
            evento,
            user=request.user,
        )
    except ValidationError as exc:
        messages.error(request, " ".join(exc.messages))
        destino = reverse(
            "k9_evento_configuracion",
            kwargs={
                "empresa_slug": tenant.empresa.slug,
                "evento_id": evento.id,
            },
        )
        return redirect(
            _url_with_return(
                destino,
                _return_context(request, tenant.empresa),
            )
        )

    response = HttpResponse(
        content,
        content_type="application/zip",
    )
    response["Content-Disposition"] = (
        f'attachment; filename="evento_{evento.id}_PURGE_READY_D6_4.zip"'
    )
    response["X-DIRTEC-Archive-SHA256"] = receipt.sha256
    return response


@require_POST
@login_required(login_url="/login/")
def evento_ejecutar_purga_historica(
    request,
    empresa_slug,
    evento_id,
):
    tenant, _roles = _contexto_empresa(request, empresa_slug)
    evento = _evento_visible(
        request.user,
        tenant.empresa,
        evento_id,
    )
    expediente = get_object_or_404(
        ExpedienteHistoricoEvento,
        pk=request.POST.get("expediente_id"),
        empresa=tenant.empresa,
        evento_id_snapshot=evento.id,
        formato="K9_D6_PURGE_READY_V3",
    )

    try:
        receipt = ejecutar_purga_historica(
            evento,
            expediente=expediente,
            user=request.user,
            confirmacion=request.POST.get("confirmacion"),
            sha256=request.POST.get("sha256"),
        )
    except PermissionDenied:
        raise
    except ValidationError as exc:
        messages.error(request, " ".join(exc.messages))
        destino = reverse(
            "k9_evento_configuracion",
            kwargs={
                "empresa_slug": tenant.empresa.slug,
                "evento_id": evento.id,
            },
        )
        return redirect(
            _url_with_return(
                destino,
                _return_context(request, tenant.empresa),
            )
        )

    failed = len(
        (receipt.resultado_purga or {}).get(
            "binarios_fallidos",
            [],
        )
    )
    if failed:
        messages.warning(
            request,
            f"Evento purgado. Quedaron {failed} archivo(s) fisico(s) pendientes de limpieza.",
        )
    else:
        messages.success(
            request,
            "Evento historico purgado y binarios eliminados. Se conserva el recibo de auditoria.",
        )
    return redirect(_return_context(request, tenant.empresa))


@require_GET
@login_required(login_url="/login/")
def evento_exportar_expediente(request, empresa_slug, evento_id):
    tenant, _roles = _contexto_empresa(request, empresa_slug)
    evento = _evento_visible(
        request.user,
        tenant.empresa,
        evento_id,
        action=Actions.EVENT_EDIT,
    )
    try:
        content, receipt = generar_expediente_estructurado(
            evento,
            user=request.user,
        )
    except ValidationError as exc:
        messages.error(request, " ".join(exc.messages))
        destino = reverse(
            "k9_evento_configuracion",
            kwargs={
                "empresa_slug": tenant.empresa.slug,
                "evento_id": evento.id,
            },
        )
        return redirect(
            _url_with_return(
                destino,
                _return_context(request, tenant.empresa),
            )
        )

    safe_name = f"evento_{evento.id}_expediente_D6_1.zip"
    response = HttpResponse(content, content_type="application/zip")
    response["Content-Disposition"] = (
        f'attachment; filename="{safe_name}"'
    )
    response["X-DIRTEC-Archive-SHA256"] = receipt.sha256
    return response




@require_POST
@login_required(login_url="/login/")
def evento_confirmar_respaldo_externo(request, empresa_slug, evento_id):
    tenant, _roles = _contexto_empresa(request, empresa_slug)
    evento = _evento_visible(
        request.user,
        tenant.empresa,
        evento_id,
        action=Actions.EVENT_EDIT,
    )
    expediente = get_object_or_404(
        ExpedienteHistoricoEvento,
        pk=request.POST.get("expediente_id"),
        empresa=tenant.empresa,
        evento_id_snapshot=evento.id,
    )
    try:
        confirmar_respaldo_externo(
            evento,
            expediente=expediente,
            user=request.user,
            sha256=request.POST.get("sha256"),
        )
    except ValidationError as exc:
        messages.error(request, " ".join(exc.messages))
    else:
        messages.success(
            request,
            "Respaldo externo confirmado. Inicio el periodo minimo de retencion.",
        )

    destino = reverse(
        "k9_evento_configuracion",
        kwargs={"empresa_slug": tenant.empresa.slug, "evento_id": evento.id},
    )
    return redirect(_url_with_return(destino, _return_context(request, tenant.empresa)))


@require_POST
@login_required(login_url="/login/")
def evento_autorizar_purga_historica(request, empresa_slug, evento_id):
    tenant, _roles = _contexto_empresa(request, empresa_slug)
    evento = _evento_visible(request.user, tenant.empresa, evento_id)
    expediente = get_object_or_404(
        ExpedienteHistoricoEvento,
        pk=request.POST.get("expediente_id"),
        empresa=tenant.empresa,
        evento_id_snapshot=evento.id,
    )
    try:
        autorizar_purga_historica(
            evento,
            expediente=expediente,
            user=request.user,
            motivo=request.POST.get("motivo"),
        )
    except PermissionDenied:
        raise
    except ValidationError as exc:
        messages.error(request, " ".join(exc.messages))
    else:
        messages.success(
            request,
            "Purga historica autorizada por DIRTEC. La ejecucion destructiva sigue bloqueada hasta D6.4.",
        )

    destino = reverse(
        "k9_evento_configuracion",
        kwargs={"empresa_slug": tenant.empresa.slug, "evento_id": evento.id},
    )
    return redirect(_url_with_return(destino, _return_context(request, tenant.empresa)))


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
