from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from core.services.authorization import Actions, usuario_puede_evento
from core.services.ciclo_vida_operativo import (
    archivar_servicio_evento,
    cancelar_servicio_evento,
    desarchivar_servicio_evento,
)
from presupuesto.services import usuario_puede_ver_finanzas_internas
from proveedores.models import ServicioEvento

from .workspace_services import (
    eliminar_servicio_error,
    evaluar_eliminacion_servicio,
    guardar_servicio_operativo,
    purgar_servicio_archivado,
    usuario_puede_purgar_servicio,
)
from .workspace_services_forms import WorkspaceServicioForm
from .workspace_views import (
    _app_context,
    _contexto_empresa,
    _evento_visible,
    _return_context,
    _url_with_return,
    _workspace_context,
)


def _redirect_servicios(empresa, evento, return_to, *, servicio_id=None, vista=None):
    url = reverse(
        "k9_evento_servicios",
        kwargs={"empresa_slug": empresa.slug, "evento_id": evento.id},
    )
    params = []
    if servicio_id:
        params.append(f"servicio={servicio_id}")
    if vista:
        params.append(f"vista={vista}")
    if params:
        url = f"{url}?{'&'.join(params)}"
    return _url_with_return(url, return_to)


def _message_validation(request, exc):
    messages.error(
        request,
        " ".join(getattr(exc, "messages", None) or [str(exc)]),
    )


@login_required(login_url="/login/")
def evento_servicios(request, empresa_slug, evento_id):
    tenant, _roles = _contexto_empresa(request, empresa_slug)
    empresa = tenant.empresa
    evento = _evento_visible(request.user, empresa, evento_id)
    return_to = _return_context(request, empresa)

    puede_operar = usuario_puede_evento(
        request.user,
        evento,
        Actions.EVENT_OPERATIONS,
    )
    puede_finanzas = usuario_puede_ver_finanzas_internas(request.user, evento)

    servicios_qs = (
        ServicioEvento.objects.filter(evento=evento)
        .select_related(
            "proveedor",
            "servicio_catalogo_k9",
            "contrato_origen",
        )
        .order_by("archivado_en", "fecha_servicio", "nombre_servicio", "id")
    )

    vista = (request.GET.get("vista") or request.POST.get("vista") or "activos").lower()
    q = (request.GET.get("q") or "").strip()

    if vista == "archivados":
        servicios_listado = servicios_qs.filter(archivado_en__isnull=False)
    elif vista == "cancelados":
        servicios_listado = servicios_qs.filter(
            archivado_en__isnull=True,
            estado_operativo="CANCELADO",
        )
    else:
        servicios_listado = servicios_qs.filter(archivado_en__isnull=True).exclude(
            estado_operativo="CANCELADO"
        )

    if q:
        servicios_listado = servicios_listado.filter(
            Q(nombre_servicio__icontains=q)
            | Q(proveedor__nombre_comercial__icontains=q)
            | Q(categoria__icontains=q)
        )

    servicio_id = request.POST.get("servicio_id") or request.GET.get("servicio")
    servicio = None
    if servicio_id:
        servicio = get_object_or_404(servicios_qs, pk=servicio_id)

    accion = request.POST.get("accion")
    form = None

    if request.method == "POST":
        if not puede_operar:
            raise PermissionDenied("No tienes permiso para gestionar los servicios de este evento.")

        if accion == "guardar":
            instance = servicio or ServicioEvento(evento=evento)
            form = WorkspaceServicioForm(
                request.POST,
                instance=instance,
                empresa=empresa,
                can_finance=puede_finanzas,
            )
            if form.is_valid():
                cleaned = dict(form.cleaned_data)
                if not puede_finanzas:
                    cleaned.pop("costo_proveedor", None)
                try:
                    servicio = guardar_servicio_operativo(
                        instance,
                        evento=evento,
                        cleaned_data=cleaned,
                        user=request.user,
                        request=request,
                    )
                except ValidationError as exc:
                    _message_validation(request, exc)
                else:
                    messages.success(
                        request,
                        "Servicio creado." if not servicio_id else "Servicio actualizado.",
                    )
                    return redirect(
                        _redirect_servicios(
                            empresa,
                            evento,
                            return_to,
                            servicio_id=servicio.id,
                            vista=vista,
                        )
                    )
            else:
                messages.error(request, "Revisa los datos del servicio.")

        elif accion == "cancelar":
            if servicio is None:
                raise PermissionDenied("Selecciona un servicio.")
            try:
                cancelar_servicio_evento(
                    servicio,
                    actor=request.user,
                    motivo=request.POST.get("motivo"),
                    request=request,
                )
            except ValidationError as exc:
                _message_validation(request, exc)
            else:
                messages.success(request, "Servicio cancelado sin borrar su historial.")
            return redirect(_redirect_servicios(empresa, evento, return_to, vista="cancelados"))

        elif accion == "archivar":
            if servicio is None:
                raise PermissionDenied("Selecciona un servicio.")
            try:
                archivar_servicio_evento(
                    servicio,
                    actor=request.user,
                    request=request,
                )
            except ValidationError as exc:
                _message_validation(request, exc)
            else:
                messages.success(request, "Servicio archivado.")
            return redirect(_redirect_servicios(empresa, evento, return_to, vista="archivados"))

        elif accion == "restaurar":
            if servicio is None:
                raise PermissionDenied("Selecciona un servicio.")
            desarchivar_servicio_evento(
                servicio,
                actor=request.user,
                request=request,
            )
            messages.success(request, "Servicio restaurado del archivo.")
            return redirect(
                _redirect_servicios(
                    empresa,
                    evento,
                    return_to,
                    servicio_id=servicio.id,
                    vista="cancelados" if servicio.estado_operativo == "CANCELADO" else "activos",
                )
            )

        elif accion == "eliminar_error":
            if servicio is None:
                raise PermissionDenied("Selecciona un servicio.")
            if (request.POST.get("confirmacion") or "").strip().upper() != "ELIMINAR":
                messages.error(request, "Escribe ELIMINAR para confirmar.")
            else:
                try:
                    eliminar_servicio_error(
                        servicio,
                        user=request.user,
                        request=request,
                    )
                except ValidationError as exc:
                    _message_validation(request, exc)
                else:
                    messages.success(request, "Servicio creado por error eliminado.")
            return redirect(_redirect_servicios(empresa, evento, return_to, vista=vista))

        elif accion == "purgar":
            if servicio is None:
                raise PermissionDenied("Selecciona un servicio.")
            if (request.POST.get("confirmacion") or "").strip().upper() != "PURGAR":
                messages.error(request, "Escribe PURGAR para confirmar.")
            else:
                try:
                    purgar_servicio_archivado(
                        servicio,
                        user=request.user,
                        request=request,
                    )
                except ValidationError as exc:
                    _message_validation(request, exc)
                else:
                    messages.success(request, "Servicio archivado purgado.")
            return redirect(_redirect_servicios(empresa, evento, return_to, vista="archivados"))

    if form is None:
        form = WorkspaceServicioForm(
            instance=servicio,
            empresa=empresa,
            can_finance=puede_finanzas,
        )

    evaluaciones = {}
    for item in servicios_listado:
        evaluaciones[item.id] = evaluar_eliminacion_servicio(
            item,
            para_purga=bool(item.archivado_en),
        )

    selected_eval = (
        evaluar_eliminacion_servicio(
            servicio,
            para_purga=bool(servicio.archivado_en),
        )
        if servicio
        else None
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
            "workspace_active": "servicios",
            "workspace_navigation": _workspace_context(
                request,
                empresa=empresa,
                evento=evento,
                active_key="servicios",
            ),
            "return_to": return_to,
            "puede_editar": puede_operar,
            "puede_operar": puede_operar,
            "puede_finanzas": puede_finanzas,
            "puede_purgar": bool(
                servicio and usuario_puede_purgar_servicio(request.user, servicio)
            ),
            "servicios": servicios_listado,
            "servicio": servicio,
            "form": form,
            "vista": vista,
            "busqueda": q,
            "evaluaciones": evaluaciones,
            "selected_eval": selected_eval,
        }
    )
    return render(request, "eventos/workspace/servicios.html", context)
