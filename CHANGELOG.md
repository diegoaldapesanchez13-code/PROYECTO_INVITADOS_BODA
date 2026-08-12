# CHANGELOG

## 2026-08-01 - S01-P14 Component Resize Handles

### Agregado

- Los componentes seleccionados en la Vista Rapida ahora muestran handles visuales en las esquinas.
- Los handles permiten redimensionar componentes `TEXTO`, `IMAGEN` y `BOTON` sin usar solamente sliders.
- La Vista Real en modo `Editar` ahora permite redimensionar el componente seleccionado desde sus esquinas.
- El resize actualiza:
  - `x`,
  - `y`,
  - `width`,
  - `height`.
- Al soltar el handle, el componente se guarda mediante la API del Motor de Componentes.
- El inspector se sincroniza mientras se redimensiona en la Vista Rapida.

### Compatibilidad

- El drag anterior de componentes se conserva.
- Los componentes bloqueados no muestran handles de resize.
- La Vista Real conserva su modo `Probar` para botones, enlaces, mapas y formularios.
- No se modifica la estructura publica de RSVP ni contenido funcional.

### Pendiente

- Handle de rotacion.
- Snap y guias inteligentes.
- Constraints responsive.
- Mejor experiencia tactil para mobile.

### Validacion

- `node --check invitaciones/static/invitaciones/js/editor_invitacion.js`
- `py manage.py check`
- carga de templates principales con `get_template`
- render del editor con `django.test.Client`: 200
- render publico con `django.test.Client`: 200

## 2026-08-01 - S01-P13 Component Tree Drag and Drop

### Agregado

- El arbol de componentes ahora permite reordenar con drag and drop:
  - Capas de una misma seccion.
  - Componentes persistentes de una misma seccion.
- Al arrastrar capas, se actualiza su orden visual dentro del borrador del editor.
- Al arrastrar componentes persistentes, se recalcula y guarda su `zIndex` mediante la API del Motor de Componentes.
- Se agregaron estados visuales para:
  - fila arrastrada,
  - destino valido,
  - filas reordenables.

### Compatibilidad

- No se altera el reordenamiento de secciones existente.
- No se permite mezclar capas y componentes en un mismo drop.
- No se permite mover componentes entre secciones desde esta primera version.
- Las acciones anteriores del arbol siguen funcionando: mostrar, bloquear, enviar atras/frente y eliminar.

### Validacion

- `node --check invitaciones/static/invitaciones/js/editor_invitacion.js`
- `py manage.py check`
- carga de templates principales con `get_template`
- render del editor con `django.test.Client`: 200
- render publico con `django.test.Client`: 200

## 2026-08-01 - S01-P12 Component Tree Actions

### Agregado

- El arbol de componentes ahora permite acciones directas sin depender del canvas:
  - Mostrar / ocultar.
  - Bloquear / desbloquear.
  - Enviar atras.
  - Traer al frente.
  - Eliminar.
- Las acciones estan disponibles segun el tipo de nodo:
  - Secciones: mostrar / ocultar.
  - Capas: mostrar / ocultar, bloquear / desbloquear, reordenar z-index y eliminar capas personalizadas.
  - Componentes persistentes: mostrar / ocultar, bloquear / desbloquear, ajustar z-index y eliminar.
- Los componentes persistentes guardan estos cambios mediante la API del Motor de Componentes.
- Las acciones del arbol sincronizan la seleccion con el Inspector Universal y la vista rapida.

### Validacion

- `node --check invitaciones/static/invitaciones/js/editor_invitacion.js`
- `py manage.py check`
- carga de templates principales con `get_template`
- render del editor con `django.test.Client`: 200
- render publico con `django.test.Client`: 200

## 2026-08-01 - S01-P11 Component Tree Base

### Agregado

- Se agrego un panel `Arbol` en el panel izquierdo del editor.
- El arbol muestra:
  - Pagina / Invitacion
  - Secciones
  - Capas base de cada seccion
  - Contenido real
  - Componentes persistentes
- Desde el arbol se puede seleccionar:
  - una seccion,
  - una capa,
  - contenido real,
  - un componente.
- La seleccion del arbol sincroniza el Inspector Universal y el canvas.
- El arbol muestra estados de oculto y seleccion activa.

### Validacion

- `node --check invitaciones/static/invitaciones/js/editor_invitacion.js`
- `py manage.py check`
- carga de templates principales con `get_template`
- render del editor con `django.test.Client`: 200
- render publico con `django.test.Client`: 200

## 2026-08-01 - S01-P10 Inspector Universal Base

### Agregado

- Se agrego un bloque `Inspector` unico dentro del panel de propiedades.
- El inspector detecta y resume el elemento seleccionado:
  - Seccion
  - Capa activa
  - Contenido real
  - Componente
- Se agregaron controles comunes reutilizables:
  - X
  - Y
  - ancho
  - alto / escala
  - rotacion
  - opacidad
  - z-index
  - bloqueo
  - ocultar
- El inspector reutiliza la logica existente de secciones, capas, contenido real y componentes sin eliminar los paneles actuales.
- Se agrego accion directa para eliminar el componente seleccionado desde el inspector.
- El inspector puede cambiar rapidamente entre paneles: Diseno, Contenido y Assets.

### Estado

- Primera base funcional del Inspector Universal.
- Los paneles especializados siguen existiendo como respaldo mientras se migra progresivamente a un unico inspector.

### Validacion

- `node --check invitaciones/static/invitaciones/js/editor_invitacion.js`
- `py manage.py check`
- carga de templates principales con `get_template`
- render del editor con `django.test.Client`: 200
- render publico con `django.test.Client`: 200

## 2026-08-01 - S01-P09 Paridad Visual de Fotos y Mapas

### Agregado

- La Vista Rapida de `DETALLES` ahora renderiza las fotos reales/asignadas de Ceremonia y Recepcion.
- Se agregaron destinos de asset para imagen de ubicacion:
  - `MAPA_CEREMONIA`
  - `MAPA_RECEPCION`
- Cada tarjeta de Detalles puede usar una imagen o video como mapa visual mediante `realContent.items.*.mapAsset`.
- La Vista Real usa `mapAsset` antes que el embed/iframe de Google Maps cuando existe.

### Corregido

- Las secciones `REGALOS`, `ALBUM` y `ALBUM_COMPARTIDO` ahora normalizan sus estilos de `realContent` con su propio tipo de seccion, no como `DETALLES`.
- Los botones de asset especificos de Detalles se ocultan/deshabilitan fuera de la seccion Detalles para reducir confusion.

### Pendiente estructural

- Construir el Inspector Universal.
- Convertir Assets en administrador completo de recursos.
- Crear Component Tree.
- Agregar eventos, animaciones, constraints responsive y Mobile Companion.

## 2026-08-01 - S01-P08 Paridad de Detalles y Assets Reales

### Agregado

- Se agregaron destinos de asset visibles para `Foto ceremonia` y `Foto recepcion`.
- La asignacion de assets de ceremonia/recepcion ahora actualiza el borrador y tambien los campos reales del evento.
- Ceremonia y Recepcion ahora pueden configurar por separado:
  - orden de tarjeta,
  - texto del boton,
  - posicion de foto/video,
  - fondo de tarjeta,
  - visibilidad de foto, direccion y mapa,
  - modo de acceso: boton y mapa, solo boton, solo mapa u oculto.
- RSVP se mantiene fuera del contenido real editable para conservar estable el formulario de confirmacion.
- La vista rapida y la vista real comparten los mismos campos `realContent.items`.

### Validacion

- `node --check invitaciones/static/invitaciones/js/editor_invitacion.js`
- `py manage.py check`
- carga de templates principales con `get_template`
- render del editor con `django.test.Client`: 200
- render publico con `django.test.Client`: 200

## 2026-08-01 - S01-P06 Contenido Real Editable

### Agregado

- Se agrego `section.config.realContent` como capa de configuracion para datos dinamicos.
- Se agrego un panel de "Contenido real" en el editor visual.
- Se habilito la primera implementacion en la seccion `DETALLES`.
- Ceremonia y Recepcion ahora pueden ajustar etiqueta, visibilidad, layout, ancho, escala, separacion, tarjetas, fotos, direccion y mapas sin perder datos reales de Django.
- La Vista Rapida usa la misma configuracion `realContent` que la Vista Real.
- Django normaliza `realContent` al guardar/publicar para evitar configuraciones invalidas.

### Validacion

- `node --check invitaciones/static/invitaciones/js/editor_invitacion.js`
- `py manage.py check`
- Carga de templates principales con `get_template`.

## 2026-08-01 - S01-P07 Contenido Real por Tarjeta

### Agregado

- Ceremonia y Recepcion ahora tienen controles separados dentro de `realContent.items`.
- Cada tarjeta puede configurar etiqueta, visibilidad, foto/video, direccion, mapa, fondo y posicion de media.
- Regalos, Album y Album compartido se conectaron al motor visual `realContent`.
- RSVP quedo excluido del panel de contenido real para conservar el formulario estable.

### Validacion

- `node --check invitaciones/static/invitaciones/js/editor_invitacion.js`
- `py manage.py check`
- carga de templates principales con `get_template`
- render publico y render del editor con `django.test.Client`

## 2026-07-29 - v5.2-live-preview

Checkpoint estable antes del Universal Editing Engine.

### Agregado

- Se creo el modelo `ComponenteInvitacion`.
- Se agrego la migracion `invitaciones/migrations/0028_componenteinvitacion.py`.
- Se registro `ComponenteInvitacion` en el admin de Django.
- Se agrego API JSON para listar, crear, actualizar y eliminar componentes.
- Se agrego render publico de componentes con `_componentes_invitacion.html`.
- Se refactorizaron secciones hacia partials reutilizables usando `_section_base.html`.
- Se agrego Live Preview Editor sobre la invitacion publica real mediante iframe same-origin.
- Se agregaron modos de interaccion `Editar` y `Probar`.
- Se permitio seleccionar y mover componentes `ComponenteInvitacion` sobre la invitacion real.
- Se agrego sincronizacion visual y persistencia de posicion al soltar componentes.
- Se conservaron las capas libres, assets, fondos, imagenes completas y editor rapido existente.
- Se documentaron arquitectura y versionado.

### Conservado

- Invitaciones personales y familiares.
- Confirmacion individual de invitados familiares.
- Acompanantes nominales para invitaciones personales.
- Control adulto/nino definido por empresa o planner.
- Importacion CSV/XLSX de invitados.
- Mesas, QR, regalos, mapas, menus, albumes, dress code y RSVP.
- Editor visual anterior con capas libres y enfoque responsive.

### Validacion

- `node --check invitaciones/static/invitaciones/js/editor_invitacion.js`
- `py manage.py check`
- `py manage.py makemigrations --check --dry-run`

## Siguiente version prevista - v5.3-universal-editing-engine

La siguiente version no debe agregar funcionalidades pequenas. Debe implementar la base arquitectonica del Universal Editing Engine:

- registro universal de elementos editables,
- seleccion sobre cualquier elemento visible,
- transformaciones generales,
- panel de propiedades universal,
- biblioteca de componentes drag and drop,
- historial undo/redo,
- responsive engine por dispositivo.

DIRTEC — CONTROL DE CAMBIOS DEL RENDERER
Rama: v5.3-editor-consolidation
Fase: S01 — Estabilización del renderer
Fecha de inicio: 2026-07-31

OBJETIVO GENERAL
Corregir los errores visuales heredados de v5.2-live-preview sin reescribir el editor:
- imágenes encimadas;
- portadas que no respetan su posición;
- duplicación visual;
- orden incorrecto entre portada, capas y componentes;
- diferencias entre Vista Real e invitación publicada.

REGLA DE TRABAJO
Haremos un cambio pequeño por vez.
Después de cada cambio:
1. Guardar archivos.
2. Ejecutar: py manage.py check
3. Levantar: py manage.py runserver 8001
4. Probar Vista Real.
5. Probar invitación publicada.
6. Probar en escritorio y móvil.
7. Registrar el resultado aquí.
8. Solo entonces hacer commit.

==================================================
CAMBIO S01-P01
Nombre:
Normalización inicial del orden del renderer

Archivo:
invitaciones/templates/invitaciones/partials/_section_base.html

Problema detectado:
El archivo actual renderiza:
1. fondo;
2. capas personalizadas;
3. componentes;
4. imagen completa o encabezado.

Esto permite que la imagen completa aparezca después de capas y componentes y altere el apilamiento visual.

Cambio:
El nuevo orden será:
1. fondo;
2. imagen completa o encabezado;
3. capas personalizadas;
4. componentes.

Alcance:
- No cambia modelos.
- No cambia base de datos.
- No crea migraciones.
- No cambia JavaScript.
- No elimina funciones.
- No separa todavía portada e imagen de título.
- Solo corrige el orden HTML inicial.

Estado:
[ ] Pendiente
[ ] Aplicado
[ ] Probado en Vista Real
[ ] Probado en invitación publicada
[ ] Probado en escritorio
[ ] Probado en móvil
[ ] Aprobado
[ ] Revertido

Resultados observados:
__________________________________________________
__________________________________________________
__________________________________________________

Errores restantes:
__________________________________________________
__________________________________________________
__________________________________________________

Commit sugerido cuando sea aprobado:
git add invitaciones/templates/invitaciones/partials/_section_base.html
git commit -m "Normaliza el orden inicial del renderer de secciones"

IMPORTANTE
No hacer todavía cambios en:
- models.py
- migrations
- JavaScript del editor
- coordinate_engine.py
- componentes
- capas personalizadas
- CSS general

Primero debemos comprobar qué errores desaparecen únicamente corrigiendo el orden del HTML

DIRTEC — REGISTRO S01-P03

Cambio:
Corrección de componentes LAYER con position: fixed.

Archivo:
invitaciones/static/invitaciones/css/invitacion.css

Regla anterior:
position: fixed;

Regla de corrección:
position: absolute;

Estado:
[ ] Respaldo creado
[ ] Bloque agregado al final del CSS
[ ] py manage.py check correcto
[ ] Probado en Vista Real
[ ] Probado en publicación
[ ] Probado con scroll
[ ] Probado en escritorio
[ ] Probado en móvil
[ ] Aprobado
[ ] Revertido

Resultados:
__________________________________________________
__________________________________________________
__________________________________________________

Errores restantes:
__________________________________________________
__________________________________________________
__________________________________________________

Commit sugerido después de aprobar:
git add invitaciones/templates/invitaciones/partials/_section_base.html
git commit -m "Normaliza el orden inicial del renderer de secciones"
git add invitaciones/static/invitaciones/css/invitacion.css
git commit -m "Contiene los componentes visuales dentro de su sección"

DIRTEC — INSTRUCCIONES S01-P05
ELIMINAR LA DUPLICACIÓN DESDE renderPreview()

ARCHIVO:
invitaciones/static/invitaciones/js/editor_invitacion.js

--------------------------------------------------
1. CREAR RESPALDO
--------------------------------------------------

Copy-Item `
"invitaciones\static\invitaciones\js\editor_invitacion.js" `
"invitaciones\static\invitaciones\js\editor_invitacion.js.s01-p05.bak"


--------------------------------------------------
2. LOCALIZAR ESTE BLOQUE
--------------------------------------------------

Dentro de function renderPreview(), buscar:

const background = cfg.backgroundAsset || {};
const titleAsset = cfg.titleAsset || {};
const fullImage = isFullImageSection(section, cfg);
const keepRealContent = sectionKeepsRealContent(section, cfg);


--------------------------------------------------
3. REEMPLAZARLO POR EL BLOQUE A
--------------------------------------------------

Copiar el BLOQUE A desde:

13_REEMPLAZOS_JS_S01_P05.txt


--------------------------------------------------
4. LOCALIZAR EL RENDER DEL VIDEO DE FONDO
--------------------------------------------------

Buscar:

if (cfg.showBackgroundLayer !== false && background.url && background.isVideo) {


--------------------------------------------------
5. REEMPLAZAR SOLO ESA LÍNEA POR EL BLOQUE B
--------------------------------------------------

No reemplazar el contenido interno del if.
Únicamente cambiar la condición.


--------------------------------------------------
6. LOCALIZAR EL BLOQUE DE bgLayer
--------------------------------------------------

Buscar este bloque:

const bgLayer = document.createElement('div');
bgLayer.className = 'preview-section-bg';
bgLayer.classList.toggle('is-hidden', cfg.showBackgroundLayer === false);
if (cfg.showBackgroundLayer !== false) setBackgroundStyles(bgLayer, cfg, background);
attachBackgroundDrag(article, bgLayer, section, cfg);
article.appendChild(bgLayer);


--------------------------------------------------
7. REEMPLAZARLO POR EL BLOQUE C
--------------------------------------------------


--------------------------------------------------
8. LOCALIZAR EL BLOQUE DE titleLayer
--------------------------------------------------

Buscar desde:

const titleLayer = document.createElement('div');

hasta:

article.appendChild(titleLayer);


--------------------------------------------------
9. REEMPLAZAR TODO ESE BLOQUE POR EL BLOQUE D
--------------------------------------------------

IMPORTANTE:
Reemplazar solamente el bloque de titleLayer.
No borrar decorLayer ni textLayer.


--------------------------------------------------
10. VALIDACIÓN
--------------------------------------------------

py manage.py check
py manage.py runserver 8001

En el navegador:

Ctrl + F5


--------------------------------------------------
11. PRUEBAS
--------------------------------------------------

A. Sección normal con imagen de título

[ ] La imagen aparece pequeña como encabezado.
[ ] El texto del título continúa visible.
[ ] El fondo continúa visible.

B. Sección con diseño "imagen completa"

[ ] Solo aparece una imagen.
[ ] La imagen ocupa toda la sección de Vista Rápida.
[ ] No aparece una miniatura duplicada.
[ ] Vista Real continúa funcionando.
[ ] La invitación publicada continúa funcionando.

C. Cambio de modo

[ ] Cambiar normal → imagen completa.
[ ] Cambiar imagen completa → normal.
[ ] Cambiar varias veces sin duplicación.
[ ] Recargar la página y volver a probar.

D. Recurso disponible solo como fondo

[ ] La imagen de fondo aparece como imagen completa.
[ ] No queda una sección vacía.


--------------------------------------------------
12. NO MODIFICAR CSS TODAVÍA
--------------------------------------------------

No eliminar aún los tres bloques duplicados de:

.preview-section.is-full-image

Primero validar que JavaScript produzca una sola fuente visual.


--------------------------------------------------
13. REVERTIR
--------------------------------------------------

Copy-Item `
"invitaciones\static\invitaciones\js\editor_invitacion.js.s01-p05.bak" `
"invitaciones\static\invitaciones\js\editor_invitacion.js" `
-Force


--------------------------------------------------
14. NO HACER COMMIT HASTA APROBAR

DIRTEC — FASE 6.1
PRIMERA MODULARIZACIÓN SEGURA

Esta fase separa solamente cinco utilidades generales. No cambia
la Vista Rápida, Vista Real, componentes, capas, assets ni guardado.

ARCHIVOS:
- editor_utils_FASE_6_1.js.txt
- editor_invitacion_COMPLETO_FASE_6_1.js.txt


1. CREAR EL NUEVO ARCHIVO

Ruta:

invitaciones/static/invitaciones/js/editor_utils.js

Copiar TODO editor_utils_FASE_6_1.js.txt.


2. RESPALDAR EL ARCHIVO PRINCIPAL

Copy-Item `
"invitaciones\static\invitaciones\js\editor_invitacion.js" `
"invitaciones\static\invitaciones\js\editor_invitacion.js.fase-6-1.bak"


3. REEMPLAZAR EL ARCHIVO PRINCIPAL

Reemplazar TODO:

invitaciones/static/invitaciones/js/editor_invitacion.js

con TODO el contenido de:

editor_invitacion_COMPLETO_FASE_6_1.js.txt


4. MODIFICAR EL TEMPLATE

En editor_invitacion.html, editor_utils.js debe cargarse justo antes
de editor_invitacion.js:

<script src="{% static 'invitaciones/js/editor_utils.js' %}"></script>
<script src="{% static 'invitaciones/js/editor_invitacion.js' %}"></script>


5. VALIDAR

py manage.py check
py manage.py runserver 8001

Recargar con Ctrl + F5.

Comprobar:
[ ] abre el editor;
[ ] carga la Vista Rápida;
[ ] carga la Vista Real;
[ ] no se duplica la imagen completa;
[ ] se mueve una capa;
[ ] se crea y guarda un componente;
[ ] no hay errores rojos en la consola.


6. COMMIT

git status
git add invitaciones/static/invitaciones/js/editor_utils.js
git add invitaciones/static/invitaciones/js/editor_invitacion.js
git add invitaciones/templates/invitaciones/editor_invitacion.html
git commit -m "Inicia modularizacion segura del editor"
git push origin v5.3-editor-consolidation
==================================================
CAMBIO S01-P02
Nombre:
Layout State persistente para tarjetas del Diseno Rapido

Objetivo:
Evitar que las tarjetas de seccion del Diseno Rapido cambien de tamano al refrescar el editor.

Archivos:
- invitaciones/static/invitaciones/js/editor_invitacion.js
- invitaciones/templates/invitaciones/editor_invitacion.html
- invitaciones/static/invitaciones/css/editor_invitacion.css
- invitaciones/views.py
- docs/editor/FASE_6_1_LAYOUT_STATE.md

Cambios:
- Se agrego estado persistente de layout por seccion.
- Se conserva ancho, alto, escala, padding, margen y estado colapsado.
- Se reemplazo el recalculo rigido de imagen completa en Diseno Rapido por `applyPreviewSectionLayout`.
- Se agregaron controles minimos de layout al inspector.
- Se normalizaron los nuevos campos en Django para que sobrevivan a guardado y refresco.

Riesgo:
Bajo. No modifica Vista Real, RSVP, invitados, QR, mesas, APIs ni URLs.

Validacion:
- `node --check invitaciones\static\invitaciones\js\editor_invitacion.js` paso sin errores.
- `py manage.py check` paso sin errores.

==================================================
CAMBIO S01-P05
Nombre:
Componentes editables basicos

Objetivo:
Hacer que los componentes Texto, Imagen y Boton puedan seleccionarse, editarse, moverse con mas estabilidad y eliminarse desde el editor.

Archivos:
- invitaciones/templates/invitaciones/editor_invitacion.html
- invitaciones/static/invitaciones/js/editor_invitacion.js
- invitaciones/static/invitaciones/css/editor_invitacion.css
- docs/editor/FASE_6_4_COMPONENTES_EDITABLES.md

Cambios:
- Se agrego panel de componente seleccionado.
- Se agregaron controles de posicion, tamano, rotacion, opacidad, z-index, bloquear, ocultar y eliminar.
- Se agregaron propiedades especificas para Texto, Imagen y Boton.
- Se corrigio el calculo de drag en Vista Rapida usando `getBoundingClientRect`.
- Se agrego eliminacion de componentes desde el editor.
- Se mejoro la seleccion visual del componente activo.

Riesgo:
Medio-bajo. Toca el motor de componentes del editor, pero no modifica la Vista Real publica, RSVP operativo, invitados, QR, mesas ni URLs.

Validacion:
- `node --check invitaciones\static\invitaciones\js\editor_invitacion.js` paso sin errores.
- `py manage.py check` paso sin errores.

==================================================
CAMBIO S01-P04
Nombre:
Paridad entre Borrador, Vista Rapida y Vista Real

Objetivo:
Corregir diferencias entre lo que se edita en el editor, lo que se ve en Vista Rapida y lo que se publica.

Archivos:
- invitaciones/static/invitaciones/js/editor_invitacion.js
- invitaciones/static/invitaciones/css/editor_invitacion.css
- invitaciones/views.py
- docs/editor/FASE_6_3_PARIDAD_BORRADOR_REAL.md

Cambios:
- Publicar queda protegido contra payloads vacios o sin secciones.
- Guardar y publicar sincronizan primero el formulario de contenido rapido.
- Detalles deja de renderizar mapas complejos dentro de Vista Rapida y usa tarjetas tipo Vista Real.
- Regalos/datos bancarios, Album, Album compartido y RSVP usan clases y estructuras mas cercanas a los partials publicos.
- El alto publico de seccion usa el mismo rango base del editor.

Riesgo:
Medio-bajo. Toca el flujo de publicar y el render de Vista Rapida, pero no modifica URLs, RSVP operativo, invitados, QR, mesas ni APIs publicas.

Validacion:
- `node --check invitaciones\static\invitaciones\js\editor_invitacion.js` paso sin errores.
- `py manage.py check` paso sin errores.

==================================================
CAMBIO S01-P03
Nombre:
Resize Handles para tarjetas del Diseno Rapido

Objetivo:
Permitir ajustar visualmente el ancho y alto de las tarjetas seleccionadas en el Diseno Rapido sin depender solamente de sliders.

Archivos:
- invitaciones/static/invitaciones/js/editor_invitacion.js
- invitaciones/static/invitaciones/css/editor_invitacion.css
- docs/editor/FASE_6_2_RESIZE_HANDLES.md

Cambios:
- Se agregaron handles de resize a la tarjeta seleccionada.
- El handle derecho modifica `layoutWidth`.
- El handle inferior modifica `sectionHeight`.
- El handle de esquina modifica ancho y alto al mismo tiempo.
- Los cambios actualizan el inspector y quedan dentro del `section.config` persistente.
- Se activo el render de `builderComponents` dentro de la Vista Rapida para mantener coherencia con el motor de componentes.

Riesgo:
Bajo. No modifica Vista Real, RSVP, invitados, QR, mesas, APIs ni URLs.

Validacion:
- `node --check invitaciones\static\invitaciones\js\editor_invitacion.js` paso sin errores.
- `py manage.py check` paso sin errores.

DIRTEC — S02-P01
INTEGRIDAD DE HERRAMIENTAS, PANELES Y CONTROLES

OBJETIVO

Evitar que las herramientas del editor desaparezcan por depender
exclusivamente de la inicialización JavaScript.

PROBLEMA ENCONTRADO

El CSS contiene esta regla:

.properties-panel > .property-group {
    display: none;
}

Los grupos solo vuelven a mostrarse cuando reciben data-editor-group.

El template actual no incluía esos atributos de forma estática.
JavaScript los agregaba después de iniciar.

Consecuencia:
Si JavaScript falla antes de installSimplifiedEditorUi(), tarda en cargar
o se interrumpe por otro error, todos los grupos del panel derecho quedan
ocultos y parecen haber desaparecido.

CAMBIO

1. El template define desde Django:
   - data-editor-mode="simple"
   - data-editor-panel="design"

2. Cada grupo declara su función:
   - design
   - content
   - assets

3. El Inspector Universal queda marcado como persistente.

4. JavaScript agrega ensureEditorUiIntegrity() como respaldo para:
   - templates antiguos;
   - grupos sin clasificar;
   - atributos faltantes;
   - diagnóstico en consola.

5. CSS mantiene visible el Inspector Universal al cambiar de panel.

ARCHIVOS ENTREGADOS

- editor_invitacion_COMPLETO_S02_P01.html.txt
- editor_invitacion_COMPLETO_S02_P01.js.txt
- editor_invitacion_COMPLETO_S02_P01.css.txt
- S02_P01_CONTROL_Y_PRUEBAS.txt

APLICACIÓN

Crear respaldos:

Copy-Item `
"invitaciones\templates\invitaciones\editor_invitacion.html" `
"invitaciones\templates\invitaciones\editor_invitacion.html.s02-p01.bak"

Copy-Item `
"invitaciones\static\invitaciones\js\editor_invitacion.js" `
"invitaciones\static\invitaciones\js\editor_invitacion.js.s02-p01.bak"

Copy-Item `
"invitaciones\static\invitaciones\css\editor_invitacion.css" `
"invitaciones\static\invitaciones\css\editor_invitacion.css.s02-p01.bak"

Después reemplazar completamente los tres archivos.

Actualizar versión de caché en editor_invitacion.html a:

?v=20260801-01

VALIDACIÓN

1. Ejecutar:

node --check invitaciones\static\invitaciones\js\editor_invitacion.js
py manage.py check
py manage.py runserver 8001

2. Recargar con Ctrl + F5.

3. Probar:

[ ] Aparece el selector Fácil / Avanzado.
[ ] Aparecen Diseño / Contenido / Archivos.
[ ] Diseño muestra Tema y Sección seleccionada.
[ ] Contenido muestra Contenido rápido.
[ ] Archivos muestra subida y biblioteca de assets.
[ ] El Inspector Universal permanece visible.
[ ] Cambiar entre paneles no deja el lateral vacío.
[ ] Las herramientas siguen visibles después de refrescar.
[ ] No hay errores rojos en consola.
[ ] Vista Rápida sigue funcionando.
[ ] Vista Real sigue funcionando.
[ ] Guardar borrador sigue funcionando.

NO HACER COMMIT HASTA CONFIRMAR LAS PRUEBAS.

COMMIT SUGERIDO

git add invitaciones/templates/invitaciones/editor_invitacion.html
git add invitaciones/static/invitaciones/js/editor_invitacion.js
git add invitaciones/static/invitaciones/css/editor_invitacion.css
git commit -m "Estabiliza paneles y herramientas del editor"
git push origin v5.3-editor-consolidation

ROLLBACK

Restaurar los tres archivos .s02-p01.bak.

DIRTEC — S02-P02
BARRA DE HERRAMIENTAS ESTÁTICA Y CONEXIÓN DE ACCIONES

OBJETIVO

Hacer que las herramientas principales existan desde el HTML generado
por Django y no dependan de que JavaScript las cree dinámicamente.

PROBLEMA CORREGIDO

installSimplifiedEditorUi() tenía esta condición:

if (root.querySelector('[data-simple-editor-toolbar]')) return;

Eso impedía conectar listeners cuando la barra existía previamente
en el HTML. Por esa razón no bastaba con hacerla estática.

SOLUCIÓN

- La barra Fácil / Avanzado se renderiza desde el template.
- Diseño / Contenido / Archivos se renderizan desde el template.
- Reparar distribución y Usar imagen completa se renderizan desde el template.
- Texto / Imagen / Botón se renderizan desde el template.
- JavaScript solo crea la barra como fallback.
- JavaScript siempre conecta listeners, exista o no la barra.
- Se verifica automáticamente que estén las diez herramientas esenciales.
- Si falta una, aparece advertencia visual y en consola.

ARCHIVOS

- editor_invitacion_COMPLETO_S02_P02.html.txt
- editor_invitacion_COMPLETO_S02_P02.js.txt
- editor_invitacion_COMPLETO_S02_P02.css.txt

APLICACIÓN

Respaldar primero los archivos S02-P01 actuales.

Reemplazar completamente:

invitaciones/templates/invitaciones/editor_invitacion.html
invitaciones/static/invitaciones/js/editor_invitacion.js
invitaciones/static/invitaciones/css/editor_invitacion.css

Actualizar caché a:

?v=20260801-02

VALIDAR

node --check invitaciones\static\invitaciones\js\editor_invitacion.js
py manage.py check
py manage.py runserver 8001

PRUEBAS

[ ] La barra aparece incluso antes de terminar de cargar JavaScript.
[ ] Fácil y Avanzado cambian correctamente.
[ ] Diseño abre el panel de diseño.
[ ] Contenido abre contenido rápido.
[ ] Archivos abre Assets.
[ ] Reparar distribución ejecuta una acción.
[ ] Usar imagen completa ejecuta una acción.
[ ] Texto crea componente.
[ ] Imagen crea componente.
[ ] Botón crea componente.
[ ] No aparece advertencia naranja.
[ ] En consola no aparece “herramientas faltantes”.
[ ] data-editor-tools-ready queda en true en .editor-shell.
[ ] Refrescar no hace desaparecer herramientas.

NO HACER COMMIT HASTA APROBAR.

COMMIT SUGERIDO

git add invitaciones/templates/invitaciones/editor_invitacion.html
git add invitaciones/static/invitaciones/js/editor_invitacion.js
git add invitaciones/static/invitaciones/css/editor_invitacion.css
git commit -m "Conecta de forma estable la barra de herramientas"
git push origin v5.3-editor-consolidation
## K.8.7.8 — Production Baseline & Security Hardening

- autorización explícita de Builder por `EVENT_BUILDER`;
- portales Cliente/Proveedor endurecidos por relación real;
- calendario, métricas, mesas y exports protegidos por acción;
- marcar envío/recordatorio cambia a POST + CSRF;
- rutas legacy de `ExpedienteServicio` retiradas del URLconf;
- auditoría de limpieza destructiva en Collaboration Workspace;
- borrado físico de adjuntos mediante `transaction.on_commit()`;
- descargas privadas autenticadas `/secure/...`;
- configuración PostgreSQL por entorno;
- configuración segura para reverse proxy HTTPS;
- Waitress/Caddy y scripts de despliegue Windows;
- backup portable SQLite + media e inventario de migración;
- documentación de cutover y baseline actualizada.
