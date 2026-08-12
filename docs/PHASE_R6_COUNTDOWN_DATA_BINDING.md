# PHASE R.6 — Countdown Data Binding

## Contract

Countdown stores the binding source in the Builder document:

- `RECEPTION`
- `CEREMONY`
- `EVENT`
- `CUSTOM`

New Countdown components default to `RECEPTION`.

Django dates are runtime context and are not copied into the Builder document.

## Runtime event context

```json
{
  "eventId": 1,
  "eventDate": "...",
  "ceremonyDate": "...",
  "receptionDate": "..."
}
```

`eventDate` is the earliest available ceremony/reception date and represents the
general start of the event.

## Backwards compatibility

Old Countdown with `targetDate` and no `targetSource` remains manual/custom.

Old Countdown with neither value falls forward to `RECEPTION`.

## Surfaces

The same event context is supplied to:

- editable Builder canvas;
- mobile Preview;
- Public invitation.

No schema or database migration is required.
