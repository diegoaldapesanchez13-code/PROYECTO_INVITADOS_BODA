# K.8.1 — Collaboration & Commercial Workflow

## Core architecture

A new `colaboracion` domain sits above `ServicioEvento`.

`ServicioEvento` remains the internal operational/financial service record.

`ExpedienteServicio` becomes the collaboration source of truth:
- client request;
- planner analysis;
- provider assignment;
- channel histories;
- provider quote versions;
- client proposal versions;
- client approval;
- planner contract confirmation.

## Communication topology

CLIENTE <-> PLANNER
PLANNER <-> PROVEEDOR

There is intentionally no direct Client <-> Provider channel.

## Commercial privacy

Provider sees:
- its own cost quotation;
- planner responses;
- its own service.

Client sees:
- final commercial proposal only;
- never provider cost;
- never margin.

Planner sees:
- both communication channels;
- provider quotation;
- private cost;
- margin;
- client price.

## Budget behavior

When Client approves:
- ADICIONAL -> creates active client budget line at `precio_cliente`.
- INCLUIDO_PAQUETE -> creates zero-price line marked included.

Internal provider costs remain in `ServicioEvento.costo_total`.

## Versioning

Provider quotations and client proposals never overwrite previous versions.

## Next subphase

K.8.2 will add Client Guest & Table Self-Service:
- client creates/manages invited people;
- planner owns table layout;
- client assigns people only to existing tables;
- capacity/layout constraints remain server-enforced.
