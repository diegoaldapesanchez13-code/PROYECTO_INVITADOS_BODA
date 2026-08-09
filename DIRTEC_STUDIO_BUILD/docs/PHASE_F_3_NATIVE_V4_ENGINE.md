# PHASE F.3 — Native V4 Engine

## Resultado

El motor interno deja de usar la proyección temporal V4 → V3.

Runtime principal:

```text
schemaVersion 4
canvases[]
CANVAS
canvasId
CANVAS coordinate space
mobile -> tablet -> desktop
```

## Convertido

- `core/schema.js`
- `core/state.js`
- Canvas Manager
- Transform policy
- Components factory
- Asset nodes
- Layer Tree
- Navigation Engine
- Interaction Runtime
- Interaction Canvas executor
- Inspector
- Renderer
- DocumentStorage
- demo/editor bootstrap runtime

## Compatibilidad

Las referencias `sections`, `sectionId` y `SECTION` solo se permiten dentro de
módulos cuya función explícita es leer/migrar datos históricos V3:

```text
core/schema_v4.js
core/migrate.js
```

No participan como contrato del runtime principal.

## Eliminación

`interaction/executors/section.js` se retira. El executor oficial es
`interaction/executors/canvas.js`.

## Regression

Antes de empaquetar:

```text
60 tests
60 pass
0 fail
```

## Aplicación

```powershell
python .\scripts\apply_phase_f3_cleanup.py
python .\scripts\verify_phase_f3.py
```
