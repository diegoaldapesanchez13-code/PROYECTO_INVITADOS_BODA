# Sprint 11.1 — Contratos base

Este sprint no modifica todavía la interfaz.

## Módulos nuevos

- `layout/`
  - TransformContract
  - TransformPolicyRegistry
  - CoordinateSpaceResolver
- `layers/`
  - LayerStackService
- `viewport/`
  - CanvasViewportState
- `canvas/canvas_size_contract.js`
- `interaction/node_interaction_contract.js`
- `migration/schema_1_contract_migrator.js`

## Principios

### Mobile first

- Mobile: 390 px
- Tablet: 768 px
- Desktop: 1180 px

El ancho lo determina el dispositivo. La altura puede editarse por dispositivo.

### Geometría separada de estilo visual

`layout.transform` contiene:

- x
- y
- width
- height
- rotation
- opacity
- origin

### Z-index no responsive

El orden canónico vive en `parent.children[]`.

`LayerStackService` normaliza `style.zIndex` solo como representación derivada.

### Interacción universal

Cualquier nodo puede contener acciones:

- IMAGE
- TEXT
- BUTTON
- CARD
- CONTAINER
- ICON
- VIDEO

Una imagen puede actuar como botón sin cambiar de tipo.

### Modos del viewport

- EDIT
- PREVIEW_CONTINUOUS

## No incluido todavía

- interfaz de altura;
- ocho handles;
- drag de capas;
- Universal Renderer conectado;
- eliminación legacy.

Estas funciones se conectan en los siguientes sprints.
