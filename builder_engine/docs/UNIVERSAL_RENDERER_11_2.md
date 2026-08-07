# Sprint 11.2 — Universal Renderer

## Objetivo

Renderizar un único Document Schema en:

- EDIT
- PREVIEW
- PUBLIC

sin depender de:

- `editor_invitacion.html`
- `ver_invitacion.html`
- `sections[]`
- Builder V3
- montaje Django

## Módulos

- `universal_renderer.js`
- `universal_style_resolver.js`
- `universal_interaction_resolver.js`
- `universal_dom_adapter.js`
- `universal_fixture.js`

## Reglas

### Misma salida visual

Los tres modos generan la misma geometría y jerarquía.

Solo cambia:

- si las interacciones están activas;
- metadatos de edición;
- atributos internos de modo.

### Mobile first

- mobile: 390 px
- tablet: 768 px
- desktop: 1180 px

La altura procede de CanvasSizeContract.

### Capas

Los hermanos se ordenan de atrás hacia delante. El stack visual se normaliza dentro del padre.

### Imágenes interactivas

IMAGE conserva su etiqueta `img`, pero puede adquirir:

- `role=button`
- `tabindex=0`
- `aria-label`
- acciones CLICK

### Renderer aislado

Este sprint no cambia rutas Django ni templates oficiales.

## Próximo paso

Crear un sandbox Django del Universal Renderer para inspección visual, todavía sin cambiar las rutas oficiales.
