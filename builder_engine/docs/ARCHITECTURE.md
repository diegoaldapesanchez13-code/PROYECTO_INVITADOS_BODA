# Arquitectura del Builder Engine

## Capas actuales

1. `frontend/app`: Kernel, configuración y registro de módulos.
2. `frontend/document`: contrato, validación y serialización del documento.
3. `frontend/sdk`: API mínima para registrar extensiones.

Los módulos visuales permanecen temporalmente en `builder_v3` y `static/.../builder` hasta migrarse por sprints completos.

## Canvas Module

El módulo `frontend/canvas` administra el contrato estructural de los lienzos.
Opera sobre `document.canvases` mediante `BuilderApp.updateDocument()` y no depende del DOM, del renderer ni de Django. La representación visual se conectará posteriormente mediante adaptadores de UI.

La compatibilidad temporal con Builder R3 se mantiene mediante `adapters/r3_canvas_adapter.js`, que traduce `sections` a `canvases` sin alterar el editor activo.
