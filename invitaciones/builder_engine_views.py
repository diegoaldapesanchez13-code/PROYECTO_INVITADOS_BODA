import json
from copy import deepcopy

from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST

from .models import (
    DisenoInvitacion,
    EventoBoda,
    VersionDisenoInvitacion,
)
from .permissions import eventos_visibles_usuario


BUILDER_SCHEMA_VERSION = 1
BUILDER_ENGINE_VERSION = "0.14.0"
MAX_DOCUMENT_BYTES = 5 * 1024 * 1024


def _evento_editor_para_usuario(request, evento_id):
    return get_object_or_404(
        eventos_visibles_usuario(request.user),
        id=evento_id,
    )


def _diseno_para_evento(evento):
    diseno, _ = DisenoInvitacion.objects.get_or_create(
        evento=evento,
        defaults={
            "nombre": "Diseño principal",
            "configuracion_borrador": {},
        },
    )
    return diseno


def _documento_vacio(evento):
    ahora = timezone.now().isoformat()
    return {
        "schemaVersion": BUILDER_SCHEMA_VERSION,
        "documentVersion": 1,
        "builderVersion": BUILDER_ENGINE_VERSION,
        "metadata": {
            "id": None,
            "eventId": evento.id,
            "name": evento.nombre_evento or evento.titulo_evento,
            "status": "draft",
            "createdAt": ahora,
            "updatedAt": ahora,
        },
        "theme": {},
        "assets": [],
        "globals": {},
        "canvases": [],
    }


def _normalizar_documento_guardado(evento, configuracion):
    if (
        isinstance(configuracion, dict)
        and configuracion.get("schemaVersion") == BUILDER_SCHEMA_VERSION
        and isinstance(configuracion.get("canvases"), list)
    ):
        documento = deepcopy(configuracion)
        metadata = documento.setdefault("metadata", {})
        metadata["eventId"] = evento.id
        return documento

    documento = _documento_vacio(evento)

    # El diseño anterior se conserva completo para una migración posterior
    # sin continuar usándolo como contrato principal del Engine.
    if isinstance(configuracion, dict) and configuracion:
        documento["globals"]["legacyEditorConfig"] = deepcopy(configuracion)
        documento["globals"]["legacyMigrationPending"] = True

    return documento


def _leer_json_request(request):
    if len(request.body) > MAX_DOCUMENT_BYTES:
        raise ValueError("El documento excede el límite permitido de 5 MB.")

    try:
        payload = json.loads(request.body.decode("utf-8") or "{}")
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("El cuerpo JSON no es válido.") from exc

    if not isinstance(payload, dict):
        raise ValueError("El cuerpo debe ser un objeto JSON.")

    return payload


def _buscar_fuentes_temporales(value, ruta="document"):
    errores = []

    if isinstance(value, dict):
        for clave, item in value.items():
            errores.extend(
                _buscar_fuentes_temporales(item, f"{ruta}.{clave}")
            )
    elif isinstance(value, list):
        for indice, item in enumerate(value):
            errores.extend(
                _buscar_fuentes_temporales(item, f"{ruta}[{indice}]")
            )
    elif isinstance(value, str):
        texto = value.strip().lower()
        if texto.startswith("data:"):
            errores.append(f"{ruta}: Base64/data URL no permitido.")
        elif texto.startswith("blob:"):
            errores.append(f"{ruta}: blob URL temporal no permitido.")

    return errores


def _validar_documento(documento, evento):
    errores = []

    if not isinstance(documento, dict):
        return ["document debe ser un objeto."]

    if documento.get("schemaVersion") != BUILDER_SCHEMA_VERSION:
        errores.append(
            f"schemaVersion debe ser {BUILDER_SCHEMA_VERSION}."
        )

    for campo in ("metadata", "theme", "globals"):
        if not isinstance(documento.get(campo), dict):
            errores.append(f"{campo} debe ser un objeto.")

    for campo in ("assets", "canvases"):
        if not isinstance(documento.get(campo), list):
            errores.append(f"{campo} debe ser un arreglo.")

    metadata = documento.get("metadata")
    if isinstance(metadata, dict):
        event_id = metadata.get("eventId")
        if event_id not in (None, evento.id, str(evento.id)):
            errores.append("metadata.eventId no corresponde al evento.")

    errores.extend(_buscar_fuentes_temporales(documento))
    return errores


def _preparar_documento_para_guardar(documento, evento, estado):
    resultado = deepcopy(documento)
    resultado["schemaVersion"] = BUILDER_SCHEMA_VERSION
    resultado["builderVersion"] = str(
        resultado.get("builderVersion") or BUILDER_ENGINE_VERSION
    )
    resultado["documentVersion"] = max(
        int(resultado.get("documentVersion") or 1),
        1,
    )

    metadata = resultado.setdefault("metadata", {})
    metadata["eventId"] = evento.id
    metadata["name"] = (
        metadata.get("name")
        or evento.nombre_evento
        or evento.titulo_evento
    )
    metadata["status"] = estado
    metadata.setdefault("createdAt", timezone.now().isoformat())
    metadata["updatedAt"] = timezone.now().isoformat()

    return resultado


@login_required
@require_GET
def cargar_documento_builder(request, evento_id):
    evento = _evento_editor_para_usuario(request, evento_id)
    diseno = _diseno_para_evento(evento)

    documento = _normalizar_documento_guardado(
        evento,
        diseno.configuracion_borrador,
    )

    return JsonResponse({
        "ok": True,
        "document": documento,
        "design": {
            "id": diseno.id,
            "status": diseno.estado,
            "hasPublished": diseno.tiene_publicacion,
            "updatedAt": diseno.fecha_actualizacion.isoformat(),
        },
    })


@login_required
@require_POST
@transaction.atomic
def guardar_documento_builder(request, evento_id):
    evento = _evento_editor_para_usuario(request, evento_id)
    diseno = _diseno_para_evento(evento)

    try:
        payload = _leer_json_request(request)
    except ValueError as exc:
        return JsonResponse(
            {"ok": False, "error": str(exc)},
            status=400,
        )

    documento = payload.get("document")
    errores = _validar_documento(documento, evento)
    if errores:
        return JsonResponse(
            {"ok": False, "error": "Documento inválido.", "errors": errores},
            status=400,
        )

    documento = _preparar_documento_para_guardar(
        documento,
        evento,
        "draft",
    )

    diseno.configuracion_borrador = documento
    diseno.estado = "BORRADOR"
    diseno.actualizado_por = request.user
    diseno.save(update_fields=[
        "configuracion_borrador",
        "estado",
        "actualizado_por",
        "fecha_actualizacion",
    ])

    return JsonResponse({
        "ok": True,
        "documentVersion": documento["documentVersion"],
        "savedAt": diseno.fecha_actualizacion.isoformat(),
        "reason": str(payload.get("reason") or "manual"),
    })


@login_required
@require_POST
@transaction.atomic
def publicar_documento_builder(request, evento_id):
    evento = _evento_editor_para_usuario(request, evento_id)
    diseno = _diseno_para_evento(evento)

    try:
        payload = _leer_json_request(request)
    except ValueError as exc:
        return JsonResponse(
            {"ok": False, "error": str(exc)},
            status=400,
        )

    documento = payload.get("document")
    errores = _validar_documento(documento, evento)
    if errores:
        return JsonResponse(
            {"ok": False, "error": "Documento inválido.", "errors": errores},
            status=400,
        )

    documento_publicado = _preparar_documento_para_guardar(
        documento,
        evento,
        "published",
    )

    diseno.configuracion_borrador = deepcopy(documento_publicado)
    diseno.configuracion_publicada = deepcopy(documento_publicado)
    diseno.estado = "PUBLICADO"
    diseno.publicado_en = timezone.now()
    diseno.actualizado_por = request.user
    diseno.save(update_fields=[
        "configuracion_borrador",
        "configuracion_publicada",
        "estado",
        "publicado_en",
        "actualizado_por",
        "fecha_actualizacion",
    ])

    VersionDisenoInvitacion.objects.create(
        diseno=diseno,
        nombre=f"Publicación {timezone.localtime().strftime('%d/%m/%Y %H:%M')}",
        configuracion=deepcopy(documento_publicado),
        publicado=True,
        creado_por=request.user,
    )

    return JsonResponse({
        "ok": True,
        "publishedAt": diseno.publicado_en.isoformat(),
        "documentVersion": documento_publicado["documentVersion"],
    })
