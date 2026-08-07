# S01-P07 - Contenido Real por Tarjeta

Fecha: 2026-08-01

## Objetivo

Separar la edicion visual de Ceremonia y Recepcion para que no dependan de un unico bloque global.

La seccion `DETALLES` ahora permite configurar cada tarjeta de forma independiente, manteniendo los datos reales del evento.

## Cambios

### Detalles

Cada tarjeta tiene configuracion propia:

- visible;
- etiqueta;
- mostrar foto/video;
- mostrar direccion;
- mostrar mapa/boton;
- fondo de tarjeta;
- posicion de media: arriba, abajo u oculta.

La informacion sigue leyendo datos reales:

- `evento.fecha_misa`;
- `evento.lugar_misa`;
- `evento.direccion_ceremonia`;
- `evento.link_mapa_misa`;
- `evento.fecha_fiesta`;
- `evento.lugar_fiesta`;
- `evento.direccion_recepcion`;
- `evento.link_mapa_fiesta`.

### Secciones hibridas conectadas al motor

Se conectaron al motor `realContent`:

- Regalos;
- Album;
- Album compartido.

Estas secciones pueden usar controles globales de acomodo visual, ancho, escala, separacion, tarjetas y sombra.

### RSVP

RSVP se excluyo del panel `realContent`.

La confirmacion se mantiene como bloque funcional estable. Solo debe editarse mediante:

- fondo;
- portada/imagen completa;
- titulo o encabezado;
- contenido rapido del formulario.

## Validacion

- `node --check invitaciones/static/invitaciones/js/editor_invitacion.js`
- `py manage.py check`
- carga de templates principales;
- render publico con `Client`;
- render del editor con `Client`.

