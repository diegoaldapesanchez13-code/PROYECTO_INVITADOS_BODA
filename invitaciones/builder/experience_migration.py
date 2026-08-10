from copy import deepcopy

from django.db import transaction

from invitaciones.models import AssetInvitacion


DEFAULT_OPEN_LABEL = "Abrir invitacion"


def importar_experience_legacy(diseno, usuario=None):
    """Import legacy envelope/music fields into document.experience once."""
    evento = diseno.evento
    if not _tiene_fuente_legacy(evento):
        return _resultado(False)

    documento = _documento_v4_base(diseno.documento_builder_borrador)
    if _experience_configurada(documento):
        return _resultado(False)

    with transaction.atomic():
        seal_asset, seal_created = _asset_legacy(
            evento=evento,
            usuario=usuario,
            archivo=getattr(evento, "sello_sobre", None),
            tipo="DECORACION",
            titulo="Sello sobre legacy",
        )
        audio_asset, audio_created = _asset_legacy(
            evento=evento,
            usuario=usuario,
            archivo=getattr(evento, "cancion", None),
            tipo="AUDIO",
            titulo="Cancion legacy",
        )

        seal_asset_id = _builder_asset_id(seal_asset)
        audio_asset_id = _builder_asset_id(audio_asset)
        has_envelope = bool(
            seal_asset_id
            or _texto(getattr(evento, "monograma_sobre", ""))
        )

        documento["experience"] = _legacy_experience(
            evento=evento,
            seal_asset_id=seal_asset_id,
            audio_asset_id=audio_asset_id,
            has_envelope=has_envelope,
        )

        diseno.documento_builder_borrador = documento
        diseno.builder_revision += 1
        if usuario is not None:
            diseno.actualizado_por = usuario

        update_fields = [
            "documento_builder_borrador",
            "builder_revision",
            "fecha_actualizacion",
        ]
        if usuario is not None:
            update_fields.append("actualizado_por")
        diseno.save(update_fields=update_fields)

    return _resultado(
        True,
        seal_asset_id=seal_asset_id,
        audio_asset_id=audio_asset_id,
        assets_created=int(seal_created) + int(audio_created),
    )


def _resultado(applied, seal_asset_id=None, audio_asset_id=None, assets_created=0):
    return {
        "applied": applied,
        "assetsCreated": assets_created if applied else 0,
        "sealAssetId": seal_asset_id,
        "audioAssetId": audio_asset_id,
    }


def _tiene_fuente_legacy(evento):
    return bool(
        _archivo_nombre(getattr(evento, "sello_sobre", None))
        or _archivo_nombre(getattr(evento, "cancion", None))
        or _texto(getattr(evento, "monograma_sobre", ""))
    )


def _documento_v4_base(documento):
    if isinstance(documento, dict):
        output = deepcopy(documento)
    else:
        output = {}

    output["schemaVersion"] = 4
    output.setdefault("page", {})
    output.setdefault("canvases", [])
    output.setdefault("nodes", [])
    output.setdefault("assets", [])
    output.setdefault("responsive", {})
    output.setdefault("meta", {})
    return output


def _experience_configurada(documento):
    if not isinstance(documento, dict):
        return False

    experience = documento.get("experience")
    if not isinstance(experience, dict):
        return False

    intro = experience.get("intro")
    audio = experience.get("audio")
    intro = intro if isinstance(intro, dict) else {}
    audio = audio if isinstance(audio, dict) else {}

    if audio.get("enabled") or audio.get("assetId"):
        return True

    mode = intro.get("mode")
    if intro.get("enabled") or (mode and mode != "NONE"):
        return True

    if intro.get("assetId") or intro.get("posterAssetId"):
        return True

    envelope = intro.get("envelope")
    envelope = envelope if isinstance(envelope, dict) else {}
    return any(
        envelope.get(key)
        for key in (
            "backgroundAssetId",
            "sealAssetId",
            "monogram",
            "message",
        )
    )


def _asset_legacy(*, evento, usuario, archivo, tipo, titulo):
    nombre = _archivo_nombre(archivo)
    if not nombre:
        return None, False

    asset = AssetInvitacion.objects.filter(
        evento=evento,
        tipo=tipo,
        archivo=nombre,
    ).first()
    if asset:
        return asset, False

    return (
        AssetInvitacion.objects.create(
            evento=evento,
            tipo=tipo,
            titulo=titulo,
            archivo=nombre,
            creado_por=usuario,
        ),
        True,
    )


def _legacy_experience(*, evento, seal_asset_id, audio_asset_id, has_envelope):
    return {
        "intro": {
            "enabled": has_envelope,
            "mode": "ENVELOPE" if has_envelope else "NONE",
            "assetId": None,
            "posterAssetId": None,
            "backgroundColor": "#000000",
            "fit": "cover",
            "clickAnywhere": True,
            "showOpenLabel": True,
            "openLabel": _texto(
                getattr(evento, "texto_boton_sobre", "")
            ) or DEFAULT_OPEN_LABEL,
            "allowSkip": True,
            "transition": {
                "type": "FADE",
                "durationMs": 500,
            },
            "envelope": {
                "palette": _texto(getattr(evento, "paleta_sobre", "")) or "CLASSIC",
                "backgroundAssetId": None,
                "sealAssetId": seal_asset_id,
                "monogram": _texto(getattr(evento, "monograma_sobre", "")),
                "message": "",
                "animation": "CLASSIC",
            },
            "video": {
                "controls": False,
                "muted": False,
                "playsInline": True,
                "transitionOnEnded": True,
            },
        },
        "audio": {
            "enabled": bool(audio_asset_id),
            "assetId": audio_asset_id,
            "volume": 0.7,
            "loop": True,
            "showControl": True,
            "startPolicy": "AFTER_INTRO",
        },
    }


def _builder_asset_id(asset):
    return f"db-{asset.id}" if asset else None


def _archivo_nombre(archivo):
    return str(getattr(archivo, "name", "") or "").strip()


def _texto(value):
    return str(value or "").strip()
