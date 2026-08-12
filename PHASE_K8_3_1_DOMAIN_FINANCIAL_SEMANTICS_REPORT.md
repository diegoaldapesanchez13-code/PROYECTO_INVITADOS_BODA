# K.8.3.1 — Domain Financial Semantics

## Objetivo

Separar de forma explícita tres conceptos que antes estaban mezclados en `ServicioEvento`:

- `costo_proveedor`: costo real/esperado para la empresa frente al proveedor.
- `valor_contratado`: valor comercial atribuible al servicio dentro del acuerdo o paquete.
- `cargo_adicional_cliente`: importe que se agrega al contrato base por extra/upgrade.

Los campos legacy `costo_total`, `precio_cliente` y `ajuste_cliente` permanecen temporalmente porque vistas y flujos anteriores todavía los utilizan.

## Regla por modalidad

- `INCLUIDO`: puede tener `valor_contratado`, pero `cargo_adicional_cliente = 0`.
- `UPGRADE`: `cargo_adicional_cliente` representa únicamente la diferencia cobrada.
- `ADICIONAL`: normalmente el cargo adicional coincide con el precio comercial del servicio, aunque ambos campos permanecen separados.

## Materialización desde paquete

`ServicioPaquete.precio_incluido` se interpreta como valor comercial del componente dentro del paquete. No se utiliza como costo del proveedor porque el catálogo no aporta evidencia suficiente para afirmar ese costo.

Por compatibilidad temporal, `precio_cliente` conserva el valor incluido mientras las pantallas antiguas migran a `valor_contratado`. `costo_total` y `costo_proveedor` quedan en cero para servicios materializados sin costo de proveedor conocido.

## Migración

`proveedores.0009_financial_semantics_k831` agrega los dos campos nuevos y realiza backfill conservador:

- incluido -> cargo adicional 0;
- upgrade -> usa `ajuste_cliente` como primera opción;
- adicional originado en catálogo/paquete -> usa `precio_cliente` como cargo cuando ya existe esa semántica;
- registros legacy `MANUAL` -> cargo adicional 0, porque `costo_total/precio_cliente` antiguos son ambiguos y no deben convertirse automáticamente en deuda del cliente;
- valor contratado -> usa `precio_cliente` o, si está vacío, `costo_total` como fallback histórico.

## Builder

No se modifica ningún archivo del Builder.
