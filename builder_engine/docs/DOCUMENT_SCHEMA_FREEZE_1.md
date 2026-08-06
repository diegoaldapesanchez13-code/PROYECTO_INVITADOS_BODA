# Document Schema Freeze — Schema 1

Antes de integrar Django se congelan los nombres raíz:

```json
{
  "schemaVersion": 1,
  "documentVersion": 1,
  "builderVersion": "0.14.0",
  "metadata": {},
  "theme": {},
  "assets": [],
  "globals": {},
  "canvases": []
}
```

## Reglas

- `metadata`, `theme` y `globals` son objetos.
- `assets` y `canvases` son arreglos.
- Los nodos viven dentro de `canvases[].nodes`.
- Los archivos no se guardan dentro del Documento.
- El estado del workspace no se guarda dentro del Documento.
- Cambios incompatibles futuros requieren incrementar `schemaVersion` y un migrador.
