# K.5 — Planner Workspace

## Product role

Wedding Planner is an internal operator of one tenant.

The workspace shows only:
- assigned events;
- planner-owned pending tasks;
- event providers;
- event operational tools.

It does not expose:
- company users;
- company plans;
- company switching;
- client portal shortcuts;
- DIRTEC or Django Admin functions.

## Navigation

- Inicio
- Mis eventos
- Pendientes
- Proveedores

Create Event is a secondary action inside Mis eventos, not a permanent
navigation module.

## Event workflow

Each assigned event exposes:
- complete event workspace;
- Builder;
- Guests / RSVP / buffet;
- Tables;
- Calendar;
- Export summary.

## Tenant

Company context is displayed as locked information. The backend continues to
derive it from the authenticated planner membership.

## No migration

K.5 changes workspace composition and planner summary context only.
