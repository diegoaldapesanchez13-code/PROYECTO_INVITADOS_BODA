# PHASE B — Django Integration

## Objetivo

Convertir `DIRTEC_STUDIO_BUILD/builder` en el editor oficial de Django sin
reescribir el Builder V3.

## Arquitectura

```text
/dashboard/editor-invitacion/<id>/
        ↓
Django Builder View
        ↓ bootstrap JSON
DIRTEC Studio Builder
        ↓
DjangoDocumentStorageBridge
        ↓
/api/document/
        ↓
DisenoInvitacion.documento_builder_borrador
```

## Persistencia

Se agregan campos independientes:

```text
documento_builder_borrador
documento_builder_publicado
builder_revision
```

No se reutilizan los JSON legacy. Esto evita mezclar Schema V3 con
`configuracion_borrador.sections`.

## Autosave

La UI V3 conserva `BuilderDocumentStorage`, pero en Django recibe un objeto
Storage compatible inyectado en:

```js
globalThis.__DIRTEC_BUILDER_DOCUMENT_STORAGE__
```

Por tanto:

- V3 no se llena de `fetch()` Django;
- localStorage deja de ser source of truth oficial;
- el mismo Builder sigue funcionando standalone;
- Django se conecta mediante adapter.

## Concurrencia

Cada guardado incluye `baseRevision`.

Si otra sesión guardó antes:

```text
HTTP 409
```

El bridge actualiza la revisión y reintenta una vez.

## Publicación

PHASE B ya permite crear el snapshot:

```text
documento_builder_publicado
```

pero `/invitacion/<uuid>/` todavía utiliza el renderer legacy.

El cutover público será PHASE D.

## Legacy

El editor antiguo sigue temporalmente accesible en:

```text
/dashboard/editor-invitacion/<id>/legacy/
```

La ruta normal ya abre DIRTEC Builder.

## No cambia

- Schema V3;
- Canvas;
- handles;
- Layers;
- Inspector;
- Components;
- Renderer;
- Assets backend (PHASE C);
- ruta pública (PHASE D).
