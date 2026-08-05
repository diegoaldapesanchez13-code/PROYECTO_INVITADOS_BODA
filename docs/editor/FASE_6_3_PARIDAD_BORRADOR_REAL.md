# FASE 6.3 - Paridad entre Borrador, Vista Rapida y Vista Real

## Objetivo

Corregir diferencias entre lo que se edita en el editor y lo que aparece al publicar.

La prioridad de esta fase es que el usuario pueda confiar en que:

- la Vista Rapida representa mejor el contenido real,
- la Vista Real del borrador usa el mismo contenido que se esta editando,
- Publicar no tome una configuracion vacia o reconstruida por accidente.

## Cambios principales

### Publicacion protegida

El endpoint de publicar ahora evita publicar un payload vacio o sin secciones.

Si el navegador manda `{}` o un payload incompleto, Django usa `configuracion_borrador` como fuente segura.

### Sincronizacion de contenido antes de guardar/publicar

Antes de guardar o publicar el diseno, el editor guarda automaticamente el formulario de contenido rapido.

Esto reduce el riesgo de publicar una version vieja de:

- ceremonia,
- recepcion,
- mapas,
- textos de RSVP,
- album compartido,
- datos generales del evento.

### Vista Rapida mas cercana a Vista Real

Se ajusto el render interno de:

- Detalles,
- Regalos / datos bancarios,
- Album,
- Album compartido,
- RSVP.

La Vista Rapida ahora usa clases y jerarquias mas parecidas a los partials publicos:

- `event-detail-grid`,
- `event-place-card`,
- `gift-grid`,
- `gift-box`,
- `album-grid`,
- `shared-album-content`,
- `invitation-summary`,
- `summary-grid`,
- `guest-box`.

## No incluido

- No se reemplaza la Vista Rapida por un iframe de Vista Real.
- No se cambia la URL publica.
- No se modifican RSVP, invitados, QR, mesas ni APIs operativas.
- No se cambia el modelo de datos.

## Validacion

- `node --check invitaciones\static\invitaciones\js\editor_invitacion.js`
- `py manage.py check`
