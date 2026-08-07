# Asset Manager 10.8.1

Reutiliza `AssetInvitacion`; no crea modelos ni migraciones.

## Backend

`GET /dashboard/editor-invitacion/<evento_id>/engine/assets/`

Devuelve assets normalizados para el Engine con:

- id y backendId;
- tipo IMAGE, GIF o VIDEO;
- categoría;
- URL MEDIA;
- MIME;
- tamaño;
- metadatos.

## UI

- biblioteca visual;
- búsqueda;
- filtros;
- selección;
- asignación a IMAGE o VIDEO;
- actualización del Documento sin Base64.

La subida se incorpora en 10.8.2.
