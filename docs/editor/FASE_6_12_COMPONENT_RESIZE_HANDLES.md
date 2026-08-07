# FASE 6.12 - Component Resize Handles

## Objetivo

Permitir modificar el tamano de componentes visuales directamente desde el canvas, sin depender solo de sliders del inspector.

Esto acerca el editor al comportamiento esperado de un constructor tipo Canva/Figma.

## Componentes soportados

- `TEXTO`
- `IMAGEN`
- `BOTON`

## Vista Rapida

Cuando un componente esta seleccionado y no esta bloqueado, se muestran handles en las cuatro esquinas:

- `nw`
- `ne`
- `sw`
- `se`

Al arrastrar un handle se actualizan:

- `x`
- `y`
- `width`
- `height`

El inspector se actualiza mientras se redimensiona.

Al soltar el handle, el componente se guarda mediante la API del Motor de Componentes.

## Vista Real

En modo `Editar`, la vista real dentro del iframe tambien muestra handles en el componente seleccionado.

Al arrastrarlos:

- se actualiza el componente en el iframe,
- se sincroniza el estado del editor,
- se guarda el componente al soltar.

El modo `Probar` no se modifica, para que botones, links, formularios y mapas sigan funcionando como usuario final.

## Archivos principales

- `invitaciones/static/invitaciones/js/editor_invitacion.js`
- `invitaciones/static/invitaciones/css/editor_invitacion.css`
- `invitaciones/templates/invitaciones/editor_invitacion.html`

## Compatibilidad

Este cambio mantiene:

- drag anterior de componentes,
- inspector de componentes,
- Component Tree,
- acciones del arbol,
- API existente de componentes,
- render publico.

## Pendiente

- Rotacion visual con handle dedicado.
- Snap a guias y centros.
- Constraints responsive.
- Resize tactil optimizado para mobile.
- Agrupacion y resize de grupos.
