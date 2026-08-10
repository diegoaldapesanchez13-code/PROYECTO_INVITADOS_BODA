# PHASE H.11.1 — Asset Library Workspace

## Scope

UX-only hardening of the Assets workspace. It does not modify Canvas, Layers,
Inspector, Experience contract, persistence or Django models.

## Changes

- Assets tab no longer competes with the resource grid for vertical scrolling.
- Header, search, views, categories and count remain visible.
- The resource grid owns the vertical scroll.
- Cards keep a readable preview size and visible footer/actions.
- Adds a `Ver` action with a large detail dialog.
- Delete remains available both on the card and detail view.
- Audio assets use a proper audio visual placeholder instead of a broken image.
- Detail view can preview image/GIF, video and audio.
- Upload picker includes the audio formats already supported by Phase H.

## Protected behavior

- Clicking the card preview still uses/inserts the asset.
- Drag-and-drop insertion is unchanged.
- Favorite behavior is unchanged.
- Remote deletion still goes through the existing upload adapter/backend.
- Referenced assets remain protected by the existing Django backend rule.

## Browser acceptance

1. Assets header and filters remain visible.
2. Resource grid scrolls independently.
3. Cards are readable and actions stay visible.
4. `Ver` opens a large preview.
5. User asset can be deleted.
6. Referenced asset reports the existing backend protection instead of disappearing.
7. Audio shows a music placeholder and detail player.
8. Image/video/GIF insertion still works.
