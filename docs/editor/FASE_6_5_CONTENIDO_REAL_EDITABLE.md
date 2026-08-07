# S01-P06 - Contenido Real Editable

Fecha: 2026-08-01

## Objetivo

Permitir que el contenido real de las secciones hibridas sea configurable desde el editor sin convertirlo en texto plano.

La regla principal es:

- los datos siguen saliendo de Django;
- la presentacion se controla desde el editor;
- la Vista Rapida, el borrador y la Vista Real deben usar la misma configuracion.

## Alcance de esta entrega

La primera implementacion se aplico a `DETALLES`.

El bloque real de Detalles ahora puede controlar:

- posicion visual X/Y;
- ancho;
- escala;
- opacidad;
- separacion;
- layout en una o dos columnas;
- alineacion;
- fondo, radio, padding y sombra de tarjetas;
- tamano de texto;
- mostrar u ocultar fotos;
- mostrar u ocultar direccion;
- mostrar u ocultar mapas/botones;
- mostrar u ocultar Ceremonia;
- mostrar u ocultar Recepcion;
- cambiar etiquetas de Ceremonia y Recepcion.

## Arquitectura

Se agrego `section.config.realContent`.

Ejemplo conceptual:

```json
{
  "realContent": {
    "x": 50,
    "y": 50,
    "width": 100,
    "scale": 1,
    "layout": "grid",
    "align": "center",
    "gap": 14,
    "cardBg": "#ffffff",
    "cardRadius": 0,
    "cardPadding": 16,
    "showMedia": true,
    "showAddress": true,
    "showMaps": true,
    "items": {
      "ceremony": {
        "visible": true,
        "label": "Ceremonia"
      },
      "reception": {
        "visible": true,
        "label": "Recepcion"
      }
    }
  }
}
```

## Archivos modificados

- `invitaciones/templates/invitaciones/editor_invitacion.html`
- `invitaciones/static/invitaciones/js/editor_invitacion.js`
- `invitaciones/static/invitaciones/css/editor_invitacion.css`
- `invitaciones/static/invitaciones/css/invitacion.css`
- `invitaciones/templates/invitaciones/partials/_section_details.html`
- `invitaciones/views.py`

## Pendiente

Extender el mismo patron a:

- Regalos;
- Album;
- Album compartido;
- RSVP.

