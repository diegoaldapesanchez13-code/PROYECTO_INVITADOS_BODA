from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from core.services.authorization import Actions, usuario_puede_evento
from core.services.ciclo_vida_operativo import (
    archivar_tarea_evento,
    cancelar_tarea_evento,
    desarchivar_tarea_evento,
)
from tareas.models import TareaEvento

from .workspace_tasks import (
    eliminar_tarea_error,
    evaluar_eliminacion_tarea,
    guardar_tarea,
    mover_tarea_kanban,
    purgar_tarea_archivada,
    usuario_puede_purgar_tarea,
)
from .workspace_tasks_forms import WorkspaceTareaForm
from .workspace_views import (
    _app_context,
    _contexto_empresa,
    _evento_visible,
    _return_context,
    _url_with_return,
    _workspace_context,
)


def _redirect_tareas(empresa, evento, return_to, *, tarea_id=None, vista=None, modo=None):
    url = reverse(
        "k9_evento_tareas",
        kwargs={"empresa_slug": empresa.slug, "evento_id": evento.id},
    )
    params = []
    if tarea_id:
        params.append(f"tarea={tarea_id}")
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
def evento_tareas(request, empresa_slug, evento_id):
    tenant, _roles = _contexto_empresa(request, empresa_slug)
    empresa = tenant.empresa
    evento = _evento_visible(request.user, empresa, evento_id)
    return_to = _return_context(request, empresa)

    puede_operar = usuario_puede_evento(request.user, evento, Actions.EVENT_OPERATIONS)

    all_tasks = (
        TareaEvento.objects.filter(evento=evento)
        .select_related("responsable", "servicio_evento")
        .order_by("fecha_limite", "-prioridad", "id")
    )

    vista = (request.POST.get("vista") or request.GET.get("vista") or "activas").lower()
    modo = (request.POST.get("modo") or request.GET.get("modo") or "tablero").lower()
    if modo not in {"tablero", "lista"}:
        modo = "tablero"

    q = (request.GET.get("q") or "").strip()
    prioridad = (request.GET.get("prioridad") or "").strip()
    responsable_id = (request.GET.get("responsable") or "").strip()

    if vista == "archivadas":
        tasks = all_tasks.filter(archivado_en__isnull=False)
    elif vista == "canceladas":
        tasks = all_tasks.filter(archivado_en__isnull=True, estado="CANCELADA")
    elif vista == "completadas":
        tasks = all_tasks.filter(archivado_en__isnull=True, estado="COMPLETADA")
    else:
        tasks = all_tasks.filter(archivado_en__isnull=True).exclude(
            estado__in={"CANCELADA", "COMPLETADA"}
        )

    if q:
        tasks = tasks.filter(
            Q(titulo__icontains=q)
            | Q(descripcion__icontains=q)
            | Q(responsable__first_name__icontains=q)
            | Q(responsable__last_name__icontains=q)
            | Q(responsable__username__icontains=q)
        )
    if prioridad:
        tasks = tasks.filter(prioridad=prioridad)
    if responsable_id.isdigit():
        tasks = tasks.filter(responsable_id=int(responsable_id))

    tarea_id = request.POST.get("tarea_id") or request.GET.get("tarea")
    tarea = get_object_or_404(all_tasks, pk=tarea_id) if tarea_id else None

    accion = request.POST.get("accion")
    form = None

    if request.method == "POST":
        if not puede_operar:
            raise PermissionDenied("No tienes permiso para gestionar tareas de este evento.")

        if accion == "guardar":
            instance = tarea or TareaEvento(evento=evento)
            form = WorkspaceTareaForm(
                request.POST,
                instance=instance,
                empresa=empresa,
                evento=evento,
            )
            if form.is_valid():
                try:
                    tarea = guardar_tarea(
                        instance,
                        evento=evento,
                        cleaned_data=dict(form.cleaned_data),
                        user=request.user,
                        request=request,
                    )
                except ValidationError as exc:
                    _validation_message(request, exc)
                else:
                    messages.success(request, "Tarea guardada.")
                    return redirect(_redirect_tareas(
                        empresa, evento, return_to,
                        tarea_id=tarea.id, vista=vista, modo=modo,
                    ))
            else:
                messages.error(request, "Revisa los datos de la tarea.")

        elif accion == "mover_estado":
            if tarea is None:
                raise PermissionDenied("Selecciona una tarea.")
            try:
                mover_tarea_kanban(
                    tarea,
                    estado=request.POST.get("estado", ""),
                    user=request.user,
                    request=request,
                )
            except ValidationError as exc:
                _validation_message(request, exc)
            else:
                messages.success(request, "Estado actualizado.")
            return redirect(_redirect_tareas(empresa, evento, return_to, vista=vista, modo=modo))

        elif accion == "cancelar":
            if tarea is None:
                raise PermissionDenied("Selecciona una tarea.")
            try:
                cancelar_tarea_evento(
                    tarea,
                    actor=request.user,
                    motivo=request.POST.get("motivo"),
                    request=request,
                )
            except ValidationError as exc:
                _validation_message(request, exc)
            else:
                messages.success(request, "Tarea cancelada.")
            return redirect(_redirect_tareas(empresa, evento, return_to, vista="canceladas", modo=modo))

        elif accion == "archivar":
            if tarea is None:
                raise PermissionDenied("Selecciona una tarea.")
            try:
                archivar_tarea_evento(tarea, actor=request.user, request=request)
            except ValidationError as exc:
                _validation_message(request, exc)
            else:
                messages.success(request, "Tarea archivada.")
            return redirect(_redirect_tareas(empresa, evento, return_to, vista="archivadas", modo=modo))

        elif accion == "restaurar":
            if tarea is None:
                raise PermissionDenied("Selecciona una tarea.")
            desarchivar_tarea_evento(tarea, actor=request.user, request=request)
            messages.success(request, "Tarea restaurada.")
            return redirect(_redirect_tareas(
                empresa, evento, return_to,
                tarea_id=tarea.id,
                vista="completadas" if tarea.estado == "COMPLETADA" else "canceladas",
                modo=modo,
            ))

        elif accion == "eliminar_error":
            if tarea is None:
                raise PermissionDenied("Selecciona una tarea.")
            if (request.POST.get("confirmacion") or "").strip().upper() != "ELIMINAR":
                messages.error(request, "Escribe ELIMINAR para confirmar.")
            else:
                try:
                    eliminar_tarea_error(tarea, user=request.user, request=request)
                except ValidationError as exc:
                    _validation_message(request, exc)
                else:
                    messages.success(request, "Tarea creada por error eliminada.")
            return redirect(_redirect_tareas(empresa, evento, return_to, vista=vista, modo=modo))

        elif accion == "purgar":
            if tarea is None:
                raise PermissionDenied("Selecciona una tarea.")
            if (request.POST.get("confirmacion") or "").strip().upper() != "PURGAR":
                messages.error(request, "Escribe PURGAR para confirmar.")
            else:
                try:
                    purgar_tarea_archivada(tarea, user=request.user, request=request)
                except ValidationError as exc:
                    _validation_message(request, exc)
                else:
                    messages.success(request, "Tarea archivada purgada.")
            return redirect(_redirect_tareas(empresa, evento, return_to, vista="archivadas", modo=modo))

    if form is None:
        form = WorkspaceTareaForm(
            instance=tarea,
            empresa=empresa,
            evento=evento,
        )

    task_list = list(tasks)
    board = {
        state: [item for item in task_list if item.estado == state]
        for state in ("PENDIENTE", "EN_PROCESO", "EN_REVISION")
    }

    selected_eval = (
        evaluar_eliminacion_tarea(tarea, para_purga=bool(tarea.archivado_en))
        if tarea else None
    )

    responsables = form.fields["responsable"].queryset
    context = _app_context(
        request, empresa, title=evento.titulo_evento, section="Event Workspace",
    )
    context.update({
        "evento": evento,
        "workspace_active": "tareas",
        "workspace_navigation": _workspace_context(
            request, empresa=empresa, evento=evento, active_key="tareas",
        ),
        "return_to": return_to,
        "puede_editar": puede_operar,
        "puede_operar": puede_operar,
        "tareas": task_list,
        "board": board,
        "tarea": tarea,
        "form": form,
        "vista": vista,
        "modo": modo,
        "busqueda": q,
        "prioridad_filtro": prioridad,
        "responsable_filtro": responsable_id,
        "responsables": responsables,
        "selected_eval": selected_eval,
        "puede_purgar": bool(tarea and usuario_puede_purgar_tarea(request.user, tarea)),
    })
    return render(request, "eventos/workspace/tareas.html", context)
