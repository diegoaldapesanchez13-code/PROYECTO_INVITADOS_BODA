# RFC-005 — Assets Module

## Estado
Aprobado e implementado.

## Objetivo
Extraer la biblioteca multimedia como módulo independiente del Builder Engine. El Documento solo conserva referencias y metadatos; los bytes viven en almacenamiento externo.

## Decisiones
- Se prohíben URLs `data:` y `blob:` en documentos persistentes.
- El módulo no conoce Django ni `MEDIA_ROOT`.
- La subida y eliminación se inyectan mediante adaptadores.
- Un asset puede reutilizarse en múltiples capas.
- No se elimina un asset referenciado salvo operación forzada.
