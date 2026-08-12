# PHASE J.1 — Countdown Presentation + Data Binding Foundation

## Countdown

The composite Countdown keeps its CARD → TEXT/TEXT structure so deleting a
visual container never destroys Number/Label bindings.

Visual presentation is independent:

- `CARDS`: current visual cards.
- `PLAIN`: cards are structural only; background/border/shadow are hidden.
- `showLabels=true`: number + label.
- `showLabels=false`: number only.

No countdown binding or real-time timer is replaced.

## Text Data Bindings V1

Text nodes can now use:

- MANUAL
- EVENT
- INVITATION_GROUP

EVENT fields:
- event name
- groom
- bride
- couple names
- ceremony/reception places
- ceremony/reception date and time text

INVITATION_GROUP fields:
- group name
- group type
- total people
- confirmed people
- pending people

Manual `content.text` remains the fallback.

Countdown value/label text retains its protected `COUNTDOWN` binding and does
not expose the generic dynamic-data selector.

## Architecture

The same UniversalRenderer resolves the binding in Editor/Preview/Public.

No second renderer and no database migration are introduced.
