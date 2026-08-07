# Sprint 11.3.1 — Transform Lab

## Ruta

```text
/dashboard/editor-invitacion/<evento_id>/engine/transform-lab/
```

## Valida

- selección;
- movimiento;
- ocho handles;
- ancho y alto;
- rotación;
- altura del Canvas;
- Mobile/Tablet/Desktop;
- cancelación con Escape;
- sincronía entre contenido y frame.

## Seguridad

- solo carga mediante GET;
- no guarda;
- no publica;
- no modifica la base de datos;
- no reemplaza el editor oficial;
- no elimina legacy.

## Gate

No se integra History ni Layer Stack hasta validar visualmente que el contenido y el overlay usan exactamente la misma geometría.
