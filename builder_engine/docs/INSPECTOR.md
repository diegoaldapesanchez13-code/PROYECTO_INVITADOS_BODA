# Inspector Module

El módulo Inspector administra selección, edición de propiedades y resolución de paneles sin depender del DOM.

## Componentes
- `InspectorRegistry`: registra contratos de panel.
- `InspectorService`: selección y mutaciones del nodo.
- `InspectorModule`: ciclo de vida registrable en `BuilderApp`.
- `r3_inspector_adapter`: compatibilidad gradual con paneles R3.

## Persistencia de interfaz
El estado abierto/cerrado de grupos y la posición de scroll se guardan en memoria por nodo. El renderer de interfaz consumirá estos valores sin reconstruir el estado del Inspector.
