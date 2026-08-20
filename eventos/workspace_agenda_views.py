from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from core.services.authorization import Actions, usuario_puede_evento
from core.services.ciclo_vida_operativo import (
    archivar_actividad_itinerario,
    cancelar_actividad_itinerario,
    desarchivar_actividad_itinerario,
)
from itinerario.models import ActividadItinerario

from .workspace_agenda import (
    completar_actividad,
    eliminar_actividad_error,
    evaluar_eliminacion_actividad,
    guardar_actividad,
    purgar_actividad_archivada,
    usuario_puede_purgar_actividad,
)
from .workspace_agenda_forms import WorkspaceActividadForm
from .workspace_views import (
    _app_context,
    _contexto_empresa,
    _evento_visible,
    _return_context,
    _url_with_return,
    _workspace_context,
)


def _redirect_agenda(empresa, evento, return_to, *, actividad_id=None, vista=None, modo=None):
    url = reverse(
        "k9_evento_agenda",
        kwargs={"empresa_slug": empresa.slug, "evento_id": evento.id},
    )
    params = []
    if actividad_id:
        params.append(f"actividad={actividad_id}")
    if vista:
        params.append(f"vista={vista}")
    if modo:
        params.append(f"modo={modo}")
    if params:
        url += "?" + "&".join(params)
    return _url_with_return(url, return_to)


def _validation_message(request, exc):
    messages.error(request, " ".join(getattr(exc, "messages", None) or [str(exc)]))


@login_required(login_url="/login/")
def evento_agenda(request, empresa_slug, evento_id):
    tenant, _roles = _contexto_empresa(request, empresa_slug)
    empresa = tenant.empresa
    evento = _evento_visible(request.user, empresa, evento_id)
    return_to = _return_context(request, empresa)
    puede_operar = usuario_puede_evento(request.user, evento, Actions.EVENT_OPERATIONS)

    all_items = (
        ActividadItinerario.objects.filter(evento=evento)
        .select_related("responsable", "proveedor", "servicio_evento")
        .prefetch_related("participantes__usuario", "participantes__proveedor")
        .order_by("fecha", "hora_inicio", "orden", "id")
    )

    vista = (request.POST.get("vista") or request.GET.get("vista") or "proximas").lower()
    modo = (request.POST.get("modo") or request.GET.get("modo") or "timeline").lower()
    if modo not in {"timeline", "lista"}:
        modo = "timeline"

    q = (request.GET.get("q") or "").strip()
    tipo = (request.GET.get("tipo") or "").strip()
    hoy = timezone.localdate()

    if vista == "archivadas":
        items = all_items.filter(archivado_en__isnull=False)
    elif vista == "canceladas":
        items = all_items.filter(archivado_en__isnull=True, estado="CANCELADA")
    elif vista == "completadas":
        items = all_items.filter(archivado_en__isnull=True, estado="COMPLETADA")
    elif vista == "todas":
        items = all_items.filter(archivado_en__isnull=True)
    else:
        items = all_items.filter(
            archivado_en__isnull=True,
            fecha__gte=hoy,
        ).exclude(estado__in={"CANCELADA", "COMPLETADA"})

    if q:
        items = items.filter(
            Q(titulo__icontains=q)
            | Q(descripcion__icontains=q)
            | Q(ubicacion__icontains=q)
            | Q(proveedor__nombre_comercial__icontains=q)
        )
    if tipo:
        items = items.filter(tipo=tipo)

    actividad_id = request.POST.get("actividad_id") or request.GET.get("actividad")
    actividad = get_object_or_404(all_items, pk=actividad_id) if actividad_id else None
    accion = request.POST.get("accion")
    form = None

    if request.method == "POST":
        if not puede_operar:
            raise PermissionDenied("No tienes permiso para gestionar la agenda de este evento.")

        if accion == "guardar":
            instance = actividad or ActividadItinerario(evento=evento)
            form = WorkspaceActividadForm(
                request.POST,
                instance=instance,
                empresa=empresa,
                evento=evento,
            )
            if form.is_valid():
                try:
                    actividad = guardar_actividad(
                        instance,
                        evento=evento,
                        cleaned_data=dict(form.cleaned_data),
                        user=request.user,
                        request=request,
                    )
                except ValidationError as exc:
                    _validation_message(request, exc)
                else:
                    messages.success(request, "Actividad guardada.")
                    return redirect(_redirect_agenda(
                        empresa, evento, return_to,
                        actividad_id=actividad.id, vista=vista, modo=modo,
                    ))
            else:
                messages.error(request, "Revisa los datos de la actividad.")

        elif accion == "completar":
            if actividad is None:
                raise PermissionDenied("Selecciona una actividad.")
            try:
                completar_actividad(actividad, user=request.user, request=request)
            except ValidationError as exc:
                _validation_message(request, exc)
            else:
                messages.success(request, "Actividad completada.")
            return redirect(_redirect_agenda(empresa, evento, return_to, vista="completadas", modo=modo))

        elif accion == "cancelar":
            if actividad is None:
                raise PermissionDenied("Selecciona una actividad.")
            try:
                cancelar_actividad_itinerario(
                    actividad,
                    actor=request.user,
                    motivo=request.POST.get("motivo"),
                    request=request,
                )
            except ValidationError as exc:
                _validation_message(request, exc)
            else:
                messages.success(request, "Actividad cancelada.")
            return redirect(_redirect_agenda(empresa, evento, return_to, vista="canceladas", modo=modo))

        elif accion == "archivar":
            if actividad is None:
                raise PermissionDenied("Selecciona una actividad.")
            try:
                archivar_actividad_itinerario(actividad, actor=request.user, request=request)
            except ValidationError as exc:
                _validation_message(request, exc)
            else:
                messages.success(request, "Actividad archivada.")
            return redirect(_redirect_agenda(empresa, evento, return_to, vista="archivadas", modo=modo))

        elif accion == "restaurar":
            if actividad is None:
                raise PermissionDenied("Selecciona una actividad.")
            desarchivar_actividad_itinerario(actividad, actor=request.user, request=request)
            messages.success(request, "Actividad restaurada.")
            return redirect(_redirect_agenda(
                empresa, evento, return_to,
                actividad_id=actividad.id,
                vista="completadas" if actividad.estado == "COMPLETADA" else "canceladas",
                modo=modo,
            ))

        elif accion == "eliminar_error":
            if actividad is None:
                raise PermissionDenied("Selecciona una actividad.")
            if (request.POST.get("confirmacion") or "").strip().upper() != "ELIMINAR":
                messages.error(request, "Escribe ELIMINAR para confirmar.")
            else:
                try:
                    eliminar_actividad_error(actividad, user=request.user, request=request)
                except ValidationError as exc:
                    _validation_message(request, exc)
                else:
                    messages.success(request, "Actividad creada por error eliminada.")
            return redirect(_redirect_agenda(empresa, evento, return_to, vista=vista, modo=modo))

        elif accion == "purgar":
            if actividad is None:
                raise PermissionDenied("Selecciona una actividad.")
            if (request.POST.get("confirmacion") or "").strip().upper() != "PURGAR":
                messages.error(request, "Escribe PURGAR para confirmar.")
            else:
                try:
                    purgar_actividad_archivada(actividad, user=request.user, request=request)
                except ValidationError as exc:
                    _validation_message(request, exc)
                else:
                    messages.success(request, "Actividad archivada purgada.")
            return redirect(_redirect_agenda(empresa, evento, return_to, vista="archivadas", modo=modo))

    if form is None:
        initial = {}
        if not actividad and evento.fecha_inicio:
            initial["fecha"] = evento.fecha_inicio.date()
        form = WorkspaceActividadForm(
            instance=actividad,
            empresa=empresa,
            evento=evento,
            initial=initial,
        )

    agenda_list = list(items)
    selected_eval = (
        evaluar_eliminacion_actividad(actividad, para_purga=bool(actividad.archivado_en))
        if actividad else None
    )

    context = _app_context(request, empresa, title=evento.titulo_evento, section="Event Workspace")
    context.update({
        "evento": evento,
        "workspace_active": "agenda",
        "workspace_navigation": _workspace_context(
            request, empresa=empresa, evento=evento, active_key="agenda",
        ),
        "return_to": return_to,
        "puede_editar": puede_operar,
        "puede_operar": puede_operar,
        "actividades": agenda_list,
        "actividad": actividad,
        "form": form,
        "vista": vista,
        "modo": modo,
        "busqueda": q,
        "tipo_filtro": tipo,
        "selected_eval": selected_eval,
        "puede_purgar": bool(actividad and usuario_puede_purgar_actividad(request.user, actividad)),
    })
    return render(request, "eventos/workspace/agenda.html", context)
