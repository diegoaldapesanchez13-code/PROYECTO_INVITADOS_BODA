# PHASE A.1.1 — Windows portability

## Incidencia

`test_r3_mobile_preview.mjs` calculaba su directorio con:

```js
new URL(import.meta.url).pathname
```

En Windows eso devuelve una ruta URL con prefijo `/C:/...`. Al pasarla por `path.resolve`, Node terminaba intentando leer:

```text
C:\C:\Users\...
```

## Corrección

Se usa la API oficial de Node:

```js
import { fileURLToPath } from "node:url";
const here = path.dirname(fileURLToPath(import.meta.url));
```

Es portable entre Windows y POSIX.

## Paridad

Esta modificación afecta exclusivamente un test. No modifica código de producto.

El verificador de paridad ahora reporta por separado:

- 74 archivos de producto exactos;
- tests baseline sin cambios;
- deltas de test explícitamente permitidos;
- metadata propia del workspace.

No se permite ninguna diferencia silenciosa.
