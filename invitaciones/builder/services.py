from copy import deepcopy

from django.db import transaction

from invitaciones.models import DisenoInvitacion
from .experience_migration import importar_experience_legacy


BUILDER_SCHEMA_VERSION = 4
LEGACY_BUILDER_SCHEMA_VERSION = 3
BUILDER_BUILD_VERSION = "f4-native-v4-freeze"


class BuilderDocumentError(ValueError):
    pass


def obtener_diseno_builder(evento, usuario=None):
    diseno, _ = DisenoInvitacion.objects.get_or_create(
        evento=evento,
        defaults={
            "configuracion_borrador": DisenoInvitacion.configuracion_inicial(evento),
            "actualizado_por": usuario,
        },
    )
    importar_experience_legacy(diseno, usuario=usuario)
    return diseno


def validar_documento_builder(documento):
    if not isinstance(documento, dict):
        raise BuilderDocumentError("El documento debe ser un objeto JSON.")

    version = documento.get("schemaVersion")

    if version == BUILDER_SCHEMA_VERSION:
        if not isinstance(documento.get("canvases"), list):
            raise BuilderDocumentError("El documento V4 requiere canvases[].")
        if not isinstance(documento.get("nodes"), list):
            raise BuilderDocumentError("El documento V4 requiere nodes[].")
        return documento

    if version == LEGACY_BUILDER_SCHEMA_VERSION:
        if not isinstance(documento.get("sections"), list):
            raise BuilderDocumentError("El documento V3 requiere sections[].")
        if not isinstance(documento.get("nodes"), list):
            raise BuilderDocumentError("El documento V3 requiere nodes[].")
        return documento

    raise BuilderDocumentError(
        "Schema no soportado. Se esperaba V4 "
        "(V3 se admite solo durante la migración)."
    )


def snapshot_documento(documento):
    return deepcopy(documento)


@transaction.atomic
def guardar_documento_builder(*, evento, usuario, documento, base_revision, reset=False):
    diseno = (
        DisenoInvitacion.objects.select_for_update()
        .get(evento=evento)
    )

    if int(base_revision or 0) != diseno.builder_revision:
        return diseno, False

    if reset:
        documento_normalizado = {}
    else:
        documento_normalizado = snapshot_documento(
            validar_documento_builder(documento)
        )

    diseno.documento_builder_borrador = documento_normalizado
    diseno.builder_revision += 1
    diseno.actualizado_por = usuario
    if diseno.documento_builder_publicado:
        diseno.estado = "PUBLICADO"
    else:
        diseno.estado = "BORRADOR"

    diseno.save(
        update_fields=[
            "documento_builder_borrador",
            "builder_revision",
            "actualizado_por",
            "estado",
            "fecha_actualizacion",
        ]
    )
    return diseno, True
