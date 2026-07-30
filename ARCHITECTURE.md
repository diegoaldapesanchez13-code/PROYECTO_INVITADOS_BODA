# ARCHITECTURE

## Proyecto

`PROYECTO_INVITADOS_BODA-INTEGRACION` esta evolucionando de una aplicacion de invitaciones digitales hacia un constructor visual profesional para eventos. El objetivo final es que una empresa, planner o cliente autorizado pueda construir y ajustar una invitacion completa desde interfaz grafica, sin modificar HTML o CSS manualmente.

## Version actual documentada

Version funcional actual: `v5.2-live-preview`

Esta version contiene el sistema estable previo al gran salto del Universal Editing Engine.

## Capas principales

### Evento

`EventoBoda` sigue siendo la entidad central. Contiene datos reales del evento: nombres, fechas, lugares, musica, portada, mapas, RSVP, regalos, menus, albumes y configuracion general.

### Secciones

`SeccionInvitacion` representa cada bloque visible: portada, padres y padrinos, cuenta regresiva, detalles, dress code, itinerario, album, menu, regalos, album compartido y RSVP.

Cada seccion conserva:

- orden,
- visibilidad,
- fondo,
- imagen o video completo,
- titulo,
- descripcion,
- configuracion visual.

### Diseno visual

`DisenoInvitacion` guarda la configuracion del editor existente: tema, layout, fondos, capas libres, enfoque responsive, posiciones y opciones de publicacion.

### Capas libres

Las capas libres viven dentro de la configuracion JSON de `DisenoInvitacion`. Permiten agregar texto, imagen o video sobre una seccion sin tocar templates.

Soportan:

- posicion,
- ancho,
- escala,
- rotacion,
- opacidad,
- z-index,
- bloqueo,
- visibilidad,
- fit de media.

### Motor de Componentes

`ComponenteInvitacion` es la nueva capa persistente creada para el constructor visual. Cada componente pertenece a un evento y a una seccion.

Campos principales:

- `evento`
- `seccion`
- `tipo`: `TEXTO`, `IMAGEN`, `BOTON`
- `x`, `y`
- `width`, `height`
- `rotation`
- `opacity`
- `z_index`
- `locked`
- `hidden`
- `properties`

El motor de componentes convive con el sistema anterior. No sustituye todavia todos los elementos HTML originales.

## Refactor de templates

La invitacion publica se apoya progresivamente en partials reutilizables:

- `_section_base.html`
- `_section_header.html`
- `_componentes_invitacion.html`
- `_capas_personalizadas.html`
- partials especificos por seccion

`_section_base.html` permite renderizar fondo, capas libres, componentes persistentes, imagen completa y encabezado sin duplicar esa logica en cada seccion.

## Live Preview Editor

El editor visual puede abrir la invitacion publica real dentro de un iframe same-origin usando el borrador:

`/invitacion/<codigo>/?preview=1&draft=1`

Modos:

- `Diseno rapido`: canvas interno compatible con la primera etapa del editor.
- `Vista real`: invitacion publica real con datos, formularios, mapas, botones y componentes.
- `Editar`: permite seleccionar y mover componentes sobre la invitacion real.
- `Probar`: permite usar botones, formularios, links y mapas dentro del iframe.

## Endpoints del Motor de Componentes

- `GET /dashboard/editor-invitacion/<evento_id>/componentes/`
- `POST /dashboard/editor-invitacion/<evento_id>/componentes/`
- `POST /dashboard/editor-invitacion/<evento_id>/componentes/<componente_id>/`
- `PATCH /dashboard/editor-invitacion/<evento_id>/componentes/<componente_id>/`
- `DELETE /dashboard/editor-invitacion/<evento_id>/componentes/<componente_id>/`

## Compatibilidad mantenida

La version actual mantiene compatibilidad con:

- templates HTML existentes,
- datos dinamicos de Django,
- RSVP personal y familiar,
- invitados adultos/ninos,
- importacion CSV/XLSX de invitados,
- mesas y QR,
- fondos e imagenes completas por seccion,
- videos y GIFs,
- albumes,
- regalos,
- mapas,
- menus,
- capas libres,
- componentes persistentes.

## Limite actual

La version `v5.2-live-preview` permite mover componentes nuevos `ComponenteInvitacion`, pero todavia no convierte todos los elementos HTML existentes en objetos editables.

Elementos como RSVP, mapas, countdown, botones existentes, titulos, textos nativos e imagenes propias de secciones aun dependen parcialmente del HTML y CSS de plantilla.

## Siguiente version

La siguiente version debe ser `v5.3-universal-editing-engine`.

Objetivo:

Convertir todos los elementos visibles en entidades editables mediante un Universal Editing Engine.

No debe ser una mejora pequena. Debe crear una arquitectura general para registrar, seleccionar, transformar, persistir y editar cualquier elemento visible.

## Fases siguientes

### Fase 5.3 - Universal Editing Engine

Registrar cualquier elemento HTML visible como editable.

### Fase 5.4 - Selection Engine

Seleccion visual con borde, handles y componente activo.

### Fase 5.5 - Transform Engine

Mover, redimensionar, rotar, snap, grid y guias inteligentes.

### Fase 5.6 - Properties Panel

Editar texto, fuente, color, imagen, video, boton, URL, mapa, countdown, formulario, padding, margin, borde, sombra y animacion desde interfaz.

### Fase 5.7 - Component Library

Biblioteca drag and drop para texto, imagen, video, boton, QR, mapa, countdown, Spotify, timeline, menu, dress code, RSVP, redes sociales, WhatsApp, decoraciones, SVG, iconos, flores y separadores.

### Fase 5.8 - History Engine

Undo, redo, snapshots y versionado.

### Fase 5.9 - Responsive Engine

Posicion independiente por desktop, tablet y mobile manteniendo el mismo contenido.

### Fase 6 - Plantillas sin HTML rigido

Construir plantillas con componentes y configuracion, reduciendo la dependencia de HTML especifico.
