import json

from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_http_methods
from django.views.decorators.clickjacking import xframe_options_sameorigin

from invitaciones.models import DisenoInvitacion, Grupoinvitacion, Invitado
from invitaciones.rsvp_control import evaluar_rsvp
from .assets import listar_assets_builder
from .event_context import serializar_contexto_evento
from .invitation_context import serializar_contexto_invitacion
from .services import BUILDER_BUILD_VERSION, snapshot_documento


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
    try:
        from core.services.authorization import Actions, usuario_puede_evento
        return usuario_puede_evento(user, evento, Actions.EVENT_BUILDER)
    except Exception:
        return False


def _invitados_frescos(grupo):
    """Return the current RSVP roster directly from the database."""
    return list(
        Invitado.objects
        .filter(grupo_id=grupo.pk)
        .order_by("orden", "id")
    )


def _rsvp_payload(grupo):
    invitados = _invitados_frescos(grupo)
    payload = serializar_contexto_invitacion(
        grupo,
        invitados=invitados,
        include_guests=True,
    )
    payload["rsvpControl"] = evaluar_rsvp(grupo).as_dict()
    return payload


def _sync_group_legacy_summary(grupo):
    """Keep legacy group reporting coherent while Invitado remains authority."""
    invitados = _invitados_frescos(grupo)
    total = len(invitados)
    yes_count = sum(
        1
        for invitado in invitados
        if invitado.asistira is True
    )
    responded = sum(
        1
        for invitado in invitados
        if invitado.asistira is not None
    )
    pending = total - responded

    grupo.cantidad_confirmada = yes_count
    grupo.confirmado = total > 0 and pending == 0
    grupo.fecha_confirmacion = (
        timezone.now()
        if responded
        else None
    )

    if total == 0:
        grupo.asistira = None
    elif pending:
        grupo.asistira = None
    else:
        grupo.asistira = yes_count > 0

    grupo.save(update_fields=[
        "cantidad_confirmada",
        "confirmado",
        "fecha_confirmacion",
        "asistira",
    ])


@xframe_options_sameorigin
@ensure_csrf_cookie
def public_invitation(request, codigo):
    grupo = _grupo(codigo)
    evento = grupo.evento
    diseno = DisenoInvitacion.objects.filter(evento=evento).first()

    preview = (
        request.GET.get("preview") == "1"
        and _puede_ver_borrador(request, evento)
    )
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

    rsvp_control = evaluar_rsvp(grupo).as_dict()
    bootstrap = {
        "schemaVersion": 4,
        "buildVersion": BUILDER_BUILD_VERSION,
        "document": snapshot_documento(document),
        "assets": listar_assets_builder(evento),
        "device": "mobile",
        "preview": preview,
        "event": serializar_contexto_evento(evento),
        "invitation": _rsvp_payload(grupo),
        "endpoints": {
            "rsvp": reverse(
                "builder_public_rsvp_api",
                args=[grupo.codigo],
            ),
        },
    }

    return render(
        request,
        "invitaciones/builder/public_invitation.html",
        {
            "evento": evento,
            "grupo": grupo,
            "builder_public_bootstrap": bootstrap,
            "builder_build_version": BUILDER_BUILD_VERSION,
            "rsvp_control": rsvp_control,
        },
    )


@require_http_methods(["GET", "POST"])
def public_rsvp_api(request, codigo):
    grupo = _grupo(codigo)
    decision = evaluar_rsvp(grupo)

    if request.method == "GET":
        return JsonResponse({
            "ok": True,
            "data": _rsvp_payload(grupo),
        })

    # Server-side enforcement is the authority. Hiding or disabling a browser
    # control is not considered sufficient protection.
    if not decision.permitido:
        return JsonResponse(
            {
                "ok": False,
                "error": decision.message,
                "code": "RSVP_CLOSED",
                "rsvpControl": decision.as_dict(),
            },
            status=403,
        )

    try:
        payload = json.loads(
            request.body.decode("utf-8")
            or "{}"
        )
    except json.JSONDecodeError:
        return JsonResponse(
            {
                "ok": False,
                "error": "Solicitud JSON inválida.",
            },
            status=400,
        )

    attending = payload.get("attending")
    if attending not in (True, False):
        return JsonResponse(
            {
                "ok": False,
                "error": "Selecciona si asistirás.",
            },
            status=400,
        )

    guest_id = payload.get("guestId")
    try:
        guest_id = int(guest_id)
    except (TypeError, ValueError):
        return JsonResponse(
            {
                "ok": False,
                "error": "Invitado inválido.",
            },
            status=400,
        )

    with transaction.atomic():
        invitado = (
            Invitado.objects
            .select_for_update()
            .filter(
                pk=guest_id,
                grupo_id=grupo.id,
            )
            .first()
        )

        if invitado is None:
            return JsonResponse(
                {
                    "ok": False,
                    "error": (
                        "El invitado no pertenece "
                        "a esta invitación."
                    ),
                },
                status=404,
            )

        invitado.asistira = attending
        invitado.fecha_confirmacion = timezone.now()
        invitado.save(
            update_fields=[
                "asistira",
                "fecha_confirmacion",
            ]
        )

        _sync_group_legacy_summary(grupo)

    grupo = _grupo(codigo)

    return JsonResponse({
        "ok": True,
        "message": (
            f"Respuesta de {invitado.nombre} guardada."
        ),
        "data": _rsvp_payload(grupo),
    })
