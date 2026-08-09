# PHASE D — Public Renderer Cut

La ruta pública `invitacion/<uuid>/` usa el snapshot `documento_builder_publicado` y el mismo `UniversalRenderer` del Builder.

## Reglas
- Invitado anónimo: solo snapshot publicado.
- `?preview=1`: borrador únicamente para usuario con acceso al evento.
- Sin snapshot V3: fallback temporal al renderer legacy.
- Assets: resueltos por `assetId` desde Django.
- Interacciones: runtime público del UniversalRenderer.
- RSVP: API JSON pública protegida por CSRF.
- Rollback: `invitacion-legacy/<uuid>/`.

## Próximo corte
Tras validar visualmente PHASE D, PHASE E elimina dependencias visuales legacy y migra cualquier comportamiento restante antes de borrar archivos antiguos.
