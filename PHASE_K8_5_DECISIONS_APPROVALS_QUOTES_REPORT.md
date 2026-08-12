# K.8.5 — Decisions / Approvals / Quotes / Client Proposals

## Objetivo
Convertir resultados del workspace en informacion estructurada directamente sobre `ServicioEvento`, sin depender de `ExpedienteServicio`.

## Nuevos modelos
- `DecisionServicio`
- `CotizacionServicio` (versionada)
- `PropuestaServicioCliente` (versionada)
- `AprobacionServicio`

## Reglas
- Proveedor y Planner pueden registrar cotizaciones; solo Planner/operacion decide su aceptacion.
- Aceptar una cotizacion actualiza `ServicioEvento.costo_proveedor`.
- Solo Planner/operacion crea propuestas para cliente.
- Solo cliente del evento responde propuestas/aprobaciones.
- Aprobar una propuesta actualiza `modalidad` y `cargo_adicional_cliente`; no mezcla el costo privado del proveedor con el cargo al cliente.
- Costos/cotizaciones del proveedor no se renderizan al cliente.
- Propuestas/aprobaciones del cliente no se renderizan al proveedor.
- Modelos legacy permanecen por compatibilidad y no son la fuente de verdad nueva.

## No incluido
Agenda, tareas, documentos financieros y pagos se conectan en K.8.6. Limpieza legacy queda para fase posterior.
