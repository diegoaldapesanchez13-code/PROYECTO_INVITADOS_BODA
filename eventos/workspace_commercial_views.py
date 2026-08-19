from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from core.services.authorization import Actions, usuario_puede_evento
from eventos.models import ContratoEvento
from eventos.services import leer_contrato_interno, materializar_servicios_contrato_v2
from paquetes.models import PropuestaEvento, PropuestaLinea
from paquetes.services import actualizar_totales_propuesta, calcular_propuesta, propuestas_empresa_qs

from .workspace_commercial import (
    cancelar_contrato,
    crear_revision_desde_contrato,
    eliminar_propuesta_error,
    generar_version_contractual,
    propuesta_es_editable,
)
from .workspace_commercial_forms import WorkspaceLineaForm, WorkspacePropuestaForm
from .workspace_views import (
    _app_context,
    _contexto_empresa,
    _evento_visible,
    _return_context,
    _url_with_return,
    _workspace_context,
)


def _redirect_comercial(empresa, evento, return_to, propuesta_id=None):
    url = reverse(
        "k9_evento_comercial",
        kwargs={"empresa_slug": empresa.slug, "evento_id": evento.id},
    )
    if propuesta_id:
        separator = "&" if "?" in url else "?"
        url = f"{url}{separator}propuesta={propuesta_id}"
    return _url_with_return(url, return_to)


@login_required(login_url="/login/")
def evento_comercial(request, empresa_slug, evento_id):
    tenant, _roles = _contexto_empresa(request, empresa_slug)
    empresa = tenant.empresa
    evento = _evento_visible(request.user, empresa, evento_id)
    return_to = _return_context(request, empresa)

    puede_editar = usuario_puede_evento(request.user, evento, Actions.EVENT_EDIT)
    propuestas = propuestas_empresa_qs(empresa).filter(evento=evento).order_by("-updated_at", "-id")
    contratos = (
        ContratoEvento.objects.filter(evento=evento)
        .select_related("propuesta_origen")
        .order_by("-version", "-id")
    )

    selected_id = request.POST.get("propuesta_id") or request.GET.get("propuesta")
    propuesta = None
    if selected_id:
        propuesta = get_object_or_404(propuestas, pk=selected_id)
    elif propuestas.exists():
        propuesta = propuestas.first()

    accion = request.POST.get("accion")
    if request.method == "POST":
        if not puede_editar:
            raise PermissionDenied("No tienes permiso para modificar el area comercial.")

        if accion == "guardar_propuesta":
            instance = propuesta
            form = WorkspacePropuestaForm(
                request.POST,
                instance=instance,
                empresa=empresa,
                evento=evento,
            )
            if instance is not None and not propuesta_es_editable(instance):
                raise PermissionDenied("Esta propuesta ya es contractual y esta congelada.")
            if form.is_valid():
                propuesta = form.save(commit=False)
                if not propuesta.pk:
                    propuesta.created_by = request.user
                propuesta.updated_by = request.user
                propuesta.full_clean()
                propuesta.save()
                actualizar_totales_propuesta(propuesta, user=request.user)
                messages.success(request, "Propuesta guardada.")
                return redirect(_redirect_comercial(empresa, evento, return_to, propuesta.id))
            messages.error(request, "Revisa los datos de la propuesta.")

        elif accion == "agregar_linea":
            if propuesta is None or not propuesta_es_editable(propuesta):
                raise PermissionDenied("La propuesta debe estar editable.")
            linea_form = WorkspaceLineaForm(request.POST, propuesta=propuesta)
            if linea_form.is_valid():
                linea_form.save()
                actualizar_totales_propuesta(propuesta, user=request.user)
                messages.success(request, "Servicio agregado a la propuesta.")
                return redirect(_redirect_comercial(empresa, evento, return_to, propuesta.id))
            messages.error(request, "Revisa la linea comercial.")

        elif accion == "toggle_linea":
            if propuesta is None or not propuesta_es_editable(propuesta):
                raise PermissionDenied("La propuesta debe estar editable.")
            linea = get_object_or_404(
                PropuestaLinea,
                propuesta=propuesta,
                pk=request.POST.get("linea_id"),
            )
            linea.activo = not linea.activo
            linea.save(update_fields=["activo", "updated_at"])
            actualizar_totales_propuesta(propuesta, user=request.user)
            messages.success(request, "Linea reactivada." if linea.activo else "Linea retirada.")
            return redirect(_redirect_comercial(empresa, evento, return_to, propuesta.id))

        elif accion == "eliminar_propuesta_error":
            if propuesta is None:
                raise PermissionDenied("Selecciona una propuesta.")
            try:
                eliminar_propuesta_error(propuesta, user=request.user, request=request)
            except ValidationError as exc:
                messages.error(request, " ".join(exc.messages))
            else:
                messages.success(request, "Borrador eliminado.")
            return redirect(_redirect_comercial(empresa, evento, return_to))

        elif accion == "generar_contrato":
            if propuesta is None:
                raise PermissionDenied("Selecciona una propuesta.")
            try:
                contrato = generar_version_contractual(
                    propuesta,
                    user=request.user,
                    request=request,
                )
            except ValidationError as exc:
                messages.error(request, " ".join(exc.messages))
            else:
                messages.success(request, f"Contrato v{contrato.version} generado y congelado.")
            return redirect(_redirect_comercial(empresa, evento, return_to, propuesta.id))

        elif accion == "crear_revision":
            contrato = get_object_or_404(
                contratos,
                pk=request.POST.get("contrato_id"),
            )
            try:
                nueva = crear_revision_desde_contrato(
                    contrato,
                    user=request.user,
                    request=request,
                )
            except ValidationError as exc:
                messages.error(request, " ".join(exc.messages))
                return redirect(_redirect_comercial(empresa, evento, return_to, propuesta.id if propuesta else None))
            messages.success(request, f"Revision creada desde contrato v{contrato.version}.")
            return redirect(_redirect_comercial(empresa, evento, return_to, nueva.id))

        elif accion == "cancelar_contrato":
            contrato = get_object_or_404(
                contratos,
                pk=request.POST.get("contrato_id"),
            )
            cancelar_contrato(
                contrato,
                motivo=request.POST.get("motivo", ""),
                user=request.user,
                request=request,
            )
            messages.success(request, f"Contrato v{contrato.version} cancelado; el snapshot se conserva.")
            return redirect(_redirect_comercial(empresa, evento, return_to, propuesta.id if propuesta else None))

        elif accion == "materializar_contrato":
            contrato = get_object_or_404(
                contratos,
                pk=request.POST.get("contrato_id"),
            )
            if not usuario_puede_evento(request.user, evento, Actions.EVENT_OPERATIONS):
                raise PermissionDenied("No tienes permiso para preparar la operacion.")
            try:
                resultado = materializar_servicios_contrato_v2(contrato.id, user=request.user)
            except ValidationError as exc:
                messages.error(request, " ".join(exc.messages))
            else:
                messages.success(
                    request,
                    f"Operacion preparada: {resultado['creados']} nuevos, {resultado['actualizados']} actualizados.",
                )
            return redirect(_redirect_comercial(empresa, evento, return_to, propuesta.id if propuesta else None))

    if propuesta is not None and propuesta.estado == "CONTRATADO":
        form = WorkspacePropuestaForm(instance=propuesta, empresa=empresa, evento=evento)
    elif request.method == "POST" and accion == "guardar_propuesta":
        # Preserve validation errors from the POST branch.
        pass
    else:
        form = WorkspacePropuestaForm(instance=propuesta, empresa=empresa, evento=evento)

    linea_form = (
        WorkspaceLineaForm(propuesta=propuesta)
        if propuesta is not None and propuesta_es_editable(propuesta)
        else None
    )
    dto = calcular_propuesta(propuesta) if propuesta is not None else None

    contrato_actual = contratos.filter(estado__in=["CONTRATADO", "FIRMADO"]).first()
    if contrato_actual is None:
        contrato_actual = contratos.first()
    contrato_data = leer_contrato_interno(contrato_actual) if contrato_actual else None

    context = _app_context(
        request,
        empresa,
        title=evento.titulo_evento,
        section="Event Workspace",
    )
    context.update(
        {
            "evento": evento,
            "workspace_active": "comercial",
            "workspace_navigation": _workspace_context(
                request,
                empresa=empresa,
                evento=evento,
                active_key="comercial",
            ),
            "return_to": return_to,
            "puede_editar": puede_editar,
            "propuestas": propuestas,
            "propuesta": propuesta,
            "propuesta_editable": propuesta_es_editable(propuesta),
            "form": form,
            "linea_form": linea_form,
            "dto": dto,
            "contratos": contratos,
            "contrato_actual": contrato_actual,
            "contrato_data": contrato_data,
        }
    )
    return render(request, "eventos/workspace/comercial.html", context)
