# PHASE R.4 — Guest Analytics V2

## Source of truth

All event RSVP statistics now come directly from `Invitado`.

`Grupoinvitacion` remains grouping/link metadata and legacy aggregate
compatibility only.

## Canonical metrics

- invited people
- attending
- not attending
- pending
- attendance percentage
- adult/child person classification
- confirmed adult/child classification
- confirmed adult-menu count
- confirmed child-menu count
- confirmed people without a table

## Buffet rule

Buffet uses `menu_asignado` effective value, not only `tipo_persona`.

Examples:
- Child + `SEGUN_TIPO` => child menu.
- Child + `ADULTO` => adult menu.
- Adult + `INFANTIL` => child menu.

Only confirmed attendees are included in buffet totals.

## Tables

R.4 does not migrate the tables domain. It fixes the dashboard metric with a
temporary compatibility bridge:
- direct Invitado assignment = seated;
- old PERSONAL group assignment temporarily covers only its nominal person;
- extra companions still require their own seat.

R.5 will remove group-based table assignment entirely.
