# Sprint 6.1.1 — Reorganización del Builder Engine

## Objetivo

Crear la arquitectura oficial `builder/` sin activar todavía el reemplazo del editor Django actual.

## Resultado

- `builder_v3/` permanece como respaldo estable.
- `builder/` contiene una copia compatible del motor R3.
- Se incorpora `BuilderApp` como punto único de entrada.
- Se incorpora el Document Engine.
- Se incorpora la capa `integrations/django`.
- Se incorpora la base del Theme Engine.
- El demo se conserva en `examples/` y deja de ser el contrato de arranque futuro.

## Fuera de alcance

- No se modifica `editor_invitacion.html`.
- No se modifica `views.py`.
- No se reemplaza `ver_invitacion.html`.
- No se elimina `builder_v3/`.
- No se activa todavía guardado Django desde la interfaz.
