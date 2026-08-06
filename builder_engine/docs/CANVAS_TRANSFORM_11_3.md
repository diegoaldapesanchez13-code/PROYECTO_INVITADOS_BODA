# Sprint 11.3 — Canvas, Selection y Transform

Este sprint establece el núcleo definitivo de manipulación visual sobre el Universal Renderer.

## Contratos

- selección primaria y múltiple;
- ocho handles: N, NE, E, SE, S, SW, W, NW;
- rotación;
- movimiento;
- resize real de width/height;
- zoom desacoplado de geometría;
- cancel/commit;
- nodos bloqueados;
- altura editable del Canvas;
- mapper screen → logical;
- overlay calculado desde la misma geometría del nodo.

## Regla crítica

El frame de selección nunca mantiene una geometría paralela.

Debe derivarse del mismo transform que consume el Universal Renderer.

Durante un drag:

1. `TransformSession` produce preview;
2. Renderer recibe preview transform;
3. overlay recibe ese mismo preview;
4. al soltar se genera una sola transacción;
5. History/Persistence se conectarán en la integración visual.

Esto evita el error anterior donde el frame se movía pero el contenido no.

## Todavía no hace

- montaje visual sobre la ruta oficial;
- persistencia;
- History real;
- reparent;
- Layer Stack;
- eliminación legacy.

Esas conexiones se realizan después de validar estos contratos.
