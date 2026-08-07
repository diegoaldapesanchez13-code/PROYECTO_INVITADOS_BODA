# FASE 6.4 - Componentes Editables Basicos

## Objetivo

Hacer que los primeros componentes del constructor visual sean controlables desde el editor:

- Texto,
- Imagen,
- Boton.

Antes de esta fase, los componentes podian crearse y moverse parcialmente, pero no existia un panel claro para editar contenido, eliminar elementos accidentales o confirmar que el componente seleccionado era el activo.

## Cambios

### Panel de componente seleccionado

Se agrega un panel dentro de las propiedades de diseno con:

- posicion X/Y,
- ancho,
- alto,
- rotacion,
- opacidad,
- z-index,
- bloquear,
- ocultar,
- eliminar componente.

### Propiedades por tipo

Texto:

- texto,
- tamano,
- color,
- fuente.

Imagen:

- URL,
- texto alternativo,
- ajuste `contain/cover`.

Boton:

- texto,
- URL,
- estilo principal/secundario.

### Drag mas estable

El movimiento de componentes en la Vista Rapida ahora calcula delta con `getBoundingClientRect()`, respetando mejor tarjetas escaladas.

Al soltar un componente, se guarda contra la API de componentes y se sincroniza con la Vista Real editable.

## No incluido

- Resize visual de componentes individuales.
- Rotacion con handles.
- Snap/grid.
- Biblioteca avanzada de componentes.
- Edicion rica de tipografias.

## Validacion

- `node --check invitaciones\static\invitaciones\js\editor_invitacion.js`
- `py manage.py check`
