from pathlib import Path

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_GET

from .models import AssetInvitacion
from .permissions import eventos_visibles_usuario


IMAGE_EXTENSIONS = {"jpg", "jpeg", "png", "webp", "gif"}
VIDEO_EXTENSIONS = {"mp4", "webm", "ogg", "mov", "m4v"}


def _evento_para_usuario(request, evento_id):
    return get_object_or_404(
        eventos_visibles_usuario(request.user),
        id=evento_id,
    )


def _tipo_engine(asset):
    extension = Path(asset.archivo.name or "").suffix.lower().lstrip(".")
    if asset.es_video or extension in VIDEO_EXTENSIONS:
        return "VIDEO"
    if extension == "gif" or asset.tipo == "GIF":
        return "GIF"
    return "IMAGE"


def _mime_type(asset):
    extension = Path(asset.archivo.name or "").suffix.lower().lstrip(".")
    return {
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "png": "image/png",
        "webp": "image/webp",
        "gif": "image/gif",
        "mp4": "video/mp4",
        "webm": "video/webm",
        "ogg": "video/ogg",
        "mov": "video/quicktime",
        "m4v": "video/x-m4v",
    }.get(extension, "application/octet-stream")


def serializar_asset_builder(asset):
    archivo = asset.archivo
    try:
        size = archivo.size
    except (FileNotFoundError, OSError, ValueError):
        size = 0

    return {
        "id": str(asset.id),
        "backendId": asset.id,
        "eventId": asset.evento_id,
        "sectionId": asset.seccion_id,
        "type": _tipo_engine(asset),
        "category": asset.tipo,
        "source": "UPLOAD",
        "name": asset.titulo or Path(archivo.name).name,
        "url": archivo.url if archivo else "",
        "mimeType": _mime_type(asset),
        "size": size,
        "visible": asset.visible,
        "order": asset.orden,
        "createdAt": asset.fecha_creacion.isoformat(),
        "metadata": {
            "legacyType": asset.tipo,
            "isVideo": asset.es_video,
            "filename": Path(archivo.name).name,
        },
    }


@login_required
@require_GET
def listar_assets_builder(request, evento_id):
    evento = _evento_para_usuario(request, evento_id)

    queryset = (
        AssetInvitacion.objects
        .filter(evento=evento, visible=True)
        .select_related("seccion")
        .order_by("orden", "-fecha_creacion", "-id")
    )

    requested_type = (request.GET.get("type") or "").strip().upper()
    query = (request.GET.get("q") or "").strip().lower()

    assets = [serializar_asset_builder(asset) for asset in queryset]

    if requested_type in {"IMAGE", "VIDEO", "GIF"}:
        assets = [
            asset for asset in assets
            if asset["type"] == requested_type
        ]

    if query:
        assets = [
            asset for asset in assets
            if query in asset["name"].lower()
            or query in asset["category"].lower()
            or query in asset["metadata"]["filename"].lower()
        ]

    totals = {
        "all": len(assets),
        "images": sum(asset["type"] in {"IMAGE", "GIF"} for asset in assets),
        "videos": sum(asset["type"] == "VIDEO" for asset in assets),
        "bytes": sum(asset["size"] for asset in assets),
    }

    return JsonResponse({
        "ok": True,
        "eventId": evento.id,
        "assets": assets,
        "totals": totals,
    })
