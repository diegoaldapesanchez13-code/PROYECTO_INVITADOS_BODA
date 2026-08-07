# FASE 6.11 - Component Tree Drag and Drop

## Objetivo

Permitir reordenar elementos desde el arbol de componentes sin depender del canvas.

Esto resuelve un problema practico del editor: algunos botones, mapas, textos o imagenes pueden ser dificiles de seleccionar cuando estan sobre una imagen grande, debajo de otra capa o dentro de una vista movil.

## Alcance implementado

El arbol permite arrastrar y soltar:

- capas de una misma seccion,
- componentes persistentes de una misma seccion.

## Reglas

### Capas

Una capa solo puede soltarse sobre otra capa de la misma seccion.

Al soltarla:

- se actualiza su `z`,
- se mantiene seleccionada,
- se marca el borrador como pendiente de guardar.

### Componentes persistentes

Un componente solo puede soltarse sobre otro componente de la misma seccion.

Al soltarlo:

- se recalcula su `zIndex`,
- se guarda mediante la API del Motor de Componentes,
- se refresca la vista real.

## Restricciones actuales

Todavia no se permite:

- mover componentes entre secciones,
- mezclar capas con componentes,
- agrupar elementos,
- crear contenedores,
- renombrar nodos desde el arbol.

Estas restricciones son intencionales para proteger la paridad entre borrador y vista real.

## Archivos principales

- `invitaciones/static/invitaciones/js/editor_invitacion.js`
- `invitaciones/static/invitaciones/css/editor_invitacion.css`
- `invitaciones/templates/invitaciones/editor_invitacion.html`

## Validacion esperada

- `node --check invitaciones/static/invitaciones/js/editor_invitacion.js`
- `py manage.py check`
- render del editor: 200
- render publico: 200

## Siguiente paso recomendado

Crear un sistema de seleccion y transformacion mas robusto para componentes:

- handles de resize,
- rotacion,
- snap,
- guias,
- constraints responsive,
- mejor soporte tactil para mobile.
