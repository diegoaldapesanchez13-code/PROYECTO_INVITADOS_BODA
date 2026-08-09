# PHASE F.3.1 — Browser Import Fix

## Síntoma

El editor mostraba `Conectado`, pero el Builder no terminaba de iniciar.

## Causa

`inspector/index.js` ya había migrado a:

```js
import { canvasPanel } from "./panels/canvas.js";
```

pero el archivo físico seguía llamándose:

```text
inspector/panels/section.js
```

El navegador fallaba durante la resolución de módulos antes de inicializar el Builder.

## Corrección

```text
inspector/panels/section.js
            ↓
inspector/panels/canvas.js
```

También se corrigió un import relativo huérfano en `inspector/library.js`.

## Nuevo gate

`verify_phase_f3_1.py` recorre todos los imports relativos estáticos y dinámicos
del Builder y falla si algún archivo apuntado no existe.
