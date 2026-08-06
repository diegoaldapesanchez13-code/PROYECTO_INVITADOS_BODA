# Decisiones de arquitectura — Milestone 1

## ADR-M1-01 — Builder Engine independiente del SaaS

**Estado:** Aprobado

El Engine no conocerá bodas, invitados, empresas, planners ni rutas Django. El SaaS proporcionará datos y puertos mediante adaptadores.

## ADR-M1-02 — Documento como fuente de verdad

**Estado:** Aprobado

Editor, preview y publicación usarán el mismo Documento. No se guardará HTML como fuente.

## ADR-M1-03 — Universal Renderer

**Estado:** Aprobado

Existirá un solo renderer con modos EDIT, PREVIEW y PUBLIC.

## ADR-M1-04 — Assets por referencia

**Estado:** Aprobado

El Documento almacena IDs, URLs y metadatos. Los archivos viven en almacenamiento persistente.

## ADR-M1-05 — Historial por snapshots limitados durante la migración

**Estado:** Aprobado temporalmente

Se usarán snapshots normalizados con límite configurable. Los patches se evaluarán después de congelar el esquema.

## ADR-M1-06 — Django se integra por puertos

**Estado:** Aprobado

El Core no ejecutará `fetch()` con rutas del proyecto. Persistence e integración Django inyectarán operaciones.

## ADR-M1-07 — Estado de workspace separado

**Estado:** Aprobado

Zoom, selección, pestañas, scrolls y acordeones no formarán parte del Documento publicado.

## ADR-M1-08 — Integración diferida

**Estado:** Aprobado

Django se conectará únicamente después de extraer Components, Interaction y Persistence.
