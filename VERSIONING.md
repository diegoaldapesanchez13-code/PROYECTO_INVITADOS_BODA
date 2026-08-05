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

## Rama actual de consolidacion

### `v5.3-editor-consolidation`

Estado: en progreso.

Objetivo inmediato:

Estabilizar el renderer/editor antes de avanzar hacia el Visual Studio completo.

Reglas:

- Cambios pequenos por fase.
- No modificar Vista Real salvo sincronizacion necesaria.
- No romper RSVP, invitados, QR, mesas, APIs ni URLs.
- Documentar cada fase en `docs/editor/`.
- Mantener compatibilidad con `v5.2-live-preview`.

Fase registrada:

- `S01-P02`: Layout State persistente para tarjetas del Diseno Rapido.
- `S01-P03`: Resize Handles para tarjetas del Diseno Rapido.
- `S01-P04`: Paridad entre Borrador, Vista Rapida y Vista Real.
- `S01-P05`: Componentes editables basicos.
- `S01-P06`: Contenido real editable para secciones hibridas, iniciado en Detalles.
- `S01-P07`: Contenido real por tarjeta para Detalles y conexion visual de Regalos, Album y Album compartido.
