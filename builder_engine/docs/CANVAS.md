# Canvas Module

## Responsabilidad
Gestionar la colección `document.canvases` como estructura independiente del modo de renderizado.

## API principal

```js
const module = registerCanvasModule(app);
await app.start();

module.service.create({ name: "Ceremonia" });
module.service.duplicate(canvasId);
module.service.move(canvasId, 0);
module.service.update(canvasId, { height: 1200 });
module.service.remove(canvasId);
module.service.select(canvasId);
```

## Regla de arquitectura
Canvas no conoce elementos HTML ni rutas del backend. Las futuras interfaces visuales consumirán `CanvasService` mediante adaptadores.
