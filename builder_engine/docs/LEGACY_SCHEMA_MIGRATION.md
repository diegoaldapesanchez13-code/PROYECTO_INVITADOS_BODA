# Legacy Schema Migration

## Origen

```text
theme
layout
sections[]
```

## Destino

```text
theme
assets[]
globals
canvases[]
  nodes[]
```

## Conservado

- orden y visibilidad de secciones;
- altura;
- fondo;
- título visual;
- título y descripción;
- capas personalizadas;
- contenido real;
- Countdown compuesto;
- referencias de assets;
- tema y layout anterior.

## Seguridad

La migración es:

- determinista;
- idempotente;
- no destructiva hasta completar la conversión;
- guardada automáticamente como borrador;
- ejecutada solo cuando `legacyMigrationPending` es verdadero y no existen canvases.

El editor anterior continúa disponible como respaldo.
