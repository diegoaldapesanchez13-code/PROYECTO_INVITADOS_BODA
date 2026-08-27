import hashlib
import io
import json
import posixpath
import zipfile
from datetime import date, datetime, timedelta
from decimal import Decimal
from pathlib import PurePosixPath

from django.apps import apps
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.files.storage import default_storage
from django.db import transaction
from django.db.models.deletion import Collector, ProtectedError, RestrictedError
from django.db.models.fields.files import FieldFile, FileField
from django.utils import timezone

from core.services.authorization import Actions, usuario_puede_evento
from core.services.permisos import usuario_es_dirtec_operativo

from .event_domain import evaluar_purga_evento
from .models import ExpedienteHistoricoEvento


ARCHIVE_FORMAT = "K9_D6_FULL_V2"
PURGE_ARCHIVE_FORMAT = "K9_D6_PURGE_READY_V3"
EXPORTABLE_STATES = {"FINALIZADO", "CANCELADO", "ARCHIVADO"}
RETENTION_DAYS_HISTORICAL = 30


def _primitive(value):
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, FieldFile):
        return value.name or None
    return str(value)


def _serialize_instance(obj):
    row = {}
    for field in obj._meta.concrete_fields:
        try:
            value = getattr(obj, field.name)
        except Exception:
            continue
        if field.is_relation:
            row[field.attname] = _primitive(getattr(obj, field.attname, None))
        else:
            row[field.name] = _primitive(value)
    return row


def _objects_for_event(evento):
    """
    Canonical D6.2 event graph used by both JSON export and binary discovery.
    Keeping objects here avoids guessing file fields from their names.
    """
    PropuestaLinea = apps.get_model("paquetes", "PropuestaLinea")
    return {
        "evento": [evento],
        "participantes": list(evento.participantes_evento.all()),
        "propuestas": list(evento.propuestas_k9.all()),
        "propuesta_lineas": list(
            PropuestaLinea.objects.filter(propuesta__evento=evento)
            .order_by("propuesta_id", "orden", "id")
        ),
        "contratos": list(evento.contratos_evento.all()),
        "servicios": list(evento.servicios_contratados.all()),
        "gastos": list(evento.gastos_evento.all()),
        "pagos_cliente": list(evento.pagos_cliente_reportados.all()),
        "documentos": list(evento.documentos_evento.all()),
        "tareas": list(evento.tareas_evento.all()),
        "agenda": list(evento.actividades_itinerario.all()),
        "grupos_invitacion": list(evento.grupos.all()),
        "expedientes_colaboracion": list(evento.expedientes_servicio.all()),
        "ajustes_contractuales": list(
            getattr(evento, "ajustes_contractuales_servicio").all()
        ) if hasattr(evento, "ajustes_contractuales_servicio") else [],
    }


def _core_payload(objects):
    payload = {}
    for section, rows in objects.items():
        serialized = [_serialize_instance(obj) for obj in rows]
        payload[section] = serialized[0] if section == "evento" and serialized else serialized
    return payload


def _safe_archive_name(section, obj, field, storage_name):
    base = PurePosixPath(str(storage_name).replace("\\", "/")).name or "archivo"
    obj_id = getattr(obj, "pk", None) or "sin_id"
    return posixpath.join(
        "files",
        section,
        str(obj_id),
        field.name,
        base,
    )


def _binary_inventory(objects):
    inventory = []
    seen = set()
    for section, rows in objects.items():
        for obj in rows:
            for field in obj._meta.concrete_fields:
                if not isinstance(field, FileField):
                    continue
                value = getattr(obj, field.name, None)
                storage_name = getattr(value, "name", "") if value else ""
                if not storage_name:
                    continue

                key = (section, obj._meta.label_lower, obj.pk, field.name, storage_name)
                if key in seen:
                    continue
                seen.add(key)
                inventory.append({
                    "seccion": section,
                    "modelo": obj._meta.label_lower,
                    "registro_id": obj.pk,
                    "campo": field.name,
                    "storage_name": storage_name,
                    "archive_path": _safe_archive_name(
                        section, obj, field, storage_name
                    ),
                    "estado": "PENDIENTE",
                    "sha256": None,
                    "tamano_bytes": None,
                })
    return inventory


def _ultimo_expediente_completo(evento):
    return (
        ExpedienteHistoricoEvento.objects.filter(
            empresa=evento.empresa,
            evento_id_snapshot=evento.id,
            formato=ARCHIVE_FORMAT,
            completo_para_purga_historica=True,
            integridad_verificada=True,
        )
        .order_by("-generado_en", "-id")
        .first()
    )


def evaluar_ciclo_datos_evento(evento):
    purge = evaluar_purga_evento(evento)
    ultimo = ExpedienteHistoricoEvento.objects.filter(
        empresa=evento.empresa,
        evento_id_snapshot=evento.id,
    ).order_by("-generado_en", "-id").first()
    completo = _ultimo_expediente_completo(evento)
    now = timezone.now()

    respaldo_confirmado = bool(
        completo and completo.respaldo_externo_confirmado_en
    )
    retencion_cumplida = bool(
        respaldo_confirmado
        and completo.retencion_hasta
        and completo.retencion_hasta <= now
    )
    autorizada = bool(
        completo and completo.purga_historica_autorizada_en
    )

    return {
        "estado": evento.estado,
        "exportable": evento.estado in EXPORTABLE_STATES,
        "archivado": evento.estado == "ARCHIVADO",
        "purga_descartable_permitida": evento.estado == "ARCHIVADO" and purge.permitido,
        "purga_historica_permitida": False,
        "expediente_completo_disponible": bool(completo),
        "respaldo_externo_confirmado": respaldo_confirmado,
        "retencion_hasta": completo.retencion_hasta if completo else None,
        "retencion_cumplida": retencion_cumplida,
        "purga_historica_autorizada": autorizada,
        "expediente_para_retencion": completo,
        "motivos_proteccion": list(purge.motivos),
        "politica": (
            "DESCARTABLE"
            if evento.estado == "ARCHIVADO" and purge.permitido
            else "HISTORICO_PROTEGIDO"
        ),
    }


def confirmar_respaldo_externo(evento, *, expediente, user, sha256):
    if not usuario_puede_evento(user, evento, Actions.EVENT_EDIT):
        raise PermissionDenied("No tienes permiso para confirmar el respaldo externo.")
    if expediente.evento_id_snapshot != evento.id or expediente.empresa_id != evento.empresa_id:
        raise ValidationError("El expediente no pertenece a este evento.")
    if not (
        expediente.formato in {ARCHIVE_FORMAT, PURGE_ARCHIVE_FORMAT}
        and expediente.integridad_verificada
        and expediente.completo_para_purga_historica
        and expediente.binarios_faltantes == 0
    ):
        raise ValidationError(
            "Solo un expediente D6.2 completo e integro puede confirmarse como respaldo externo."
        )

    supplied = (sha256 or "").strip().lower()
    if supplied != expediente.sha256.lower():
        raise ValidationError(
            "El SHA-256 no coincide con el expediente descargado."
        )

    if expediente.respaldo_externo_confirmado_en:
        return expediente

    now = timezone.now()
    expediente.respaldo_externo_confirmado_en = now
    expediente.respaldo_externo_confirmado_por = user
    expediente.retencion_hasta = now + timedelta(days=RETENTION_DAYS_HISTORICAL)
    expediente.save(
        update_fields=[
            "respaldo_externo_confirmado_en",
            "respaldo_externo_confirmado_por",
            "retencion_hasta",
        ]
    )
    return expediente


def autorizar_purga_historica(evento, *, expediente, user, motivo):
    if not usuario_es_dirtec_operativo(user):
        raise PermissionDenied(
            "Solo DIRTEC puede autorizar la purga de un evento con historial real."
        )
    if evento.estado != "ARCHIVADO":
        raise ValidationError(
            "El evento debe estar archivado antes de autorizar una purga historica."
        )
    if expediente.evento_id_snapshot != evento.id or expediente.empresa_id != evento.empresa_id:
        raise ValidationError("El expediente no pertenece a este evento.")
    if not expediente.respaldo_externo_confirmado_en:
        raise ValidationError("Primero confirma la custodia externa del expediente.")
    if not expediente.retencion_hasta or expediente.retencion_hasta > timezone.now():
        raise ValidationError(
            "El periodo minimo de retencion aun no ha finalizado."
        )

    motivo = " ".join((motivo or "").split()).strip()
    if len(motivo) < 10:
        raise ValidationError(
            "Indica un motivo de autorizacion de al menos 10 caracteres."
        )

    expediente.purga_historica_autorizada_en = timezone.now()
    expediente.purga_historica_autorizada_por = user
    expediente.motivo_autorizacion_purga = motivo
    expediente.save(
        update_fields=[
            "purga_historica_autorizada_en",
            "purga_historica_autorizada_por",
            "motivo_autorizacion_purga",
        ]
    )
    return expediente


def _write_binary_files(archive, inventory):
    found = 0
    missing = 0
    for item in inventory:
        storage_name = item["storage_name"]
        try:
            with default_storage.open(storage_name, "rb") as source:
                blob = source.read()
        except Exception as exc:
            item["estado"] = "FALTANTE"
            item["error"] = exc.__class__.__name__
            missing += 1
            continue

        digest = hashlib.sha256(blob).hexdigest()
        archive.writestr(item["archive_path"], blob)
        item["estado"] = "INCLUIDO"
        item["sha256"] = digest
        item["tamano_bytes"] = len(blob)
        found += 1
    return found, missing


def _verify_archive(content, inventory):
    """
    Reopens the generated ZIP and verifies every included binary against its
    manifest hash. A missing storage object makes the archive incomplete.
    """
    try:
        with zipfile.ZipFile(io.BytesIO(content), "r") as archive:
            names = set(archive.namelist())
            required = {"README.txt", "manifest.json", "data.json", "file_inventory.json"}
            if not required.issubset(names):
                return False
            for item in inventory:
                if item["estado"] != "INCLUIDO":
                    return False
                path = item["archive_path"]
                if path not in names:
                    return False
                if hashlib.sha256(archive.read(path)).hexdigest() != item["sha256"]:
                    return False
    except (zipfile.BadZipFile, KeyError, OSError):
        return False
    return True


def generar_expediente_estructurado(evento, *, user):
    """
    D6.2 keeps the existing endpoint name for compatibility, but now produces
    the full V2 archive: structured data + every discoverable FileField binary.
    """
    if not usuario_puede_evento(user, evento, Actions.EVENT_EDIT):
        raise PermissionDenied("No tienes permiso para exportar el expediente de este evento.")
    if evento.estado not in EXPORTABLE_STATES:
        raise ValidationError(
            "El expediente histórico se genera para eventos finalizados, cancelados o archivados."
        )

    objects = _objects_for_event(evento)
    payload = _core_payload(objects)
    inventory = _binary_inventory(objects)

    buffer = io.BytesIO()
    generated_at = timezone.now()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        found, missing = _write_binary_files(archive, inventory)
        manifest = {
            "formato": ARCHIVE_FORMAT,
            "generado_en": generated_at.isoformat(),
            "evento_id": evento.id,
            "evento_nombre": evento.titulo_evento,
            "empresa_id": evento.empresa_id,
            "estado_evento": evento.estado,
            "conteos": {
                key: len(value) if isinstance(value, list) else 1
                for key, value in payload.items()
            },
            "binarios_referenciados": len(inventory),
            "binarios_encontrados": found,
            "binarios_faltantes": missing,
            "incluye_binarios": True,
            "integridad_verificada": False,
            "completo_para_purga_historica": False,
        }
        archive.writestr(
            "README.txt",
            (
                "DIRTEC Event Studio - Expediente completo D6.2\n\n"
                "Incluye datos estructurados y los binarios FileField que forman "
                "parte del grafo canónico del evento.\n"
                "La integridad se valida después de construir el ZIP.\n"
                "D6.2 NO habilita por sí solo la purga histórica; D6.3 definirá "
                "retención y autorización.\n"
            ),
        )
        archive.writestr(
            "data.json",
            json.dumps(payload, indent=2, ensure_ascii=False),
        )
        archive.writestr(
            "file_inventory.json",
            json.dumps(inventory, indent=2, ensure_ascii=False),
        )
        archive.writestr(
            "manifest.json",
            json.dumps(manifest, indent=2, ensure_ascii=False),
        )

    content = buffer.getvalue()
    integrity_ok = missing == 0 and _verify_archive(content, inventory)
    digest = hashlib.sha256(content).hexdigest()

    # Receipt is the server-side audit proof. The ZIP bytes themselves are not
    # retained by DIRTEC.
    manifest["integridad_verificada"] = integrity_ok
    manifest["completo_para_purga_historica"] = integrity_ok

    receipt = ExpedienteHistoricoEvento.objects.create(
        empresa=evento.empresa,
        evento=evento,
        evento_id_snapshot=evento.id,
        evento_nombre_snapshot=evento.titulo_evento[:200],
        formato=ARCHIVE_FORMAT,
        sha256=digest,
        tamano_bytes=len(content),
        manifest=manifest,
        incluye_binarios=True,
        integridad_verificada=integrity_ok,
        binarios_encontrados=found,
        binarios_faltantes=missing,
        completo_para_purga_historica=integrity_ok,
        generado_por=user,
    )
    return content, receipt


def _collector_for_event(evento):
    collector = Collector(using=evento._state.db or "default")
    try:
        collector.collect([evento])
    except (ProtectedError, RestrictedError) as exc:
        protected = sorted(
            {
                f"{obj._meta.label}:{obj.pk}"
                for obj in getattr(exc, "protected_objects", [])
            }
        )
        raise ValidationError(
            [
                "El grafo destructivo contiene objetos protegidos por PROTECT/RESTRICT.",
                *protected[:25],
            ]
        )
    return collector


def _collector_objects(collector):
    grouped = {}
    seen = set()

    for model, objects in collector.data.items():
        label = model._meta.label_lower
        bucket = grouped.setdefault(label, [])
        for obj in objects:
            key = (label, obj.pk)
            if key in seen:
                continue
            seen.add(key)
            bucket.append(obj)

    for qs in collector.fast_deletes:
        label = qs.model._meta.label_lower
        bucket = grouped.setdefault(label, [])
        for obj in qs:
            key = (label, obj.pk)
            if key in seen:
                continue
            seen.add(key)
            bucket.append(obj)

    for label in grouped:
        grouped[label].sort(key=lambda obj: (str(obj.pk),))
    return grouped


def _destructive_payload(grouped):
    return {
        label: [_serialize_instance(obj) for obj in objects]
        for label, objects in sorted(grouped.items())
    }


def _destructive_binary_inventory(grouped):
    inventory = []
    seen_storage = set()
    for label, objects in sorted(grouped.items()):
        section = label.replace(".", "_")
        for obj in objects:
            for field in obj._meta.concrete_fields:
                if not isinstance(field, FileField):
                    continue
                value = getattr(obj, field.name, None)
                storage_name = getattr(value, "name", "") if value else ""
                if not storage_name or storage_name in seen_storage:
                    continue
                seen_storage.add(storage_name)
                inventory.append(
                    {
                        "modelo": label,
                        "registro_id": obj.pk,
                        "campo": field.name,
                        "storage_name": storage_name,
                        "archive_path": _safe_archive_name(
                            section, obj, field, storage_name
                        ),
                        "estado": "PENDIENTE",
                        "sha256": None,
                        "tamano_bytes": None,
                    }
                )
    inventory.sort(key=lambda item: item["storage_name"])
    return inventory


def _hash_existing_binary_inventory(inventory):
    found = 0
    missing = 0
    for item in inventory:
        try:
            with default_storage.open(item["storage_name"], "rb") as source:
                blob = source.read()
        except Exception as exc:
            item["estado"] = "FALTANTE"
            item["error"] = exc.__class__.__name__
            missing += 1
            continue
        item["estado"] = "INCLUIDO"
        item["sha256"] = hashlib.sha256(blob).hexdigest()
        item["tamano_bytes"] = len(blob)
        found += 1
    return found, missing


def _destructive_graph_fingerprint(payload, inventory):
    canonical = {
        "objetos": payload,
        "binarios": [
            {
                "storage_name": item["storage_name"],
                "sha256": item["sha256"],
                "tamano_bytes": item["tamano_bytes"],
                "estado": item["estado"],
            }
            for item in inventory
        ],
    }
    raw = json.dumps(
        canonical,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _current_destructive_graph(evento):
    collector = _collector_for_event(evento)
    grouped = _collector_objects(collector)
    payload = _destructive_payload(grouped)
    inventory = _destructive_binary_inventory(grouped)
    found, missing = _hash_existing_binary_inventory(inventory)
    fingerprint = _destructive_graph_fingerprint(payload, inventory)
    counts = {
        label: len(objects)
        for label, objects in grouped.items()
    }
    return {
        "collector": collector,
        "grouped": grouped,
        "payload": payload,
        "inventory": inventory,
        "found": found,
        "missing": missing,
        "fingerprint": fingerprint,
        "counts": counts,
    }


def generar_expediente_purge_ready(evento, *, user):
    if not usuario_puede_evento(user, evento, Actions.EVENT_EDIT):
        raise PermissionDenied(
            "No tienes permiso para generar el expediente de purga."
        )
    if evento.estado != "ARCHIVADO":
        raise ValidationError(
            "El evento debe estar archivado para generar un expediente purge-ready."
        )

    graph = _current_destructive_graph(evento)
    if graph["missing"]:
        raise ValidationError(
            f"Hay {graph['missing']} archivo(s) fisico(s) faltante(s). "
            "No se puede generar un expediente purge-ready integro."
        )

    buffer = io.BytesIO()
    with zipfile.ZipFile(
        buffer, "w", compression=zipfile.ZIP_DEFLATED
    ) as archive:
        for item in graph["inventory"]:
            with default_storage.open(item["storage_name"], "rb") as source:
                archive.writestr(item["archive_path"], source.read())

        manifest = {
            "formato": PURGE_ARCHIVE_FORMAT,
            "generado_en": timezone.now().isoformat(),
            "evento_id": evento.id,
            "evento_nombre": evento.titulo_evento,
            "empresa_id": evento.empresa_id,
            "estado_evento": evento.estado,
            "destructive_graph_sha256": graph["fingerprint"],
            "model_counts": graph["counts"],
            "binarios_encontrados": graph["found"],
            "binarios_faltantes": graph["missing"],
            "incluye_binarios": True,
            "integridad_verificada": True,
            "completo_para_purga_historica": True,
        }
        archive.writestr(
            "README.txt",
            (
                "DIRTEC Event Studio - Expediente purge-ready D6.4\n\n"
                "Este ZIP representa el mismo grafo de objetos que Django "
                "eliminaria para el evento al momento de generarlo.\n"
                "Si el grafo cambia antes de la purga, la ejecucion se bloquea.\n"
            ),
        )
        archive.writestr(
            "destructive_graph.json",
            json.dumps(
                graph["payload"],
                indent=2,
                ensure_ascii=False,
            ),
        )
        archive.writestr(
            "file_inventory.json",
            json.dumps(
                graph["inventory"],
                indent=2,
                ensure_ascii=False,
            ),
        )
        archive.writestr(
            "manifest.json",
            json.dumps(
                manifest,
                indent=2,
                ensure_ascii=False,
            ),
        )

    content = buffer.getvalue()
    digest = hashlib.sha256(content).hexdigest()

    receipt = ExpedienteHistoricoEvento.objects.create(
        empresa=evento.empresa,
        evento=evento,
        evento_id_snapshot=evento.id,
        evento_nombre_snapshot=evento.titulo_evento[:200],
        formato=PURGE_ARCHIVE_FORMAT,
        sha256=digest,
        tamano_bytes=len(content),
        manifest={
            **manifest,
            "file_inventory": graph["inventory"],
        },
        incluye_binarios=True,
        integridad_verificada=True,
        binarios_encontrados=graph["found"],
        binarios_faltantes=0,
        completo_para_purga_historica=True,
        generado_por=user,
    )
    return content, receipt


def _validar_ejecucion_purga_historica(
    evento,
    *,
    expediente,
    user,
    confirmacion,
    sha256,
):
    if not usuario_es_dirtec_operativo(user):
        raise PermissionDenied(
            "Solo DIRTEC puede ejecutar una purga historica."
        )
    if evento.estado != "ARCHIVADO":
        raise ValidationError(
            "El evento debe permanecer archivado."
        )
    if expediente.evento_id_snapshot != evento.id:
        raise ValidationError(
            "El expediente no pertenece al evento."
        )
    if expediente.formato != PURGE_ARCHIVE_FORMAT:
        raise ValidationError(
            "La purga requiere un expediente purge-ready D6.4."
        )
    if not (
        expediente.integridad_verificada
        and expediente.completo_para_purga_historica
        and expediente.binarios_faltantes == 0
        and expediente.respaldo_externo_confirmado_en
        and expediente.purga_historica_autorizada_en
    ):
        raise ValidationError(
            "El expediente no ha completado integridad, custodia y autorizacion."
        )
    if not expediente.retencion_hasta or expediente.retencion_hasta > timezone.now():
        raise ValidationError(
            "El periodo de retencion no ha finalizado."
        )
    if expediente.purga_ejecutada_en:
        raise ValidationError(
            "Esta purga historica ya fue ejecutada."
        )

    expected = f"PURGAR HISTORICO {evento.id}"
    if (confirmacion or "").strip().upper() != expected:
        raise ValidationError(
            f'Escribe exactamente "{expected}" para confirmar.'
        )
    if (sha256 or "").strip().lower() != expediente.sha256.lower():
        raise ValidationError(
            "El SHA-256 confirmado no coincide con el expediente purge-ready."
        )

    graph = _current_destructive_graph(evento)
    expected_graph = expediente.manifest.get(
        "destructive_graph_sha256"
    )
    if not expected_graph or graph["fingerprint"] != expected_graph:
        raise ValidationError(
            "El evento cambio despues del respaldo purge-ready. "
            "Genera un nuevo expediente y repite el flujo de custodia/retencion."
        )
    if graph["missing"]:
        raise ValidationError(
            "Hay binarios faltantes en el servidor; la purga fue bloqueada."
        )
    return graph


def ejecutar_purga_historica(
    evento,
    *,
    expediente,
    user,
    confirmacion,
    sha256,
):
    graph = _validar_ejecucion_purga_historica(
        evento,
        expediente=expediente,
        user=user,
        confirmacion=confirmacion,
        sha256=sha256,
    )

    file_names = [
        item["storage_name"]
        for item in graph["inventory"]
    ]
    counts = graph["counts"]
    evento_id = evento.id
    evento_nombre = evento.titulo_evento
    empresa_id = evento.empresa_id

    # The receipt survives because evento uses SET_NULL.
    with transaction.atomic():
        collector = _collector_for_event(evento)
        collector.delete()

    deleted_files = []
    failed_files = []
    for storage_name in file_names:
        try:
            if default_storage.exists(storage_name):
                default_storage.delete(storage_name)
            deleted_files.append(storage_name)
        except Exception as exc:
            failed_files.append(
                {
                    "storage_name": storage_name,
                    "error": exc.__class__.__name__,
                }
            )

    expediente.refresh_from_db()
    expediente.purga_ejecutada_en = timezone.now()
    expediente.purga_ejecutada_por = user
    expediente.resultado_purga = {
        "evento_id": evento_id,
        "evento_nombre": evento_nombre,
        "empresa_id": empresa_id,
        "model_counts": counts,
        "binarios_previstos": len(file_names),
        "binarios_eliminados": len(deleted_files),
        "binarios_fallidos": failed_files,
        "destructive_graph_sha256": graph["fingerprint"],
    }
    expediente.save(
        update_fields=[
            "purga_ejecutada_en",
            "purga_ejecutada_por",
            "resultado_purga",
        ]
    )
    return expediente
