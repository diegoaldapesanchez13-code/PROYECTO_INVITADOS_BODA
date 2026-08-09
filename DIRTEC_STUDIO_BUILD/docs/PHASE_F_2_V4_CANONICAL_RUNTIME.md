# PHASE F.2 — V4 Canonical Runtime Cutover

Schema V4 becomes the official persisted/public contract.

```text
schemaVersion 4
canvases[]
CANVAS
canvasId
mobile -> tablet -> desktop
```

## Safe compatibility boundary

The Django Builder persists V4, but the already-proven editing internals still
receive a temporary V3 projection through `core/runtime_v4.js`.

Standalone V3 remains unchanged.

```text
Standalone:
V3 -> V3

Django:
existing V3/V4
  -> canonical V4
  -> temporary runtime projection
  -> editor internals
  -> save
  -> canonical V4
```

UniversalRenderer accepts V4 directly and projects internally without changing
geometry.

F.3 will remove this projection and make BuilderState/Canvas/Layers native V4.

No database migration is required.
