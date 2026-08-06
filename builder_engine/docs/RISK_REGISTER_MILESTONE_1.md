# Registro de riesgos — Milestone 1

| ID | Riesgo | Probabilidad | Impacto | Acción |
|---|---|---:|---:|---|
| R-01 | Persistir un schema aún cambiante | Alta | Alta | No integrar Django antes de Sprint 9 |
| R-02 | Tres copias del Builder divergen | Alta | Alta | Declarar `builder_engine` como fuente oficial |
| R-03 | Componentes R3 no migran exactamente | Media | Alta | Contratos y adaptadores con pruebas de equivalencia |
| R-04 | History consume memoria en documentos grandes | Media | Media | Límite configurable y futura estrategia de patches |
| R-05 | Estado visual contamina publicación | Media | Media | Introducir `WorkspaceState` separado |
| R-06 | Orden de arranque implícito | Media | Alta | Dependencias y prioridad de módulos |
| R-07 | SDK acepta plugins inválidos | Media | Media | Validación y versionado de contratos |
