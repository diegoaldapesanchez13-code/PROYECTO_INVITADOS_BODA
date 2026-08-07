# FASE 6.7 - Paridad de Detalles y Assets Reales

## Objetivo

Que lo editado en el editor coincida con la invitacion real, especialmente en la seccion `DETALLES`.

## Cambios

- Se agregaron destinos de asset:
  - `CEREMONIA`
  - `RECEPCION`
- Estos destinos actualizan:
  - `config.theme.ceremonyAsset`
  - `config.theme.receptionAsset`
  - `EventoBoda.foto_ceremonia`
  - `EventoBoda.foto_recepcion`

## Detalles por tarjeta

`realContent.items.ceremony` y `realContent.items.reception` ahora soportan:

- `visible`
- `label`
- `order`
- `showMedia`
- `showAddress`
- `showMaps`
- `cardBg`
- `mediaPosition`
- `mapDisplay`
- `buttonLabel`

## Modos de mapa

- `button-map`: muestra boton y mapa.
- `button-only`: muestra solo boton.
- `map-only`: muestra solo mapa.
- `hidden`: oculta boton y mapa.

## Imagen de ubicacion

Cada tarjeta puede guardar `mapAsset`:

- `realContent.items.ceremony.mapAsset`
- `realContent.items.reception.mapAsset`

La Vista Real prioriza `mapAsset` antes que Google Maps embed/iframe. Esto permite usar una imagen o video como "donde" cuando el mapa real no encaja visualmente con la invitacion.

## Regla de RSVP

`RSVP` no usa `realContent`. Solo debe permitir ajustes de fondo, portada/imagen completa y titulo para no romper el formulario de confirmacion.
