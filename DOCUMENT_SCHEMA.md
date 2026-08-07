# DIRTEC Builder Engine — Document Schema

## Estado

Sprint 6.1.1. Contrato inicial del documento oficial del Builder.

## Estructura

```json
{
  "schemaVersion": 1,
  "documentVersion": 1,
  "builderVersion": "0.6.1",
  "metadata": {},
  "theme": {},
  "assets": [],
  "globals": {},
  "canvasDocument": {}
}
```

`canvasDocument` mantiene el esquema R3 actual durante la migración. Esto permite reorganizar la arquitectura sin perder compatibilidad con lienzos, capas, componentes, interacciones, Countdown, Maps, Video y RSVP.

## Reglas

- El documento es la fuente única del diseño.
- El HTML no se persiste como fuente.
- Los archivos pesados no se guardan dentro del JSON; `assets` contiene referencias.
- Editor, preview y publicación deben consumir el mismo documento.
- Un cambio incompatible exige aumentar `schemaVersion` y crear un migrador.
