# PHASE R.1 — Guest Domain V2

## Contract

- `Grupoinvitacion` remains the UUID/access/grouping record.
- Every real or authorized seat is represented by `Invitado`.
- PERSONAL has one nominal `Invitado` plus zero or more organizer-authorized extra placeholders.
- FAMILIAR has named `Invitado` rows plus optional extra placeholders.
- Adult/child is organizer data (`tipo_persona`).
- Buffet menu is organizer data (`menu_asignado`) and defaults from adult/child.
- RSVP guest food suggestions/allergies/restrictions are not part of the V2 contract.

## Deferred

- R.2 dashboard redesign.
- R.3 individual public RSVP.
- R.4 buffet dashboard.
- R.5 table assignments become Invitado-only.
- R.6 real Countdown event binding.

Legacy fields are intentionally not dropped in R.1 to avoid destructive migration before R.2/R.3 are complete.
