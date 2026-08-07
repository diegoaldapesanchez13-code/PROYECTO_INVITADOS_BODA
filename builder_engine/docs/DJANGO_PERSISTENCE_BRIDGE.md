# Sprint 10.1 — Django Persistence Bridge

## Objetivo

Conectar el `Persistence Engine` con Django sin reemplazar todavía la interfaz activa.

## Endpoints

- `GET /dashboard/editor-invitacion/<evento_id>/engine/document/`
- `POST /dashboard/editor-invitacion/<evento_id>/engine/document/save/`
- `POST /dashboard/editor-invitacion/<evento_id>/engine/document/publish/`

## Persistencia

- Borrador: `DisenoInvitacion.configuracion_borrador`
- Publicación: `DisenoInvitacion.configuracion_publicada`
- Historial publicado: `VersionDisenoInvitacion`

## Compatibilidad

Los documentos antiguos no se destruyen. Al cargarlos se colocan temporalmente en:

```json
{
  "globals": {
    "legacyEditorConfig": {},
    "legacyMigrationPending": true
  }
}
```

La migración visual de `sections[]` hacia `canvases[]` se realizará en una entrega posterior.

## Seguridad

- Requiere autenticación.
- Filtra el evento mediante `eventos_visibles_usuario`.
- Verifica `metadata.eventId`.
- Rechaza Base64 y `blob:`.
- Limita el documento a 5 MB.
- Usa transacciones al guardar y publicar.
