# PHASE R.7 — Product Dashboard UX

## Audit findings

The previous dashboard had three concurrent navigation systems:

1. sidebar anchors;
2. sticky dashboard tabs;
3. workflow strip inside Design.

It also had a structural bug: `_operacion_gestion.html` was included outside a
`data-tab-panel`, so the largest operational workspace could remain visible
while another top-level tab was selected.

Operational summaries were duplicated in Production, Indicators and Operation.

The guest Excel export still used the old group/pass RSVP model even though
R.3-R.5 made `Invitado` the source of truth.

## Product architecture

One primary navigation:

- Resumen
- Invitación
- Contenido
- Invitados
- Operación
- Equipo

Secondary tools:

- Mesas
- Calendario
- Portal cliente
- Portal proveedor

## Summary

The new Resumen consolidates:

- invited people;
- confirmed/pending RSVP;
- buffet;
- confirmed people without table;
- pending payment;
- high-priority operational warnings;
- charts.

## Invitation

Builder is presented as the final visual-design tool.

Legacy event/invitation fields remain available under a collapsed compatibility
panel, avoiding two visual editors competing at the same hierarchy level.

## Operation

Operation is now a real top-level tab panel. Its 11 existing modules remain
functionally intact and their saved forms/actions are not rewritten.

The duplicated operation-summary cards were removed because their metrics now
live in Resumen.

## Excel correction

Guest export now writes one row per `Invitado` for PERSONAL and FAMILIAR alike.

It exports:

- group/invitation;
- person;
- adult/child classification;
- effective buffet;
- individual RSVP;
- actual `AsignacionMesa`;
- extra-companion flag;
- invitation UUID.

Legacy pass counts and group RSVP comments are no longer exported as authority.

## Protected domains

No model/migration changes in R.7.

R.7 does not change:

- RSVP API;
- Guest Analytics;
- individual table model;
- Countdown;
- Builder document schema;
- Experience;
- persistence/revision;
- assets.
