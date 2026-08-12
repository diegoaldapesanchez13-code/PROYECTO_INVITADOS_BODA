# K.7 — Provider Portal V2

## Product contract

Provider is an external operational collaborator.

Provider can see only:
- events where its provider profile has an assigned service;
- its own services and commercial terms;
- itinerary activities assigned to that provider;
- documents linked to that provider.

Provider cannot see:
- guest lists or RSVP;
- Builder;
- clients;
- other providers;
- company administration;
- Django Admin;
- private service notes.

## Important workflow hardening

`ServicioEvento.estado` remains the internal contractual/financial state,
managed by company/planner.

K.7 adds a separate provider response:
- PENDIENTE
- CONFIRMADO
- INCIDENCIA
- COMPLETADO

Provider updates only `estado_proveedor`, `comentario_proveedor` and
`fecha_respuesta_proveedor`.

This prevents a provider from marking its own service as paid, liquidated,
approved or cancelled.

## Documents

Provider uploads are always `visible_cliente=False`.

Company/planner remains responsible for deciding whether a provider document
should later be shared with the client.

## Migration

`proveedores.0006_servicioevento_estado_proveedor_y_comentario`
