# PHASE C — Persistent Asset Library

## Objetivo

Persistir imágenes y videos del Builder mediante Django.

## Flujo

```text
Asset Library V3
    ↓
AssetUploadService
    ↓
DjangoAssetAdapter
    ↓
POST multipart
    ↓
AssetInvitacion
    ↓
MEDIA_ROOT
    ↓
URL persistente
    ↓
node.content.assetId + src
```

## Fuente de verdad

Los archivos físicos y su existencia pertenecen a Django:

```text
AssetInvitacion + MEDIA_ROOT
```

El Documento solo guarda referencias.

No se guardan Base64 ni blob URLs en el documento oficial.

## Límites actuales del proyecto

Se respetan los validadores ya existentes:

- imágenes: 8 MB;
- videos: 80 MB;
- extensiones visuales permitidas por `validar_media_visual`.

## Eliminación segura

Django impide eliminar un AssetInvitacion si `assetId` aparece en:

- `documento_builder_borrador`;
- `documento_builder_publicado`.

Primero debe retirarse del diseño.

## Standalone

V3 conserva el modo standalone:

- si no existe Django uploader, usa su flujo DataURL/blob original;
- bajo Django, el bootstrap inyecta el adapter persistente.

Esto evita duplicar el Asset Manager.

## Sin migración

PHASE C reutiliza `AssetInvitacion`; no agrega tablas ni campos.

`seccion` queda `NULL` para los assets nuevos del Builder. La dependencia conceptual
de `SeccionInvitacion` se retirará en Database Cleanup.
