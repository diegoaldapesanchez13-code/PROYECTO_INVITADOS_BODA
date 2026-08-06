# RFC-001 — Crear DIRTEC Builder Engine

- Estado: Aprobado
- Prioridad: Crítica
- Alcance de este sprint: extraer el Kernel, el Document Engine y la API mínima del SDK.
- Fuera de alcance: mover Canvas, Renderer, Inspector, Assets o conectar Django.

## Regla principal

El Kernel coordina contratos y servicios inyectados. No conoce Django ni lógica de eventos.
