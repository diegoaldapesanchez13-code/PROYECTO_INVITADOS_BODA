# Interaction Engine

Versión del contrato: 1

El módulo `interaction` ejecuta acciones declarativas sin acoplar componentes al navegador, Django o la vista pública.

## Triggers

- CLICK
- SUBMIT
- CHANGE
- ENTER_VIEW

## Acciones

- NONE
- URL
- WHATSAPP
- GOOGLE_MAPS
- CANVAS
- COMPONENT_EVENT

## Puertos de ejecución

El host puede inyectar:

- `navigation.openUrl`
- `navigation.goToCanvas`
- `emitComponentEvent`

En pruebas o render headless, los ejecutores devuelven una descripción de la acción en lugar de acceder directamente a `window`.

## Seguridad

El ejecutor URL solo acepta:

- http
- https
- mailto
- tel
- rutas relativas
- anchors
