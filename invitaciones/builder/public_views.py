import json

from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_http_methods
from django.views.decorators.clickjacking import xframe_options_sameorigin

from invitaciones.models import DisenoInvitacion, Grupoinvitacion
from .assets import listar_assets_builder
from .services import snapshot_documento


def _grupo(codigo):
    return get_object_or_404(
        Grupoinvitacion.objects.select_related("evento").prefetch_related("invitados"),
        codigo=codigo,
    )


def _puede_ver_borrador(request, evento):
    user = request.user
    if not getattr(user, "is_authenticated", False):
        return False
    if getattr(user, "is_superuser", False):
        return True
    # El editor ya aplica aislamiento por empresa. Para preview público
    # conservamos una regla estricta y no exponemos borrador a invitados.
    try:
        from invitaciones.permissions import eventos_visibles_usuario
        return eventos_visibles_usuario(user).filter(pk=evento.pk).exists()
    except Exception:
        return False


def _rsvp_payload(grupo):
    max_guests = max(int(grupo.total_lugares or grupo.cantidad_maxima or 1), 1)
    confirmed = grupo.cantidad_confirmada
    if confirmed is None:
        confirmed = grupo.lugares_asistiran if grupo.asistira is not None else 1
    return {
        "invitationId": str(grupo.codigo),
        "groupName": grupo.nombre_grupo,
        "maxGuests": max_guests,
        "attending": grupo.asistira,
        "confirmedGuests": min(max(int(confirmed or 0), 0), max_guests),
        "comment": grupo.comentario or "",
    }


@xframe_options_sameorigin
@ensure_csrf_cookie
def public_invitation(request, codigo):
    grupo = _grupo(codigo)
    evento = grupo.evento
    diseno = DisenoInvitacion.objects.filter(evento=evento).first()

    preview = request.GET.get("preview") == "1" and _puede_ver_borrador(request, evento)
    document = {}
    if diseno:
        document = (
            diseno.documento_builder_borrador
            if preview
            else diseno.documento_builder_publicado
        ) or {}

    if not document:
        return render(
            request,
            "invitaciones/builder/not_published.html",
            {
                "evento": evento,
                "grupo": grupo,
            },
            status=404,
        )

    bootstrap = {
        "schemaVersion": 3,
        "document": snapshot_documento(document),
        "assets": listar_assets_builder(evento),
        "device": "mobile",
        "preview": preview,
        "invitation": _rsvp_payload(grupo),
        "endpoints": {
            "rsvp": reverse("builder_public_rsvp_api", args=[grupo.codigo]),
        },
    }
    return render(request, "invitaciones/builder/public_invitation.html", {
        "evento": evento,
        "grupo": grupo,
        "builder_public_bootstrap": bootstrap,
    })


@require_http_methods(["GET", "POST"])
def public_rsvp_api(request, codigo):
    grupo = _grupo(codigo)
    if request.method == "GET":
        return JsonResponse({"ok": True, "data": _rsvp_payload(grupo)})

    try:
        payload = json.loads(request.body.decode("utf-8") or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"ok": False, "error": "Solicitud JSON inválida."}, status=400)

    attending = payload.get("attending")
    if attending not in (True, False):
        return JsonResponse({"ok": False, "error": "Selecciona si asistirás."}, status=400)

    max_guests = max(int(grupo.total_lugares or grupo.cantidad_maxima or 1), 1)
    try:
        confirmed = int(payload.get("confirmedGuests", 1 if attending else 0))
    except (TypeError, ValueError):
        confirmed = 1 if attending else 0
    confirmed = min(max(confirmed, 1 if attending else 0), max_guests) if attending else 0

    grupo.asistira = attending
    grupo.cantidad_confirmada = confirmed
    grupo.comentario = str(payload.get("comment") or "").strip()[:5000]
    grupo.confirmado = True
    grupo.fecha_confirmacion = timezone.now()

    # Mantiene coherencia de métricas existentes. En grupos con personas
    # individuales no inventamos quién asistirá: el Builder V3 confirma el grupo.
    if grupo.es_personal and not grupo.invitados.exists():
        grupo.acompanantes_adultos = max(confirmed - 1, 0) if attending else 0
        grupo.acompanantes_ninos = 0

    grupo.save()
    return JsonResponse({
        "ok": True,
        "message": "Confirmación guardada.",
        "data": _rsvp_payload(grupo),
    })
