import json

from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_http_methods, require_POST
from django.middleware.csrf import get_token

from core.services.auditoria import registrar_auditoria
from invitaciones.models import AssetInvitacion, DisenoInvitacion, VersionDisenoInvitacion
from invitaciones.permissions import eventos_visibles_usuario

from .assets import (
    asset_esta_referenciado,
    crear_asset_builder,
    listar_assets_builder,
    serializar_asset_builder,
)

from .services import (
    BUILDER_BUILD_VERSION,
    BuilderDocumentError,
    guardar_documento_builder,
    obtener_diseno_builder,
    snapshot_documento,
    validar_documento_builder,
)


LOGIN_URL = "/login/"


def _evento_visible(request, evento_id):
    return get_object_or_404(
        eventos_visibles_usuario(request.user),
        id=evento_id,
    )


def _json_body(request):
    try:
        return json.loads(request.body.decode("utf-8") or "{}")
    except json.JSONDecodeError as exc:
        raise BuilderDocumentError("Solicitud JSON inválida.") from exc


@login_required(login_url=LOGIN_URL)
def editor(request, evento_id):
    evento = _evento_visible(request, evento_id)
    diseno = obtener_diseno_builder(evento, request.user)

    bootstrap = {
        "eventId": evento.id,
        "schemaVersion": 4,
        "buildVersion": BUILDER_BUILD_VERSION,
        "initialDocument": diseno.documento_builder_borrador or None,
        "revision": diseno.builder_revision,
        "csrfToken": get_token(request),
        "initialAssets": listar_assets_builder(evento),
        "endpoints": {
            "document": reverse("builder_document_api", args=[evento.id]),
            "publish": reverse("builder_publish_api", args=[evento.id]),
            "assets": reverse("builder_assets_api", args=[evento.id]),
            "assetDeleteTemplate": reverse(
                "builder_asset_detail_api",
                args=[evento.id, 999999999],
            ).replace("999999999", "__ASSET_ID__"),
        },
    }

    return render(
        request,
        "invitaciones/builder/editor.html",
        {
            "evento": evento,
            "diseno": diseno,
            "builder_bootstrap": bootstrap,
            "builder_build_version": BUILDER_BUILD_VERSION,
            "dashboard_url": f"/dashboard/?evento={evento.id}#personalizacion",
        },
    )


@login_required(login_url=LOGIN_URL)
@require_http_methods(["GET", "POST"])
def document_api(request, evento_id):
    evento = _evento_visible(request, evento_id)
    diseno = obtener_diseno_builder(evento, request.user)

    if request.method == "GET":
        return JsonResponse(
            {
                "ok": True,
                "document": diseno.documento_builder_borrador or None,
                "revision": diseno.builder_revision,
                "updatedAt": diseno.fecha_actualizacion.isoformat(),
            }
        )

    try:
        payload = _json_body(request)
        base_revision = int(payload.get("baseRevision", 0))
        reset = bool(payload.get("reset", False))
        documento = payload.get("document")

        diseno, saved = guardar_documento_builder(
            evento=evento,
            usuario=request.user,
            documento=documento,
            base_revision=base_revision,
            reset=reset,
        )
    except (BuilderDocumentError, TypeError, ValueError) as exc:
        return JsonResponse(
            {"ok": False, "error": str(exc)},
            status=400,
        )

    if not saved:
        return JsonResponse(
            {
                "ok": False,
                "error": "El documento cambió en otra sesión.",
                "revision": diseno.builder_revision,
                "document": diseno.documento_builder_borrador or None,
            },
            status=409,
        )

    registrar_auditoria(
        usuario=request.user,
        empresa=evento.empresa,
        evento=evento,
        accion="AUTOGUARDAR_DIRTEC_BUILDER",
        modelo="DisenoInvitacion",
        objeto_id=diseno.id,
        descripcion=f"Autoguardó DIRTEC Builder revisión {diseno.builder_revision}.",
        request=request,
    )

    return JsonResponse(
        {
            "ok": True,
            "revision": diseno.builder_revision,
            "updatedAt": diseno.fecha_actualizacion.isoformat(),
        }
    )


@login_required(login_url=LOGIN_URL)
@require_POST
def publish_api(request, evento_id):
    evento = _evento_visible(request, evento_id)

    with transaction.atomic():
        diseno = (
            DisenoInvitacion.objects.select_for_update()
            .get(evento=evento)
        )

        try:
            validar_documento_builder(diseno.documento_builder_borrador)
        except BuilderDocumentError as exc:
            return JsonResponse(
                {"ok": False, "error": str(exc)},
                status=400,
            )

        diseno.documento_builder_publicado = snapshot_documento(
            diseno.documento_builder_borrador
        )
        diseno.estado = "PUBLICADO"
        diseno.publicado_en = timezone.now()
        diseno.actualizado_por = request.user
        diseno.save(
            update_fields=[
                "documento_builder_publicado",
                "estado",
                "publicado_en",
                "actualizado_por",
                "fecha_actualizacion",
            ]
        )

        VersionDisenoInvitacion.objects.create(
            diseno=diseno,
            nombre=f"DIRTEC Builder publicado {timezone.now().strftime('%d/%m/%Y %H:%M')}",
            configuracion={
                "_format": (
                    "DIRTEC_BUILDER_V4"
                    if diseno.documento_builder_publicado.get("schemaVersion") == 4
                    else "DIRTEC_BUILDER_V3"
                ),
                "schemaVersion": diseno.documento_builder_publicado.get(
                    "schemaVersion",
                    3,
                ),
                "document": snapshot_documento(diseno.documento_builder_publicado),
            },
            publicado=True,
            creado_por=request.user,
        )

    registrar_auditoria(
        usuario=request.user,
        empresa=evento.empresa,
        evento=evento,
        accion="PUBLICAR_DIRTEC_BUILDER",
        modelo="DisenoInvitacion",
        objeto_id=diseno.id,
        descripcion="Publicó un snapshot del DIRTEC Builder.",
        request=request,
    )

    return JsonResponse(
        {
            "ok": True,
            "revision": diseno.builder_revision,
            "publishedAt": diseno.publicado_en.isoformat(),
        }
    )


@login_required(login_url=LOGIN_URL)
@require_http_methods(["GET", "POST"])
def assets_api(request, evento_id):
    evento = _evento_visible(request, evento_id)

    if request.method == "GET":
        return JsonResponse(
            {
                "ok": True,
                "assets": listar_assets_builder(evento),
            }
        )

    archivo = request.FILES.get("archivo")
    if not archivo:
        return JsonResponse(
            {
                "ok": False,
                "error": "Selecciona una imagen, video o audio.",
            },
            status=400,
        )

    try:
        asset = crear_asset_builder(
            evento=evento,
            usuario=request.user,
            archivo=archivo,
        )
    except Exception as exc:
        # ValidationError contains user-safe extension/size messages in this project.
        messages = getattr(exc, "messages", None)
        message = " ".join(messages) if messages else str(exc)
        return JsonResponse(
            {
                "ok": False,
                "error": message or "Archivo inválido.",
            },
            status=400,
        )

    registrar_auditoria(
        usuario=request.user,
        empresa=evento.empresa,
        evento=evento,
        accion="SUBIR_ASSET_DIRTEC_BUILDER",
        modelo="AssetInvitacion",
        objeto_id=asset.id,
        descripcion=f"Subió asset persistente: {asset.titulo or asset.id}.",
        request=request,
    )

    return JsonResponse(
        {
            "ok": True,
            "asset": serializar_asset_builder(asset),
        },
        status=201,
    )


@login_required(login_url=LOGIN_URL)
@require_http_methods(["DELETE"])
def asset_detail_api(request, evento_id, asset_id):
    evento = _evento_visible(request, evento_id)
    asset = get_object_or_404(
        AssetInvitacion,
        id=asset_id,
        evento=evento,
    )
    diseno = obtener_diseno_builder(evento, request.user)

    if asset_esta_referenciado(diseno, asset):
        return JsonResponse(
            {
                "ok": False,
                "error": (
                    "Este recurso está siendo utilizado por el diseño. "
                    "Retíralo del lienzo antes de eliminarlo."
                ),
            },
            status=409,
        )

    titulo = asset.titulo or str(asset.id)
    asset.delete()

    registrar_auditoria(
        usuario=request.user,
        empresa=evento.empresa,
        evento=evento,
        accion="ELIMINAR_ASSET_DIRTEC_BUILDER",
        modelo="AssetInvitacion",
        objeto_id=asset_id,
        descripcion=f"Eliminó asset persistente: {titulo}.",
        request=request,
    )

    return JsonResponse(
        {
            "ok": True,
            "assetId": f"db-{asset_id}",
        }
    )
