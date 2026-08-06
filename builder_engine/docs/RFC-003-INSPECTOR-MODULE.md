# RFC-003 — Inspector Module

## Estado
Aprobado e implementado.

## Objetivo
Extraer el estado y los contratos del Inspector fuera de la interfaz R3, manteniendo el renderizado DOM como una integración posterior.

## Decisiones
- El Inspector del Engine no conoce HTML ni Django.
- La selección se realiza mediante IDs estables de nodos.
- Los paneles se registran por contrato y se filtran por tipo, capacidad y pestaña.
- El estado de acordeones y scroll se conserva por nodo.
- La edición de propiedades usa rutas anidadas y actualiza el Documento oficial.
- El Inspector R3 se conectará mediante un adaptador, no mediante imports directos al Kernel.
