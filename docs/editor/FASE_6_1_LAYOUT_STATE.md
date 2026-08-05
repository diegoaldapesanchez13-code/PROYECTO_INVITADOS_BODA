# FASE 6.1 - Layout State Persistente del Diseno Rapido

## Objetivo

Evitar que las tarjetas de seccion del Diseno Rapido cambien de tamano al refrescar el editor o al guardar/publicar el borrador.

La fase introduce un estado de layout persistente por seccion dentro de `section.config`, sin modificar la Vista Real ni la arquitectura publica de la invitacion.

## Arquitectura

Cada seccion del editor conserva ahora un bloque de estado visual dentro de su configuracion:

- `sectionHeight`
- `layoutAutoHeight`
- `layoutWidth`
- `layoutScale`
- `layoutExpanded`
- `layoutCollapsed`
- `layoutPaddingX`
- `layoutPaddingY`
- `layoutMarginBottom`
- `layoutMinHeight`
- `layoutMaxHeight`
- `layoutAspectRatio`

El render del Diseno Rapido usa `applyPreviewSectionLayout(article, cfg, fullImage)` para aplicar esos valores. Esto reemplaza la logica anterior que forzaba `min-height: 0` y `aspect-ratio: 2 / 3` en modo imagen completa.

Django conserva esos valores en `normalizar_configuracion_editor`, por lo que sobreviven a refrescos, guardado de borrador y publicacion.

## Archivos modificados

- `invitaciones/static/invitaciones/js/editor_invitacion.js`
- `invitaciones/templates/invitaciones/editor_invitacion.html`
- `invitaciones/static/invitaciones/css/editor_invitacion.css`
- `invitaciones/views.py`
- `CHANGELOG.md`
- `VERSIONING.md`
- `ARCHITECTURE.md`
- `docs/editor/FASE_6_1_LAYOUT_STATE.md`

## Riesgos

- Riesgo bajo sobre Vista Real: esta fase solo modifica el canvas interno del Diseno Rapido.
- Riesgo bajo sobre APIs: no se agregan ni modifican URLs.
- Riesgo medio visual: reglas antiguas con `!important` para imagen completa podian imponerse al estado nuevo; se resolvio aplicando el layout persistente desde JavaScript con prioridad explicita.

## Rollback

Revertir los cambios de esta fase en:

- `editor_invitacion.js`
- `editor_invitacion.html`
- `editor_invitacion.css`
- `views.py`

No hay migraciones ni cambios de base de datos asociados a esta fase.

## Validacion

Ejecutar:

```powershell
node --check invitaciones\static\invitaciones\js\editor_invitacion.js
py manage.py check
```

Pruebas manuales recomendadas:

1. Abrir el editor visual.
2. Seleccionar una seccion del Diseno Rapido.
3. Cambiar alto, ancho, escala, padding o margen.
4. Guardar borrador.
5. Refrescar el navegador.
6. Confirmar que la tarjeta mantiene tamano y estado.
7. Probar una seccion con imagen completa.
8. Confirmar que la Vista Real sigue intacta.

## Commit recomendado

`v5.3: persist quick design section layout state`