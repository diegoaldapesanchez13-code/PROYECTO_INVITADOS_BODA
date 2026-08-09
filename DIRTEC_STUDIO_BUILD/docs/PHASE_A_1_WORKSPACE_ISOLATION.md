# PHASE A.1 — Workspace Isolation

## Estructura oficial

```text
DIRTEC_EVENT_STUDIO/
├── DIRTEC_STUDIO_BUILD/
│   ├── builder/        # fuente oficial en reconstrucción
│   ├── scripts/
│   └── docs/
├── invitaciones/
│   └── static/invitaciones/builder/  # salida generada
└── manage.py
```

## Auditoría del ZIP nuevo

La copia aislada conserva íntegros los 119 archivos funcionales del baseline.
No hay archivos faltantes ni modificados.

Los únicos extras son metadata intencional del workspace:

- `README.md`
- `builder.manifest.json`
- `package.json`

## Alcance

Esta fase NO modifica rutas Django, modelos, templates, Schema v3 ni UX.
Tampoco elimina `builder_v3`; continúa temporalmente como referencia de paridad.

## Gate

Desde la raíz:

```powershell
python .\DIRTEC_STUDIO_BUILD\scripts\verify_phase_a1.py
```

O individualmente:

```powershell
python .\DIRTEC_STUDIO_BUILD\scripts\verify_builder_source_parity.py
node --test DIRTEC_STUDIO_BUILD/builder/tests/*.mjs
python .\DIRTEC_STUDIO_BUILD\scripts\build_builder.py
python .\DIRTEC_STUDIO_BUILD\scripts\verify_builder_build.py
python manage.py check
```
