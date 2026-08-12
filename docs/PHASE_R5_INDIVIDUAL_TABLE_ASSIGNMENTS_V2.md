# PHASE R.5 — Individual Table Assignments V2

## Final contract

`AsignacionMesa` always points to one `Invitado`.

There is no active `grupo_invitacion` table assignment.

PERSONAL, FAMILIAR and authorized extra companions use the exact same seating
model.

## Data migration

`mesas.0002_individual_guest_assignments` converts old group assignments to the
nominal person of that group.

If a nominal person already has an explicit individual assignment, that
individual assignment wins and the duplicate legacy group record is removed.
Seat number/notes are copied when the explicit record is missing them.

Invalid orphan assignments are removed because no person can be derived.

## Database protection

`invitado` becomes non-null and receives a unique database constraint so one
person cannot be assigned to multiple tables.

## R.4 cleanup

`confirmados_sin_mesa` now checks only individual assignments. The temporary
PERSONAL group bridge is removed.
