# ARCHITECTURE
# DIRTEC VISUAL STUDIO
# ARCHITECTURE.md
## Documento Maestro de Arquitectura

---

# VISIÓN DEL PROYECTO

DIRTEC Visual Studio es una plataforma profesional para la creación, edición y publicación de documentos visuales.

Actualmente el primer producto construido sobre esta plataforma es el sistema de Invitaciones Digitales para Eventos.

Sin embargo, la arquitectura está diseñada para soportar en el futuro:

- Bodas
- XV Años
- Bautizos
- Cumpleaños
- Eventos Corporativos
- Landing Pages
- Catálogos
- Micrositios
- Invitaciones Empresariales
- Cualquier documento visual editable

El objetivo es evolucionar hacia un editor visual profesional inspirado en la filosofía de herramientas como Figma, Webflow, Canva y Framer, pero especializado en la industria de eventos.

---

# ESTADO ACTUAL DEL PROYECTO

Proyecto:

PROYECTO_INVITADOS_BODA-INTEGRACION

Estado:

Versión estable:

v5.2-live-preview

Esta versión representa el último estado estable antes del gran cambio arquitectónico.

A partir de este punto comienza oficialmente la consolidación del editor.

---

# FILOSOFÍA

Todo el proyecto deberá cumplir los siguientes principios.

• Una única fuente de verdad.

• Un único documento editable.

• Una única Vista Real.

• Todo elemento visible debe poder editarse.

• Ninguna funcionalidad debe depender de HTML rígido.

• Arquitectura modular.

• Código limpio.

• Componentes reutilizables.

• Bajo acoplamiento.

• Alta cohesión.

• Compatibilidad hacia atrás.

---

# ARQUITECTURA ACTUAL

La versión actual se compone principalmente de:

EventoBoda

↓

SeccionInvitacion

↓

DisenoInvitacion

↓

Capas Libres

↓

Contenido Real

↓

Componentes Persistentes

↓

Vista Pública

El sistema mantiene compatibilidad completa con las plantillas actuales.

El editor actual combina herramientas históricas con nuevas capacidades del Motor de Componentes.

---

# ARQUITECTURA OBJETIVO

Toda la evolución futura del proyecto deberá acercarse a la siguiente arquitectura.

Documento Universal

↓

Selection Engine

↓

Inspector Engine

↓

Renderer Engine

↓

Layout Engine

↓

Responsive Engine

↓

History Engine

↓

Asset Engine

↓

Publish Engine

↓

Vista Real

La Vista Real será el único documento editable.

El Documento Universal será la única fuente de verdad.

El HTML dejará de ser la fuente principal y pasará a ser únicamente el resultado del Renderer.

---

# FASE ACTUAL

## FASE 3.5

EDITOR CONSOLIDATION

Objetivo:

Consolidar completamente el editor antes de comenzar el Component Engine.

Esta fase NO agrega funcionalidades nuevas.

Su propósito es eliminar deuda técnica.

Objetivos:

✓ eliminar Diseño Rápido

✓ consolidar Vista Real

✓ simplificar Inspector

✓ limpiar JavaScript

✓ limpiar CSS

✓ eliminar listeners duplicados

✓ limpiar responsabilidades mezcladas

✓ mejorar UX

✓ preparar Documento Universal

✓ preparar Component Engine

Al finalizar esta fase el proyecto deberá encontrarse completamente estable.

---

# METODOLOGÍA DE DESARROLLO

Cada módulo deberá seguir exactamente el siguiente flujo.

1.

Inspección

Comprender completamente el módulo.

Nunca modificar código sin entenderlo.

2.

Auditoría

Detectar:

responsabilidades

dependencias

deuda técnica

duplicación

riesgos

3.

Plan

Dividir el trabajo en pequeños pasos.

Cada paso debe ser independiente.

Cada paso debe poder probarse.

Cada paso debe ser reversible.

4.

Implementación

Modificar únicamente el paso autorizado.

Nunca varios módulos grandes simultáneamente.

5.

Pruebas

Desktop

Mobile

Vista Real

Publicación

6.

Documentación

Actualizar documentación.

7.

Checkpoint Git

Cada fase importante termina con un checkpoint.

---

# REGLAS DEL PROYECTO

Nunca romper compatibilidad.

Nunca eliminar funcionalidad existente sin justificar.

Nunca hacer refactorizaciones masivas.

Siempre trabajar por módulos.

Todo cambio debe poder revertirse.

Todo cambio debe documentarse.

Todo cambio debe probarse.

No agregar deuda técnica nueva.

La Vista Real siempre será la referencia visual.

La arquitectura siempre tendrá prioridad sobre soluciones rápidas.

---

# DOCUMENTACIÓN OFICIAL

Este proyecto cuenta con documentación oficial.

Product Vision

Software Architecture Reference (SAR)

Engineering Specification

Blueprint

Universal Document

UX Specification

Software Implementation Reference

Toda implementación deberá respetar dicha documentación.

En caso de conflicto, prevalecerá la arquitectura oficial.

---

# ROADMAP

v5.2

↓

FASE 3.5

Editor Consolidation

↓

v6.0

DIRTEC Visual Studio Core

↓

v6.5

Component Engine

↓

v7.0

Universal Document

↓

v8.0

Marketplace

↓

v8.5

Plataforma Multiempresa

↓

v9.0

AI Assisted Visual Builder

---

# IMPORTANTE

Toda la documentación técnica existente a continuación (EventoBoda, SeccionInvitacion, DisenoInvitacion, Capas Libres, Componentes Persistentes, Inspector Universal, Component Tree, Live Preview, Endpoints, Compatibilidad, etc.) permanece vigente y forma parte del estado actual del proyecto.

Las siguientes secciones describen cómo está construido actualmente el sistema.

Las secciones anteriores describen hacia dónde evolucionará oficialmente DIRTEC Visual Studio.

Ambas forman parte del mismo documento maestro de arquitectura.

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

Transformacion actual:

- seleccion desde canvas, vista real, inspector o arbol,
- movimiento por drag,
- redimensionamiento por handles en Vista Rapida,
- redimensionamiento por handles en Vista Real modo `Editar`,
- persistencia de posicion y tamano mediante la API de componentes.

Los handles actuales cubren resize desde esquinas. Rotacion visual, snap, guias y constraints responsive quedan como fases posteriores del motor de transformacion.

### Contenido real editable

`realContent` vive dentro de `section.config` y controla los bloques dinamicos que siguen viniendo de Django, pero que necesitan acomodo visual desde el editor.

Secciones soportadas:

- `DETALLES`
- `REGALOS`
- `ALBUM`
- `ALBUM_COMPARTIDO`

`RSVP` queda fuera de esta capa para proteger el formulario. En RSVP se puede editar fondo, portada/imagen completa y titulo, pero no se modifica la estructura interna de confirmacion.

En `DETALLES`, `realContent.items` separa `ceremony` y `reception`. Cada tarjeta puede controlar etiqueta, orden, fondo, visibilidad de foto/direccion/mapa, posicion de foto, texto de boton y modo de acceso a mapa. Las fotos reales se asignan desde assets usando `CEREMONIA` y `RECEPCION`, lo que mantiene sincronizados borrador y vista publica.

Las imagenes de ubicacion se guardan como `mapAsset` dentro de cada item. Esto permite reemplazar el iframe de mapa por una imagen/video visual sin perder el link del boton de ubicacion.

Esta capa es temporalmente compatible con el editor actual. El siguiente salto arquitectonico debe consolidar estas propiedades en un Inspector Universal y en un arbol de componentes.

### Inspector Universal

El editor ya cuenta con una primera base de Inspector Universal dentro del panel de propiedades. Este inspector no reemplaza de golpe los paneles existentes; convive con ellos para mantener compatibilidad.

Objetivo del inspector:

- detectar el objetivo seleccionado,
- mostrar un resumen del objetivo,
- exponer controles comunes de transformacion,
- reutilizar la misma logica para secciones, capas, contenido real y componentes,
- servir como puente hacia un futuro Component Tree.

Tipos iniciales:

- `section`: seccion completa.
- `layer`: capa activa de la seccion.
- `real`: contenido real/dinamico de la seccion.
- `component`: componente persistente del motor visual.

Esta base permite empezar a migrar propiedades a un panel unico sin romper el editor actual.

### Component Tree

El editor cuenta con una primera base de arbol de componentes en el panel izquierdo.

Estructura inicial:

```text
Pagina / Invitacion
  Seccion
    Capa base
    Contenido real
    Componente persistente
```

El arbol permite seleccionar elementos sin depender exclusivamente del canvas. Esto es importante para secciones con imagenes grandes, botones encimados, mapas o componentes pequenos en mobile.

Acciones actuales del arbol:

- mostrar / ocultar,
- bloquear / desbloquear,
- enviar atras,
- traer al frente,
- eliminar componentes persistentes,
- eliminar capas personalizadas,
- reordenar capas con drag and drop,
- reordenar componentes persistentes con drag and drop.

Las acciones se muestran segun la capacidad del nodo. Una seccion puede ocultarse; una capa puede bloquearse o cambiar orden; un componente persistente puede eliminarse y guardar su nuevo estado en la base de datos.

El reordenamiento por drag and drop esta limitado intencionalmente al mismo tipo de nodo y a la misma seccion:

- capa hacia capa,
- componente hacia componente.

Esto evita que un componente cambie accidentalmente de seccion o que se mezclen capas temporales del editor con componentes persistentes.

La seleccion del arbol sincroniza:

- `selectedId`
- `selectedComponentId`
- `activeLayer`
- Inspector Universal
- Vista Rapida
- Vista Real

El Component Tree todavia no implementa agrupaciones ni movimiento de componentes entre secciones, pero ya permite operar y reordenar elementos sin depender de que sean faciles de tocar en el canvas.

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

## Layout State del Diseno Rapido

En `v5.3-editor-consolidation` el Diseno Rapido comienza a comportarse como canvas persistente y no como una maqueta recalculada en cada render.

Cada seccion conserva su propio estado de layout dentro de `section.config`:

- alto,
- ancho,
- escala,
- padding,
- margen,
- estado expandido,
- estado colapsado,
- altura minima,
- altura maxima,
- aspect ratio opcional.

`editor_invitacion.js` aplica estos valores mediante `applyPreviewSectionLayout`. Django los conserva en `normalizar_configuracion_editor`.

Esta capa pertenece solo al editor. La Vista Real continua como render final publico y no cambia su arquitectura.

## Resize Handles del Diseno Rapido

La fase `S01-P03` agrega controles visuales de redimensionamiento sobre la tarjeta seleccionada en la Vista Rapida.

Los handles actualizan el mismo `layout state` persistente de la seccion:

- `layoutWidth` para ancho,
- `sectionHeight` para alto,
- `layoutAutoHeight`, `layoutCollapsed`, `layoutExpanded` y `layoutAspectRatio` para conservar un estado coherente durante el resize.

La implementacion vive en `editor_invitacion.js` mediante `attachSectionResizeHandles`. Los estilos visuales viven en `editor_invitacion.css`.

Esta capa sigue limitada al editor. La Vista Real conserva su render publico independiente.

## Paridad entre Borrador y Vista Real

La fase `S01-P04` refuerza que el editor no publique una configuracion distinta a la que el usuario esta editando.

Reglas agregadas:

- Publicar no acepta payloads vacios como fuente principal; si no hay secciones en el payload, usa `configuracion_borrador`.
- Guardar y publicar sincronizan primero el formulario de contenido rapido.
- La Vista Rapida de secciones hibridas usa clases y estructura cercanas a los partials publicos.

Secciones alineadas en Vista Rapida:

- Detalles,
- Regalos / datos bancarios,
- Album,
- Album compartido,
- RSVP.

La Vista Rapida sigue siendo un renderer del editor, no reemplaza a la Vista Real. Para validacion final, la fuente de verdad visual sigue siendo el iframe de borrador con `?draft=1`.

## Componentes Editables Basicos

La fase `S01-P05` convierte los componentes iniciales del builder en elementos editables desde el inspector.

Componentes soportados:

- Texto,
- Imagen,
- Boton.

Cada componente se guarda en `ComponenteInvitacion` y se edita mediante la API de componentes.

El inspector permite modificar:

- posicion,
- tamano,
- rotacion,
- opacidad,
- z-index,
- bloqueo,
- visibilidad,
- propiedades propias de cada tipo,
- eliminacion.

El drag de componentes en Vista Rapida usa dimensiones visuales (`getBoundingClientRect`) para respetar tarjetas escaladas y reducir saltos al soltar.

Esta fase no implementa todavia resize handles por componente, snap, grid ni rotacion visual con manijas.

## Contenido Real Editable

La fase `S01-P06` introduce `section.config.realContent` para separar datos dinamicos y presentacion visual.

El contenido real no se convierte en texto libre. Sigue vinculado a los modelos de Django, pero su apariencia se controla desde el editor mediante variables:

- posicion visual;
- ancho;
- escala;
- opacidad;
- layout;
- separacion;
- estilo de tarjetas;
- visibilidad de elementos internos.

La primera seccion migrada es `DETALLES`. Sus tarjetas de Ceremonia y Recepcion siguen leyendo:

- fechas del evento;
- lugares;
- direcciones;
- enlaces de mapa;
- embeds;
- fotos o videos.

El editor solo controla como se presentan esos datos. Este patron debe extenderse despues a `REGALOS`, `ALBUM`, `ALBUM_COMPARTIDO` y `RSVP`.

## Contenido Real por Tarjeta

La fase `S01-P07` refina el motor `realContent` para que `DETALLES` no dependa de un solo bloque global.

`realContent.items` guarda configuracion independiente para:

- `ceremony`;
- `reception`.

Cada item puede controlar:

- visibilidad;
- etiqueta;
- foto/video;
- direccion;
- mapa/boton;
- fondo;
- posicion de media.

`REGALOS`, `ALBUM` y `ALBUM_COMPARTIDO` quedan conectados al motor para ajustes globales de acomodo y tarjetas.

`RSVP` queda fuera de esta capa por decision de producto: la confirmacion debe conservar su comportamiento funcional y solo exponerse a cambios de fondo, portada/titulo y contenido rapido.
