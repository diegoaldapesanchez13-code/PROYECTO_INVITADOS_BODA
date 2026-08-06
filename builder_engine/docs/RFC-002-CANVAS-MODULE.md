# RFC-002 — Extraer Canvas Module

## Estado
Aprobado e implementado.

## Objetivo
Extraer la administración estructural de lienzos al DIRTEC Builder Engine sin acoplarla al DOM, Django o al renderer actual.

## Alcance
- Contrato normalizado de Canvas.
- Servicio CRUD, selección y reordenamiento.
- Módulo registrable en BuilderApp.
- Adaptador de compatibilidad con documentos Builder R3.
- Pruebas unitarias.

## Fuera de alcance
- UI del panel Lienzos.
- selección visual y handles.
- zoom, pan o viewport.
- sustitución del editor activo.

## Riesgo controlado
`builder_v3` y `static/.../builder` no se modifican. El nuevo módulo vive únicamente en `builder_engine`.
