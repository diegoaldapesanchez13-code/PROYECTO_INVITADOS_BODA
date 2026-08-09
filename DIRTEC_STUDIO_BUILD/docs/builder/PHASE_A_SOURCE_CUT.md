# PHASE A — Source Cut

## Objetivo

Establecer `/builder` como código fuente oficial sin cambiar el comportamiento del Builder V3 estable.

## No cambia

- rutas Django;
- templates Django;
- editor activo;
- `ver_invitacion`;
- modelos;
- base de datos;
- persistencia;
- Schema v3;
- UX;
- renderer;
- assets.

## Cambios

1. `builder_v3` se copia a `/builder`.
2. Se excluyen únicamente 13 duplicados `.txt`.
3. Se agrega `package.json` para declarar ESM explícitamente.
4. Se agrega manifest de fuente.
5. Se agrega build reproducible.
6. Se agrega verificación SHA-256 de paridad.
7. Se agrega verificación SHA-256 del build.

## Comandos

```powershell
python .\scripts\verify_builder_source_parity.py
node --test builder/tests/*.mjs
python .\scripts\build_builder.py
python .\scripts\verify_builder_build.py
python manage.py check
git status
```

## Gate

Phase A se acepta solamente con:

- PARIDAD OK;
- 45/45 tests Builder;
- BUILD OK;
- Django check 0 issues;
- Builder V3 original todavía intacto.

No se elimina `builder_v3` en esta fase.
