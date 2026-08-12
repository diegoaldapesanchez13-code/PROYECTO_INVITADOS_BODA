# PHASE J.1.1 — Invitation Bindings + RSVP Adaptive UI

## Binding fix

The editable Builder now receives `invitationPreview` from Django. The first
real invitation/group of the current event is used as preview context. Public
continues to use the UUID-specific real invitation context.

Generic text bindings remain deliberately limited to Event and Invitation.
Individual-person text binding is not introduced until a repeater/person scope
exists, preventing ambiguous "which guest?" behavior for families.

## RSVP adaptive roster

The public RSVP remains individual and does not allow the guest to modify menu
or Adult/Child classification.

Each person can visually show:
- Adult / Child badge;
- assigned Adult / Child menu badge;
- RSVP status.

Density modes:
- AUTO (default): compact at 4+ people;
- COMPACT;
- COMFORTABLE.

The people list owns internal vertical scrolling, so 1 person remains spacious
while 10 people remain usable without overflowing the fixed Builder component.
