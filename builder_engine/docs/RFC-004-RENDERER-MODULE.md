# RFC-004 — Renderer Module

## Estado
Aprobado e implementado.

## Objetivo
Extraer el renderizador como módulo independiente del DIRTEC Builder Engine y establecer un único contrato para los modos `EDIT`, `PREVIEW` y `PUBLIC`.

## Decisiones
- El Renderer consume únicamente el Documento oficial.
- El núcleo produce un árbol de render headless; el DOM es un adaptador.
- Los componentes registran renderers por tipo.
- Los tres modos comparten la misma estructura y difieren solo en capacidades.
- Django y la lógica de negocio quedan fuera del módulo.

## Compatibilidad
`r3_renderer_adapter.js` permite envolver renderers heredados mientras se migra cada componente.
