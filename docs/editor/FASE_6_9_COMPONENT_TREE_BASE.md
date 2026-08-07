# FASE 6.9 - Component Tree Base

## Objetivo

Agregar un arbol de seleccion para que el editor no dependa unicamente de tocar elementos en el canvas.

## Estructura inicial

```text
Pagina / Invitacion
  Seccion
    Capa base
    Contenido real
    Componente
```

## Selecciones soportadas

- Seccion.
- Capa base o libre.
- Contenido real.
- Componente persistente.

## Sincronizacion

Al seleccionar desde el arbol se actualiza:

- `selectedId`
- `selectedComponentId`
- `activeLayer`
- Inspector Universal
- Vista Rapida
- Vista Real

## Pendiente

- Reordenamiento drag and drop desde el arbol.
- Agrupar / desagrupar.
- Bloquear / ocultar directamente desde cada fila.
- Filtros por tipo.
- Estados responsive por dispositivo.
