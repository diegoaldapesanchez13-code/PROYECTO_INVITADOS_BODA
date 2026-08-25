from pathlib import Path

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.http import HttpResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.views.decorators.http import require_GET, require_POST

from core.services.authorization import Actions, usuario_puede_evento

from .workspace_guests_io import (
    apply_guest_import,
    build_export_bytes,
    build_import_template_bytes,
    parse_import_workbook,
    validate_import_against_event,
)
from .workspace_views import (
    _contexto_empresa,
    _evento_visible,
    _return_context,
    _url_with_return,
)


def _workspace_url(empresa, evento, return_to):
    url = reverse(
        "k9_evento_invitados",
        kwargs={"empresa_slug": empresa.slug, "evento_id": evento.id},
    )
    return _url_with_return(url, return_to)


def _event_context(request, empresa_slug, evento_id):
    tenant, _roles = _contexto_empresa(request, empresa_slug)
    empresa = tenant.empresa
    evento = _evento_visible(request.user, empresa, evento_id)
    if not usuario_puede_evento(request.user, evento, Actions.EVENT_GUESTS):
        raise PermissionDenied("No tienes permiso para gestionar invitados.")
    return empresa, evento, _return_context(request, empresa)


@login_required(login_url="/login/")
@require_GET
def invitados_plantilla(request, empresa_slug, evento_id):
    empresa, evento, _return_to = _event_context(request, empresa_slug, evento_id)
    content = build_import_template_bytes()
    response = HttpResponse(
        content,
        content_type=(
            "application/vnd.openxmlformats-officedocument."
            "spreadsheetml.sheet"
        ),
    )
    response["Content-Disposition"] = (
        'attachment; filename="DIRTEC_Plantilla_Importacion_Invitados.xlsx"'
    )
    return response


@login_required(login_url="/login/")
@require_GET
def invitados_exportar(request, empresa_slug, evento_id):
    empresa, evento, _return_to = _event_context(request, empresa_slug, evento_id)
    content = build_export_bytes(
        evento,
        base_url=request.build_absolute_uri("/").rstrip("/"),
    )
    safe_name = "".join(
        char if char.isalnum() or char in "-_" else "_"
        for char in str(evento)
    ).strip("_")[:60] or f"evento_{evento.id}"
    response = HttpResponse(
        content,
        content_type=(
            "application/vnd.openxmlformats-officedocument."
            "spreadsheetml.sheet"
        ),
    )
    response["Content-Disposition"] = (
        f'attachment; filename="DIRTEC_Invitados_{safe_name}.xlsx"'
    )
    return response


@login_required(login_url="/login/")
@require_POST
def invitados_importar(request, empresa_slug, evento_id):
    empresa, evento, return_to = _event_context(request, empresa_slug, evento_id)
    destination = _workspace_url(empresa, evento, return_to)

    upload = request.FILES.get("archivo_invitados")
    if upload is None:
        messages.error(request, "Selecciona un archivo .xlsx.")
        return redirect(destination)

    suffix = Path(upload.name or "").suffix.lower()
    if suffix != ".xlsx":
        messages.error(request, "La importación acepta únicamente archivos .xlsx.")
        return redirect(destination)

    # Guardrail against accidentally loading very large workbooks into memory.
    if getattr(upload, "size", 0) > 8 * 1024 * 1024:
        messages.error(request, "El archivo supera el límite de 8 MB.")
        return redirect(destination)

    parsed = parse_import_workbook(upload)
    issues = validate_import_against_event(evento, parsed)
    if issues:
        messages.error(
            request,
            f"No se importó ninguna fila. Se encontraron {len(issues)} problema(s).",
        )
        for issue in issues[:12]:
            messages.error(request, str(issue))
        if len(issues) > 12:
            messages.warning(
                request,
                f"Hay {len(issues) - 12} problema(s) adicional(es) en el archivo.",
            )
        return redirect(destination)

    try:
        result = apply_guest_import(
            evento,
            parsed,
            user=request.user,
            request=request,
        )
    except ValidationError as exc:
        messages.error(request, "No se importó ninguna fila.")
        for error in exc.messages[:12]:
            messages.error(request, error)
        return redirect(destination)

    messages.success(
        request,
        (
            f"Importación completada: {result['groups']} invitación(es) "
            f"y {result['people']} persona(s)/lugar(es)."
        ),
    )
    return redirect(destination)
