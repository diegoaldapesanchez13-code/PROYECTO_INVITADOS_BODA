# K.8.7.2 — Planner Dashboard V3

## Objetivo
Sustituir el dashboard Planner legacy por una bandeja de trabajo Event-Centric.

## Decisiones
- El Planner Dashboard deja de editar/asignar `ServicioEvento` y proveedores.
- Se retiran de `dashboard_planner` los POST legacy `asignar_proveedor_evento` y `actualizar_servicio_evento`.
- Se eliminan las funciones muertas `asignar_proveedor_planner_dashboard` y `actualizar_servicio_planner_dashboard`.
- `ExpedienteServicio` deja de ser la fuente del dashboard Planner.
- El Planner ve acciones separadas por **Cliente / Proveedor / Interno**.
- Las acciones del servicio se derivan del mismo estado estructurado que usa el Event Dashboard V3.
- Agenda separa Citas de Actividades/Hitos y muestra confirmaciones pendientes.
- La operación detallada vive en `Event Dashboard V3` y `Service Workspace`.

## Navegación V3
- Hoy
- Trabajo
- Mis eventos
- Agenda

## Escrituras permitidas desde Planner Dashboard
- Crear evento.
- Cambiar estado del evento.

Todo lo demás se realiza en el contexto correcto del evento o servicio.

## Migraciones
No requiere migraciones.
