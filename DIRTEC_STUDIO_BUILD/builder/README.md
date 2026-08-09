# DIRTEC Builder

Fuente oficial del editor visual de DIRTEC Event Studio.

## Baseline

Esta carpeta nació como copia funcionalmente idéntica de:

`invitaciones/static/invitaciones/js/builder_v3/`

Tag de referencia:

`builder-v3-stable-baseline`

## Regla

A partir del cutover de Phase A:

- el desarrollo nuevo ocurre en `/builder`;
- `builder_v3` permanece temporalmente congelado como referencia;
- el navegador recibe el build desde `invitaciones/static/invitaciones/builder/`;
- no se edita manualmente la carpeta compilada.

## Tests

```powershell
node --test builder/tests/*.mjs
```

## Build

```powershell
python .\scripts\build_builder.py
```
