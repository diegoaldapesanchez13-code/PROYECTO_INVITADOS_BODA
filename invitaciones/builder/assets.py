import mimetypes
from pathlib import Path

from django.core.exceptions import ValidationError

from invitaciones.models import (
    AssetInvitacion,
    VIDEO_EXTENSIONS,
    extension_archivo,
)


def listar_assets_builder(evento):
    return [
        serializar_asset_builder(asset)
        for asset in evento.assets_invitacion
        .filter(visible=True)
        .order_by("orden", "-fecha_creacion")
    ]


def crear_asset_builder(*, evento, usuario, archivo):
    extension = (
        Path(getattr(archivo, "name", ""))
        .suffix.lower().lstrip(".")
    )

    if extension in VIDEO_EXTENSIONS:
        tipo = "VIDEO"
    elif extension == "gif":
        tipo = "GIF"
    else:
        tipo = "DECORACION"

    titulo = (
        Path(getattr(archivo, "name", "Recurso"))
        .stem.replace("_", " ").replace("-", " ").strip()
        or "Recurso"
    )

    asset = AssetInvitacion(
        evento=evento,
        seccion=None,
        tipo=tipo,
        titulo=titulo[:120],
        archivo=archivo,
        creado_por=usuario,
    )

    # FileField validators are not automatically executed by save().
    asset.full_clean()
    asset.save()
    return asset


def serializar_asset_builder(asset):
    extension = extension_archivo(asset.archivo)
    mime_type = (
        mimetypes.guess_type(asset.archivo.name)[0]
        or "application/octet-stream"
    )

    is_video = extension in VIDEO_EXTENSIONS
    is_gif = extension == "gif"
    supports_alpha = extension in {"png", "webp", "gif"}

    if is_video:
        builder_type = "VIDEO"
        category = "Videos"
        media_kind = "VIDEO"
    else:
        builder_type = "IMAGE"
        category = "Fotografías"
        media_kind = "IMAGE"

    try:
        size = int(asset.archivo.size or 0)
    except (OSError, ValueError):
        size = 0

    return {
        "id": f"db-{asset.id}",
        "databaseId": asset.id,
        "type": builder_type,
        "source": "UPLOAD",
        "name": asset.titulo or f"Recurso {asset.id}",
        "category": category,
        "collection": "Mis archivos",
        "url": asset.archivo.url,
        "previewUrl": asset.archivo.url,
        "mimeType": mime_type,
        "tags": [
            "upload",
            extension,
        ],
        "favorite": False,
        "order": asset.orden,
        "metadata": {
            "size": size,
            "extension": extension,
            "persistent": True,
            "mediaKind": media_kind,
            "supportsAlpha": supports_alpha,
            "animated": is_gif,
        },
        "createdAt": asset.fecha_creacion.isoformat(),
        "updatedAt": asset.fecha_creacion.isoformat(),
    }


def documento_referencia_asset(value, asset_id):
    target = str(asset_id)

    if isinstance(value, dict):
        if str(value.get("assetId", "")) == target:
            return True
        return any(
            documento_referencia_asset(item, target)
            for item in value.values()
        )

    if isinstance(value, list):
        return any(
            documento_referencia_asset(item, target)
            for item in value
        )

    return False


def asset_esta_referenciado(diseno, asset):
    builder_id = f"db-{asset.id}"
    return (
        documento_referencia_asset(
            diseno.documento_builder_borrador,
            builder_id,
        )
        or documento_referencia_asset(
            diseno.documento_builder_publicado,
            builder_id,
        )
    )
