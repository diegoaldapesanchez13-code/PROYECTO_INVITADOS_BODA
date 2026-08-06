# Arquitectura del Builder Engine

## Capas actuales

1. `frontend/app`: Kernel, configuración y registro de módulos.
2. `frontend/document`: contrato, validación y serialización del documento.
3. `frontend/sdk`: API mínima para registrar extensiones.

Los módulos visuales permanecen temporalmente en `builder_v3` y `static/.../builder` hasta migrarse por sprints completos.
