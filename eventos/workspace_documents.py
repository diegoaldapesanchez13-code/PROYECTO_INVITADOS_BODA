from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from core.services.auditoria import registrar_auditoria
from documentos.models import DocumentoEvento


def _snapshot(documento):
    return {
        "tipo_documento": documento.tipo_documento,
        "titulo": documento.titulo,
        "servicio_evento_id": documento.servicio_evento_id,
        "proveedor_id": documento.proveedor_id,
        "visible_cliente": documento.visible_cliente,
        "visible_proveedor": documento.visible_proveedor,
        "archivado_en": (
            documento.archivado_en.isoformat()
            if documento.archivado_en
            else None
        ),
    }


@transaction.atomic
def crear_documento(
    *,
    evento,
    cleaned_data,
    user=None,
    request=None,
):
    documento = DocumentoEvento(
        evento=evento,
        cargado_por=user if getattr(user, "is_authenticated", False) else None,
    )
    for field, value in cleaned_data.items():
        setattr(documento, field, value)

    documento.full_clean()
    documento.save()

    registrar_auditoria(
        usuario=user,
        empresa=evento.empresa,
        evento=evento,
        accion="CARGAR_DOCUMENTO_EVENTO_K9",
        modelo="DocumentoEvento",
        objeto_id=documento.id,
        descripcion=f"Se cargó documento: {documento.titulo}.",
        valores_nuevos=_snapshot(documento),
        request=request,
    )
    return documento


@transaction.atomic
def archivar_documento(
    documento,
    *,
    motivo="",
    user=None,
    request=None,
):
    documento = DocumentoEvento.objects.select_for_update().select_related(
        "evento",
        "evento__empresa",
    ).get(pk=documento.pk)

    if documento.archivado_en:
        return documento

    before = _snapshot(documento)
    documento.archivado_en = timezone.now()
    documento.archivado_por = (
        user if getattr(user, "is_authenticated", False) else None
    )
    documento.motivo_archivo = (motivo or "").strip() or None
    documento.save(
        update_fields=[
            "archivado_en",
            "archivado_por",
            "motivo_archivo",
        ]
    )

    registrar_auditoria(
        usuario=user,
        empresa=documento.evento.empresa,
        evento=documento.evento,
        accion="ARCHIVAR_DOCUMENTO_EVENTO_K9",
        modelo="DocumentoEvento",
        objeto_id=documento.id,
        descripcion=f"Se archivó documento: {documento.titulo}.",
        valores_anteriores=before,
        valores_nuevos=_snapshot(documento),
        request=request,
    )
    return documento


@transaction.atomic
def restaurar_documento(
    documento,
    *,
    user=None,
    request=None,
):
    documento = DocumentoEvento.objects.select_for_update().select_related(
        "evento",
        "evento__empresa",
    ).get(pk=documento.pk)

    if not documento.archivado_en:
        return documento

    before = _snapshot(documento)
    documento.archivado_en = None
    documento.archivado_por = None
    documento.motivo_archivo = None
    documento.save(
        update_fields=[
            "archivado_en",
            "archivado_por",
            "motivo_archivo",
        ]
    )

    registrar_auditoria(
        usuario=user,
        empresa=documento.evento.empresa,
        evento=documento.evento,
        accion="RESTAURAR_DOCUMENTO_EVENTO_K9",
        modelo="DocumentoEvento",
        objeto_id=documento.id,
        descripcion=f"Se restauró documento: {documento.titulo}.",
        valores_anteriores=before,
        valores_nuevos=_snapshot(documento),
        request=request,
    )
    return documento



@transaction.atomic
def reemplazar_archivo_documento(
    documento,
    *,
    nuevo_archivo,
    user=None,
    request=None,
):
    documento = DocumentoEvento.objects.select_for_update().select_related(
        "evento",
        "evento__empresa",
    ).get(pk=documento.pk)

    old_name = documento.archivo.name
    old_storage = documento.archivo.storage
    before = _snapshot(documento)
    before["archivo"] = old_name

    documento.archivo = nuevo_archivo
    documento.full_clean()
    documento.save(update_fields=["archivo"])

    new_name = documento.archivo.name

    registrar_auditoria(
        usuario=user,
        empresa=documento.evento.empresa,
        evento=documento.evento,
        accion="REEMPLAZAR_ARCHIVO_DOCUMENTO_EVENTO_K9",
        modelo="DocumentoEvento",
        objeto_id=documento.id,
        descripcion=f"Se reemplazó el archivo de: {documento.titulo}.",
        valores_anteriores=before,
        valores_nuevos={
            **_snapshot(documento),
            "archivo": new_name,
        },
        request=request,
    )

    if old_name and old_name != new_name:
        transaction.on_commit(
            lambda: old_storage.delete(old_name)
        )

    return documento


@transaction.atomic
def eliminar_documento(
    documento,
    *,
    user=None,
    request=None,
):
    documento = DocumentoEvento.objects.select_for_update().select_related(
        "evento",
        "evento__empresa",
    ).get(pk=documento.pk)

    evento = documento.evento
    document_id = documento.id
    titulo = documento.titulo
    file_name = documento.archivo.name
    storage = documento.archivo.storage
    before = {
        **_snapshot(documento),
        "archivo": file_name,
    }

    registrar_auditoria(
        usuario=user,
        empresa=evento.empresa,
        evento=evento,
        accion="ELIMINAR_DOCUMENTO_EVENTO_K9",
        modelo="DocumentoEvento",
        objeto_id=document_id,
        descripcion=f"Se eliminó permanentemente documento: {titulo}.",
        valores_anteriores=before,
        request=request,
    )

    documento.delete()

    if file_name:
        transaction.on_commit(
            lambda: storage.delete(file_name)
        )

    return document_id
