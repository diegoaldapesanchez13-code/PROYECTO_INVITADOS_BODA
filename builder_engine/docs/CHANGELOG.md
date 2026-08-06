# Changelog

## 0.7.0

- Crea el Kernel de DIRTEC Builder Engine.
- Introduce `BuilderRegistry`.
- Introduce Document Engine schema v1.
- Introduce API mínima de Builder SDK.

## 0.8.0 — Canvas Module

- Se extrajo el contrato de lienzos al Builder Engine.
- Se agregó CanvasService con CRUD, selección y reordenamiento.
- Se agregó CanvasModule registrable en el Kernel.
- Se agregó adaptador de compatibilidad con documentos Builder R3.
- El módulo permanece desacoplado de DOM, Django y Renderer.
## 0.8.0 — Inspector Module
- Extrae InspectorRegistry, InspectorService e InspectorModule.
- Agrega edición por rutas anidadas y soporte de nodos compuestos.
- Conserva acordeones y scroll por nodo.
- Agrega adaptador de contratos del Inspector R3.

