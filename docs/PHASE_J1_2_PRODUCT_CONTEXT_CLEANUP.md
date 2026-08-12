# PHASE J.1.2 — Product Context Cleanup

## Binding decision

Generic Text exposes only:
- MANUAL
- EVENT

Invitation/group bindings remain runtime-compatible for existing documents but
are no longer exposed as a new authoring choice.

Reason: RSVP is the canonical invitation/person UI. Person-level reusable
content will be introduced later through a scoped/repeater model rather than
ambiguous generic text.

## RSVP badges

Builder preview receives the real roster of the first event invitation:
- full name
- Adult/Child
- effective menu
- RSVP state

Public API uses the same serializer and GET requests use `cache: no-store`.

## Dashboard authority

Builder is the only visual invitation editor.

Dashboard Invitation contains only structured event data that can feed runtime
bindings:
- event name
- primary/secondary participant
- ceremony/reception date
- ceremony/reception place/address/map link
- textual dress code

Removed from modern Dashboard UI:
- cover/ceremony/reception images
- palette/font
- envelope/seal/audio
- section backgrounds
- legacy section visibility/title copy
- dress-code reference images
- legacy visual preview

The model fields remain for migration/backward compatibility.

## Content

Dashboard no longer uploads invitation Album media. Visual media belongs to
Builder Assets.

Structured content remains:
- ceremony people / parents / sponsors
- gifts
- itinerary
- company catalogs
