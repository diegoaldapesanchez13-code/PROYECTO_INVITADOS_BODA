# History Engine

Versión: 1

El módulo `history` centraliza undo, redo, transacciones, agrupación por `mergeKey` y navegación por la línea de tiempo.

## Contrato

- El módulo escucha cambios del `BuilderApp`.
- Los cambios dentro de una transacción se consolidan en una sola entrada.
- Las ediciones consecutivas con el mismo `mergeKey` pueden combinarse.
- `undo`, `redo` y `goTo` restauran el Documento mediante `BuilderApp.replaceDocument`.
- El historial no depende del DOM, Django ni del Renderer.

## Estrategia actual

La primera versión estable utiliza snapshots normalizados y un límite configurable. La optimización por parches/diffs queda reservada para una versión posterior, cuando el formato del Documento esté completamente congelado.
