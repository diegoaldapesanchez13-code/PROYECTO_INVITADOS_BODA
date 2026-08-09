# PHASE F.1 — Schema V4 Foundation

## Propósito

Crear el contrato V4 y su migrador antes de modificar el runtime.

PHASE F.1 trabaja en **shadow mode**:

```text
runtime actual → Schema V3
contrato futuro → Schema V4
```

El Builder sigue guardando V3. Nada en Django cambia todavía.

## Decisiones V4 ya congeladas

### 1. CANVAS reemplaza SECTION

```text
V3                       V4

sections[]                canvases[]
type: SECTION             type: CANVAS
sectionId                 canvasId
coordinateSpace SECTION   coordinateSpace CANVAS
```

La migración conserva los mismos IDs para evitar romper:

- children;
- parentId;
- assets;
- interacción;
- selección;
- capas.

### 2. Mobile-first

V3:

```text
desktop → tablet → mobile
```

V4:

```text
mobile → tablet → desktop
```

Contrato:

```json
{
  "baseDevice": "mobile",
  "inheritance": {
    "tablet": "mobile",
    "desktop": "tablet"
  }
}
```

### 3. No mutación

`migrateDocumentToV4()` siempre trabaja sobre clones.

### 4. Idempotencia

Aplicar el migrador a un Documento V4 devuelve un V4 equivalente.

## Lo que NO hacemos todavía

No se cambia:

- `BuilderState`;
- `UniversalRenderer`;
- `CanvasManager`;
- Inspector;
- Layer Stack;
- persistencia Django;
- schema validator Django;
- Documento publicado.

Eso será PHASE F.2.

## Gate para F.2

Antes del cutover necesitamos:

- suite V3 completa verde;
- tests V4 verdes;
- migración de documentos reales V3 → V4;
- validator V4;
- cero pérdida de IDs/interacciones/assets.
