# VERSIONING

## Estrategia de versionado

Este proyecto usara checkpoints por fase para separar claramente lo estable de las nuevas arquitecturas.

## Version actual congelada

### `v5.2-live-preview`

Estado: version estable del editor visual actual antes del Universal Editing Engine.

Incluye:

- invitaciones completas,
- editor visual,
- capas libres,
- enfoque responsive,
- Motor de Componentes `ComponenteInvitacion`,
- API CRUD de componentes,
- render publico de componentes,
- refactor con `_section_base.html`,
- Live Preview Editor sobre invitacion real,
- documentacion `ARCHITECTURE.md` y `CHANGELOG.md`.

Esta version debe servir como punto de regreso si la Fase 5.3 requiere cambios grandes.

## Proxima version

### `v5.3-universal-editing-engine`

Estado: pendiente.

Objetivo:

Crear una arquitectura universal donde cualquier elemento visible pueda registrarse, seleccionarse, transformarse, bloquearse, ocultarse, duplicarse, editarse y persistirse desde el editor.

## Reglas

- No mezclar cambios pequenos con fases arquitectonicas grandes.
- Cada fase grande debe tener commit y tag propios.
- La documentacion debe actualizarse antes de cerrar cada version.
- No eliminar compatibilidad sin documentar migracion.
- No usar `git push --force`.
