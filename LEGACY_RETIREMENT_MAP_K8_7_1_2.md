# Mapa de retiro legacy — K.8.7.1.2

## Retirado YA del flujo oficial del Event Dashboard
- Panel `Compatibilidad temporal`.
- `Contenido heredado`.
- `Operación heredada`.
- CRUD directo de `CateringEvento` desde Event Dashboard.
- CRUD directo de `ElementoDecoracion` desde Event Dashboard.
- CRUD directo de `EntretenimientoEvento` desde Event Dashboard.
- CRUD directo de `CancionEvento` desde Event Dashboard.
- `DetalleProduccionEvento` como fuente del dashboard.
- Semántica `Tarea con horas = cita`.

## Fuente de verdad desde ahora
- Servicio: `ServicioEvento`.
- Cliente ↔ Planner / Planner ↔ Proveedor / Interno: Workspace del servicio.
- Trabajo pendiente: `TareaEvento`.
- Tiempo/coordinación: `ActividadItinerario.tipo = CITA | ACTIVIDAD | HITO`.
- Confirmaciones: `ParticipanteActividad`.
- Documentos: `DocumentoEvento` vinculado opcionalmente a ServicioEvento.
- Gasto/Pago: `GastoEvento -> PagoEvento`, vinculado opcionalmente a ServicioEvento.

## Tablas legacy que todavía NO se borran físicamente en esta fase
`CateringEvento`, `ElementoDecoracion`, `EntretenimientoEvento` y `ExpedienteServicio` siguen en el esquema porque dashboards/portales antiguos todavía contienen referencias de código. **No son fuente de verdad y el Event Dashboard ya no escribe en ellas.**

Se eliminarán físicamente cuando el Dashboard Planner, Empresa, Cliente y Proveedor hayan sido migrados a V3 y un grep/test de regresión confirme cero dependencias activas. Esto evita una eliminación prematura que rompa otro rol, pero no mantiene dos flujos funcionales paralelos.
