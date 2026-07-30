# CHANGELOG

## 2026-07-29 - v5.2-live-preview

Checkpoint estable antes del Universal Editing Engine.

### Agregado

- Se creo el modelo `ComponenteInvitacion`.
- Se agrego la migracion `invitaciones/migrations/0028_componenteinvitacion.py`.
- Se registro `ComponenteInvitacion` en el admin de Django.
- Se agrego API JSON para listar, crear, actualizar y eliminar componentes.
- Se agrego render publico de componentes con `_componentes_invitacion.html`.
- Se refactorizaron secciones hacia partials reutilizables usando `_section_base.html`.
- Se agrego Live Preview Editor sobre la invitacion publica real mediante iframe same-origin.
- Se agregaron modos de interaccion `Editar` y `Probar`.
- Se permitio seleccionar y mover componentes `ComponenteInvitacion` sobre la invitacion real.
- Se agrego sincronizacion visual y persistencia de posicion al soltar componentes.
- Se conservaron las capas libres, assets, fondos, imagenes completas y editor rapido existente.
- Se documentaron arquitectura y versionado.

### Conservado

- Invitaciones personales y familiares.
- Confirmacion individual de invitados familiares.
- Acompanantes nominales para invitaciones personales.
- Control adulto/nino definido por empresa o planner.
- Importacion CSV/XLSX de invitados.
- Mesas, QR, regalos, mapas, menus, albumes, dress code y RSVP.
- Editor visual anterior con capas libres y enfoque responsive.

### Validacion

- `node --check invitaciones/static/invitaciones/js/editor_invitacion.js`
- `py manage.py check`
- `py manage.py makemigrations --check --dry-run`

## Siguiente version prevista - v5.3-universal-editing-engine

La siguiente version no debe agregar funcionalidades pequenas. Debe implementar la base arquitectonica del Universal Editing Engine:

- registro universal de elementos editables,
- seleccion sobre cualquier elemento visible,
- transformaciones generales,
- panel de propiedades universal,
- biblioteca de componentes drag and drop,
- historial undo/redo,
- responsive engine por dispositivo.
