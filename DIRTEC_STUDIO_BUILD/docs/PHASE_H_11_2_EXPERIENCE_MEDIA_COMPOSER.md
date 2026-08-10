# PHASE H.11.2 — Experience Media Composer

Adds a focused mobile composition tool for IMAGE, GIF and VIDEO intros.

The Experience document gains two backward-compatible fields:

```js
intro.mediaPosition = { x: 50, y: 50 }
intro.mediaScale = 1
```

Controls:
- Cover / Contain
- mobile device preview: iPhone 13/14, iPhone SE, Android
- nine focal-point presets
- X/Y focal sliders
- scale 0.5x–2x
- background color

The same contract is consumed by Preview/Public through IntroController.

This is not a Canvas editor and does not touch Layers, Inspector, Transform,
History, RSVP or the UniversalRenderer.
