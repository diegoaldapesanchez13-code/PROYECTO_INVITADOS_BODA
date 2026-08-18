# K9 Restructure Plan

## Baseline
Commercial architecture is stable through K9.8B.
K9.8C is preserved in archive branch and is not the foundation of the new product shell.
Development branch: `feature/k9-product-restructure`.

## Preserve
Tenant/security, catalog, provider-service bridge, proposal, contract v2, materialization v2, finance, lifecycle K9.8A, endpoints K9.8B, guests/RSVP, tables, workspace, audit and desktop Builder.

## Reorganize
Login/password reset, dashboards, navigation, Event Workspace, forms, visible lifecycle, return context, responsive, branding, package CRUD, provider assignment, RSVP/capacity and contract modifications.

## R0 — Preserve & Reset
Archive K9.8C, branch from K9.8B, create product documents.

## R1 — Foundation UX
R1A: design tokens/components/forms/responsive/app shell/brand context.
R1B: modern login and password reset.
R1C: topbar/sidebar/mobile nav/navigation by role.

## R2 — Generic Event + Base CRUD
Minimal event creation, optional legacy-specific fields, general dates/name, event lifecycle, safe delete/purge, audit and return context.
Do not rename `EventoBoda` yet.
States: BORRADOR, ACTIVO, FINALIZADO, CANCELADO, ARCHIVADO.

## R3 — Company / Planner Dashboards
Company business overview and Planner work overview. Both open the same Event Workspace.

## R4 — Event Workspace
Canonical shell and modules: Resumen, Datos, Comercial, Servicios, Tareas, Agenda, Invitados, Documentos, Finanzas, Invitación, Actividad, Configuración. Quick Create and context preservation.

## R5 — Lifecycle + Delete/Purge
Integrate K9.8A/B, rescue useful K9.8C pieces, add deletion evaluation, error-delete, purge, historical filters and Danger Zone.
GATE #1 after R5.

## R6 — Catalog + Packages
Simple service creation, simple package creation, pricing mode POR_DEFINIR/FIJO/POR_PERSONA/MIXTO, PaqueteServicio CRUD and reorder.

## R7 — Proposal + Versioned Contract
Price breakdown, sticky total, additions/courtesies/warnings.
Keep ContratoEvento as single authority.
Support ORIGINAL/MODIFICACION/REEMPLAZO semantics and version lineage.

## R8 — Operational Services + Provider
Provider/company/undefined, recommended provider search, costs/dates/responsible/notes, audited provider changes.

## R9 — Tasks + Agenda + Documents
Task list/Kanban, agenda timeline/calendar/list, modal/bottom-sheet editing, secure document access.
Close legacy direct private-media URL debt.

## R10 — Finance UX
Reuse K9.7. Show contractual sale, received, balance, estimated/committed/real cost, margin and cash flow.
GATE #2 after R10.

## R11 — Guests / RSVP / Capacity
Extend registration/capacity/lock state. Keep RSVP values internally if useful. Make `guest_analytics.py` the metric authority used everywhere.

## R12 — Tables + Invitation + Builder Mobile
Integrate Mesas under Guests, invitation overview, RSVP config and specialized Builder mobile UX.

## R13 — Branding
Central branding service and DIRTEC Brand Studio. Logo, hero, login image and validated colors. No arbitrary CSS.

## R14 — Client / Provider Portals
Rebuild role-specific projections over existing services.
GATE #3 after R14.

## R15 — Clean DB + Event Zero
Backup, clean local DB, migrate, controlled demo seed.
Acceptance flow: service -> provider -> package -> event -> proposal -> contract -> modification -> materialize -> assign/change provider -> tasks/agenda -> guests/RSVP/capacity -> tables -> finance -> invitation/Builder -> finish -> archive.

## Testing
Small tests per phase.
Gate #1: R1-R5.
Gate #2: R6-R10.
Gate #3: R11-R14.
R15: Event Zero.
Preproduction: full regression.

Critical regressions:
- tenant isolation;
- permissions;
- login/logout;
- frozen contract;
- idempotent materialization;
- finance;
- private media;
- public RSVP;
- desktop Builder.

## Responsive acceptance
Every new screen: 375, 390, 430, 768, 1024, 1440 px.

## Git
Work on `feature/k9-product-restructure`.
Tags at gates only:
- K9.R5-GATE1
- K9.R10-GATE2
- K9.R14-GATE3
- K9.EVENT-ZERO

## Production
Do not deploy microphases just because local tests pass.
First deployment candidate only after Gate #1 and explicit validation.
Production starts from clean PostgreSQL + migrations + real data; no local demo database.
