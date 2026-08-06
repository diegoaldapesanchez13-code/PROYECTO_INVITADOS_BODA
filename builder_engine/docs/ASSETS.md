# Assets Module

El módulo `frontend/assets` administra imágenes, videos, audio y otros recursos mediante referencias persistentes.

## Contrato mínimo

```json
{
  "id": "42",
  "type": "VIDEO",
  "source": "UPLOAD",
  "name": "video.mp4",
  "url": "/media/editor_invitaciones/assets/video.mp4",
  "mimeType": "video/mp4",
  "backendId": 42,
  "size": 10485760
}
```

Los archivos no se serializan dentro del Documento. `data:` y `blob:` están prohibidos para persistencia.
