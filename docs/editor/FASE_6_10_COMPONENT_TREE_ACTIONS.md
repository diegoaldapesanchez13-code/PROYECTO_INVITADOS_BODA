# FASE 6.10 - Component Tree Actions

## Objetivo

Convertir el arbol de componentes en una herramienta operable, no solamente en una lista de seleccion.

El usuario debe poder controlar elementos dificiles de tocar en el canvas, especialmente en mobile o cuando estan debajo de imagenes, mapas o secciones largas.

## Acciones agregadas

El arbol ahora puede mostrar acciones por nodo:

- Mostrar / ocultar.
- Bloquear / desbloquear.
- Enviar atras.
- Traer al frente.
- Eliminar.

## Capacidades por tipo

### Seccion

- Mostrar / ocultar.

### Capa

- Mostrar / ocultar.
- Bloquear / desbloquear.
- Enviar atras.
- Traer al frente.
- Eliminar, solo cuando es capa personalizada.

### Componente persistente

- Mostrar / ocultar.
- Bloquear / desbloquear.
- Enviar atras.
- Traer al frente.
- Eliminar.

Los cambios de componentes persistentes se guardan por medio de la API del Motor de Componentes.

## Archivos principales

- `invitaciones/templates/invitaciones/editor_invitacion.html`
- `invitaciones/static/invitaciones/js/editor_invitacion.js`
- `invitaciones/static/invitaciones/css/editor_invitacion.css`

## Compatibilidad

Este cambio mantiene el flujo anterior:

- Se puede seguir seleccionando desde el canvas.
- Se puede seguir usando el Inspector Universal.
- Las acciones antiguas de capas y componentes permanecen.
- No se eliminan paneles existentes.

## Validacion

- `node --check invitaciones/static/invitaciones/js/editor_invitacion.js`
- `py manage.py check`
- carga de templates principales con `get_template`
- render del editor con `django.test.Client`: 200
- render publico con `django.test.Client`: 200

## Pendiente

- Reordenamiento drag and drop dentro del arbol.
- Agrupacion de componentes.
- Renombrar nodos desde el arbol.
- Menu contextual con click derecho / long press.
- Confirmacion visual antes de eliminar elementos importantes.
