# Renderer Engine

## Contrato
`RendererService.render()` transforma un Documento en un árbol inmutable:

```text
Document
  -> Canvases ordenados
    -> Render Nodes jerárquicos
```

## Modos
- `EDIT`: selección y transformación; componentes interactivos quedan protegidos.
- `PREVIEW`: interacción real dentro del simulador.
- `PUBLIC`: interacción real para publicación.

## Extensión
```js
rendererModule.registry.register("MY_COMPONENT", renderer);
```

Un renderer recibe `(node, context, children)` y devuelve un descriptor con `id`, `type`, `tag`, `attributes`, `style`, `content` y `children`.

## Adaptadores
- `DomRenderAdapter`: materializa el árbol en DOM.
- `adaptR3Renderer`: puente temporal para renderers del Builder R3.
