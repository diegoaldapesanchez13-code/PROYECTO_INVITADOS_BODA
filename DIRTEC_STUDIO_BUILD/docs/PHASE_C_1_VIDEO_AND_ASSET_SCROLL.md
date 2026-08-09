# PHASE C.1 — Video persistente + scroll de Assets

## Problema 1: video persistente

Django devuelve assets con URL relativa al origen:

```text
/media/editor_invitaciones/assets/video.mp4
```

El normalizador de video aceptaba:

- blob:
- data:video/
- http://
- https://

pero rechazaba `/media/...` porque `new URL("/media/...")` no tiene base.

### Corrección

Las rutas root-relative seguras `/...` ahora son válidas.

Además VIDEO con:

```text
sourceType = library
assetId = db-123
```

ya no depende de una copia vieja de `content.source`.

El Renderer resuelve primero:

```text
assetId
→ AssetManager
→ URL actual
→ normalizeVideoSource
→ <video src>
```

Es el mismo principio usado por IMAGE.

## Problema 2: Assets parecía contraído

`data-r3-library` es también el panel izquierdo. La librería aplicaba
`overflow-y: visible`, anulando el comportamiento de altura del workspace.

### Corrección

La biblioteca ahora usa:

```text
header/búsqueda
filtros
categorías
resumen
RECURSOS ← minmax(0, 1fr) + scroll propio
```

Solo la cuadrícula de recursos tiene scroll vertical.

## Alcance

No cambia Django ni modelos.
No hay migraciones.
No cambia persistencia del Documento.
No cambia Layer Stack ni Transform.
