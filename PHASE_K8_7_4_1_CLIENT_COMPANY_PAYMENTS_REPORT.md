# K.8.7.4.1 — Pagos Cliente → Empresa / Planner

## Flujo correcto
Cliente reporta pago del evento → Empresa/Planner revisa → Recibido u Observado.

El proveedor queda completamente fuera de este flujo.

## Modelo
`PagoClienteEvento`
- evento
- servicio_evento opcional solo como concepto
- registrado_por
- concepto
- monto / fecha / método / referencia
- comprobante obligatorio
- estado: PENDIENTE / RECIBIDO / OBSERVADO / CANCELADO
- comentario_cliente
- comentario_equipo
- revisado_por / fecha_revision

## Separación financiera
`PagoClienteEvento` = ingreso/evidencia comercial del cliente.
`PagoEvento` = egreso/pago operativo asociado a GastoEvento.
No se mezclan.

## UI
Cliente: Portal Cliente V3 → Pagos.
Equipo: Event Dashboard V3 → Finanzas → Pagos reportados por cliente.
Proveedor: sin acceso ni participación.

## Corrección responsive
Se mantiene la corrección del gate exacto:
`@media (max-width: 680px)` y `@media (max-width: 480px)`.

## Migración
`presupuesto.0004_pago_cliente_evento_k8741`
