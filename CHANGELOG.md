# CHANGELOG

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