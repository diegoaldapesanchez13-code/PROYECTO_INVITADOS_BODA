from urllib.parse import quote

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from core.services.authorization import Actions, usuario_puede_evento
from invitaciones.guest_analytics import resumen_invitados_evento
from invitaciones.models import Grupoinvitacion, Invitado

from .workspace_guests import (
    agregar_persona,
    crear_grupo,
    editar_grupo,
    eliminar_grupo_error,
    eliminar_persona_error,
    guardar_persona,
    grupo_puede_eliminarse,
    registrar_respuesta_manual,
)
from .workspace_guests_capacity import resumen_cupo_evento
from .workspace_guests_forms import (
    WorkspaceGrupoForm,
    WorkspaceInvitadoForm,
    WorkspaceRespuestaForm,
)
from .workspace_views import (
    _app_context,
    _contexto_empresa,
    _evento_visible,
    _return_context,
    _url_with_return,
    _workspace_context,
)


def _redirect_invitados(
    empresa,
    evento,
    return_to,
    *,
    grupo_id=None,
    invitado_id=None,
    estado=None,
):
    url = reverse(
        "k9_evento_invitados",
        kwargs={"empresa_slug": empresa.slug, "evento_id": evento.id},
    )
    params = []
    if grupo_id:
        params.append(f"grupo={grupo_id}")
    if invitado_id:
        params.append(f"invitado={invitado_id}")
    if estado:
        params.append(f"estado={quote(estado)}")
    if params:
        url += "?" + "&".join(params)
    return _url_with_return(url, return_to)


def _validation_message(request, exc):
    messages.error(request, " ".join(getattr(exc, "messages", None) or [str(exc)]))


@login_required(login_url="/login/")
def evento_invitados(request, empresa_slug, evento_id):
    tenant, _roles = _contexto_empresa(request, empresa_slug)
    empresa = tenant.empresa
    evento = _evento_visible(request.user, empresa, evento_id)
    return_to = _return_context(request, empresa)

    puede_gestionar = usuario_puede_evento(
        request.user,
        evento,
        Actions.EVENT_GUESTS,
    )

    grupos_qs = (
        Grupoinvitacion.objects.filter(evento=evento)
        .prefetch_related("invitados")
        .order_by("nombre_grupo", "id")
    )
    invitados_qs = (
        Invitado.objects.filter(grupo__evento=evento)
        .select_related("grupo")
        .order_by("grupo__nombre_grupo", "orden", "id")
    )

    q = (request.GET.get("q") or "").strip()
    estado = (request.GET.get("estado") or "TODOS").upper()
    tipo = (request.GET.get("tipo") or "").upper()

    if q:
        grupos_qs = grupos_qs.filter(
            Q(nombre_grupo__icontains=q)
            | Q(telefono_contacto__icontains=q)
            | Q(correo_contacto__icontains=q)
            | Q(invitados__nombre__icontains=q)
            | Q(invitados__apellidos__icontains=q)
        ).distinct()

    if tipo in {"PERSONAL", "FAMILIAR"}:
        grupos_qs = grupos_qs.filter(tipo=tipo)

    if estado == "CONFIRMADOS":
        grupos_qs = grupos_qs.filter(invitados__asistira=True).distinct()
    elif estado == "NO_ASISTEN":
        grupos_qs = grupos_qs.filter(invitados__asistira=False).distinct()
    elif estado == "PENDIENTES":
        grupos_qs = grupos_qs.filter(invitados__asistira__isnull=True).distinct()

    grupo_id = request.POST.get("grupo_id") or request.GET.get("grupo")
    invitado_id = request.POST.get("invitado_id") or request.GET.get("invitado")

    grupo = get_object_or_404(
        Grupoinvitacion.objects.filter(evento=evento).prefetch_related("invitados"),
        pk=grupo_id,
    ) if grupo_id else None

    invitado = get_object_or_404(
        invitados_qs,
        pk=invitado_id,
    ) if invitado_id else None

    if invitado and grupo is None:
        grupo = invitado.grupo

    accion = request.POST.get("accion")
    grupo_form = None
    invitado_form = None
    respuesta_form = None

    if request.method == "POST":
        if not puede_gestionar:
            raise PermissionDenied("No tienes permiso para gestionar invitados.")

        if accion == "guardar_grupo":
            grupo_form = WorkspaceGrupoForm(request.POST, instance=grupo)
            if grupo_form.is_valid():
                try:
                    if grupo:
                        grupo = editar_grupo(
                            grupo,
                            cleaned_data=dict(grupo_form.cleaned_data),
                            user=request.user,
                            request=request,
                        )
                    else:
                        grupo = crear_grupo(
                            evento=evento,
                            cleaned_data=dict(grupo_form.cleaned_data),
                            user=request.user,
                            request=request,
                        )
                except ValidationError as exc:
                    _validation_message(request, exc)
                else:
                    messages.success(request, "Invitación guardada.")
                    return redirect(_redirect_invitados(
                        empresa, evento, return_to, grupo_id=grupo.id, estado=estado,
                    ))
            else:
                messages.error(request, "Revisa los datos de la invitación.")

        elif accion == "guardar_invitado":
            if grupo is None:
                raise PermissionDenied("Selecciona una invitación.")
            invitado_form = WorkspaceInvitadoForm(request.POST, instance=invitado)
            if invitado_form.is_valid():
                try:
                    if invitado:
                        invitado = guardar_persona(
                            invitado,
                            cleaned_data=dict(invitado_form.cleaned_data),
                            user=request.user,
                            request=request,
                        )
                    else:
                        invitado = agregar_persona(
                            grupo,
                            cleaned_data=dict(invitado_form.cleaned_data),
                            user=request.user,
                            request=request,
                        )
                except ValidationError as exc:
                    _validation_message(request, exc)
                else:
                    messages.success(request, "Persona guardada.")
                    return redirect(_redirect_invitados(
                        empresa,
                        evento,
                        return_to,
                        grupo_id=grupo.id,
                        invitado_id=invitado.id,
                        estado=estado,
                    ))
            else:
                messages.error(request, "Revisa los datos de la persona.")

        elif accion == "respuesta":
            if invitado is None:
                raise PermissionDenied("Selecciona una persona.")
            respuesta_form = WorkspaceRespuestaForm(request.POST)
            if respuesta_form.is_valid():
                try:
                    registrar_respuesta_manual(
                        invitado,
                        respuesta_form.cleaned_data["respuesta"],
                        user=request.user,
                        request=request,
                    )
                except ValidationError as exc:
                    _validation_message(request, exc)
                else:
                    messages.success(request, "RSVP actualizado.")
            return redirect(_redirect_invitados(
                empresa, evento, return_to, grupo_id=invitado.grupo_id, estado=estado,
            ))

        elif accion == "eliminar_grupo":
            if grupo is None:
                raise PermissionDenied("Selecciona una invitación.")
            if (request.POST.get("confirmacion") or "").strip().upper() != "ELIMINAR":
                messages.error(request, "Escribe ELIMINAR para confirmar.")
            else:
                try:
                    eliminar_grupo_error(
                        grupo,
                        user=request.user,
                        request=request,
                    )
                except ValidationError as exc:
                    _validation_message(request, exc)
                else:
                    messages.success(request, "Invitación sin historial eliminada.")
            return redirect(_redirect_invitados(
                empresa, evento, return_to, estado=estado,
            ))

        elif accion == "eliminar_invitado":
            if invitado is None:
                raise PermissionDenied("Selecciona una persona.")
            grupo_id_destino = invitado.grupo_id
            if (request.POST.get("confirmacion") or "").strip().upper() != "ELIMINAR":
                messages.error(request, "Escribe ELIMINAR para confirmar.")
            else:
                try:
                    eliminar_persona_error(
                        invitado,
                        user=request.user,
                        request=request,
                    )
                except ValidationError as exc:
                    _validation_message(request, exc)
                else:
                    messages.success(request, "Persona sin historial eliminada.")
            return redirect(_redirect_invitados(
                empresa, evento, return_to, grupo_id=grupo_id_destino, estado=estado,
            ))

    if grupo_form is None:
        grupo_form = WorkspaceGrupoForm(instance=grupo)

    if grupo is not None and not grupo.es_personal:
        if invitado is not None and not invitado.es_acompanante_extra:
            invitado_form = invitado_form or WorkspaceInvitadoForm(instance=invitado)
        elif invitado is None:
            invitado_form = invitado_form or WorkspaceInvitadoForm()
    elif invitado is not None:
        invitado_form = invitado_form or WorkspaceInvitadoForm(instance=invitado)

    if invitado is not None:
        current = (
            "SI" if invitado.asistira is True
            else "NO" if invitado.asistira is False
            else "PENDIENTE"
        )
        respuesta_form = respuesta_form or WorkspaceRespuestaForm(
            initial={"respuesta": current}
        )

    grupos = list(grupos_qs)
    metricas = resumen_invitados_evento(evento, incluir_mesas=True)
    cupo = resumen_cupo_evento(evento).as_dict()

    grupo_delete = grupo_puede_eliminarse(grupo) if grupo else (False, "")

    context = _app_context(
        request,
        empresa,
        title=evento.titulo_evento,
        section="Event Workspace",
    )
    context.update({
        "evento": evento,
        "workspace_active": "invitados",
        "workspace_navigation": _workspace_context(
            request,
            empresa=empresa,
            evento=evento,
            active_key="invitados",
        ),
        "return_to": return_to,
        "puede_editar": puede_gestionar,
        "puede_gestionar": puede_gestionar,
        "grupos": grupos,
        "grupo": grupo,
        "invitado": invitado,
        "grupo_form": grupo_form,
        "invitado_form": invitado_form,
        "respuesta_form": respuesta_form,
        "metricas": metricas,
        "cupo": cupo,
        "estado_filtro": estado,
        "tipo_filtro": tipo,
        "busqueda": q,
        "grupo_puede_eliminar": grupo_delete[0],
        "grupo_motivo_no_eliminar": grupo_delete[1],
    })
    return render(request, "eventos/workspace/invitados.html", context)
