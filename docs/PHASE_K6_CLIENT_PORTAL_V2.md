# K.6 — Client Portal V2

## Role goal

Client is an external event stakeholder, not an operator of the company.

The portal is intentionally simpler than Company and Planner workspaces.

## Client-visible data

- assigned event identity and dates;
- RSVP summary;
- invitation publication status;
- client approvals;
- documents explicitly marked `visible_cliente`;
- tasks/appointments where the client is the responsible user;
- ceremony/reception milestones.

## Information intentionally hidden

- provider internal costs;
- company margin;
- private provider notes;
- tasks assigned to planners or internal staff;
- company users/catalog administration;
- Builder authoring controls;
- Django Admin.

## Navigation

- Resumen
- Agenda
- Aprobaciones
- Documentos

## Event switching

Only appears when the same client account is assigned to more than one event.
There is never a company/tenant selector.

## No migration

K.6 is a portal projection/UX phase only.
