# Components Engine

Versión del contrato: 1

El módulo `components` centraliza el registro, validación, creación e inserción de componentes del DIRTEC Builder Engine.

## Contratos

Cada componente declara:

- `type`
- `version`
- `label`
- `icon`
- `element`
- `category`
- `inspector`
- `renderer`
- `capabilities`
- `defaults`
- `factory` opcional
- `validate` opcional
- `migrations`

## Blueprints

Un Blueprint genera una jerarquía de componentes sin introducir HTML especial en el Documento. El Countdown compuesto es el primer Blueprint oficial.

## Reglas

- El tipo es único y se normaliza a mayúsculas.
- El SDK valida definiciones antes de registrarlas.
- La fábrica aplica defaults sin mutar la definición.
- Los nodos generados son documentos serializables.
- Components no conoce Django ni el DOM.
