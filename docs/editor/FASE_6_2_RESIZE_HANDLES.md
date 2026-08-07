# FASE 6.2 - Resize Handles del Diseno Rapido

## Objetivo

Permitir redimensionar visualmente las tarjetas del Diseno Rapido sin tocar la Vista Real ni el contenido publico de la invitacion.

Esta fase continua el `layout state` persistente de la Fase 6.1. Los handles no crean un sistema nuevo de medidas: actualizan los mismos campos ya guardados en `section.config`.

## Campos afectados

- `layoutWidth`
- `sectionHeight`
- `layoutAutoHeight`
- `layoutCollapsed`
- `layoutExpanded`
- `layoutAspectRatio`

## Comportamiento

Cuando una tarjeta esta seleccionada en la Vista Rapida aparecen tres controles:

- lado derecho: cambia el ancho de la tarjeta,
- lado inferior: cambia el alto,
- esquina inferior derecha: cambia ancho y alto al mismo tiempo.

Al mover un handle, el editor:

- actualiza la tarjeta en pantalla,
- sincroniza los controles del inspector,
- marca el borrador como modificado,
- conserva los valores para el siguiente guardado.

## Alcance

Incluido:

- redimensionamiento visual de tarjetas seleccionadas,
- persistencia mediante los campos existentes,
- soporte para componentes del builder dentro de la Vista Rapida.

No incluido:

- resize de componentes individuales,
- rotacion visual,
- snap/grid,
- cambios en Vista Real,
- cambios en RSVP, invitados, QR, mesas, APIs o URLs.

## Archivos principales

- `invitaciones/static/invitaciones/js/editor_invitacion.js`
- `invitaciones/static/invitaciones/css/editor_invitacion.css`
- `docs/editor/FASE_6_2_RESIZE_HANDLES.md`

## Validacion

- `node --check invitaciones\static\invitaciones\js\editor_invitacion.js`
- `py manage.py check`
