# PHASE R.8 — Product Acceptance & Freeze

## Canonical authorities

- Builder source: `DIRTEC_STUDIO_BUILD/builder/`
- RSVP: `Invitado.asistira`
- Buffet: `Invitado.menu_asignado` effective value
- Table: `AsignacionMesa.invitado`
- Countdown: Django runtime event context
- Experience: `document.experience`

## Live controls

Inspector text, textarea, range and color use `input` events.

Experience typing/audio volume commits suppress their own panel rebuild.

Media X/Y/scale keeps local preview on input and persistent commit on change.

## Removed runtime duplication

- RSVP Inspector/factory no longer exposes pass limits or comments.
- legacy `_section_rsvp.html` retired.
- Inspector AssetLibrary is a compatibility re-export of the canonical Assets implementation.
- Guest Dashboard no longer edits textual mesa fields.
- Admin Group/Guest UI follows Guest Domain V2.
