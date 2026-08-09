# PHASE E.2 — Runtime Cut Plan

E.2 será una fase grande, no una sucesión de hotfixes.

## Bloque 1 — Public Renderer definitivo

Actualmente `public_invitation()` contiene fallback:

```python
if not document:
    return legacy_ver_invitacion(...)
```

E.2 lo sustituirá por una respuesta independiente del legacy:

```text
documento publicado existe
→ UniversalRenderer

no existe
→ página "Invitación aún no publicada" / 404 controlado
```

Después se elimina `/invitacion-legacy/`.

## Bloque 2 — Editor legacy

Eliminar ruta `/legacy/` y el enlace Legacy del Builder.

Eliminar todas las APIs que solo utiliza `editor_invitacion.html`.

## Bloque 3 — Helpers legacy

Eliminar del `views.py` las familias que queden sin consumidores:

```text
construir/sincronizar SeccionInvitacion
serialización editor antiguo
normalización configuración legacy
aplicar configuración publicada legacy
componentes CRUD legacy
assets legacy
editor visual legacy
```

No se borran helpers de negocio que utilice el dashboard fuera del editor.

## Bloque 4 — Dashboard

Eliminar panel `Secciones de invitación`.

El tab Diseño se convierte en un punto de entrada al Builder:

```text
Abrir Builder
Vista pública
estado publicación
```

Los datos operativos del evento continúan en sus tabs correspondientes.

## Bloque 5 — Duplicados

Eliminar:

```text
static/js/builder_v3/
builder_engine/
```

La única fuente queda:

```text
DIRTEC_STUDIO_BUILD/builder/
```

y su único build:

```text
static/invitaciones/builder/
```

## Bloque 6 — Admin

En E.2 se pueden ocultar del admin:

```text
SeccionInvitacion
MediaSeccionInvitacion
ComponenteInvitacion
```

sin borrar sus tablas.

Así nadie crea datos nuevos legacy mientras esperamos Database Cleanup.

## Bloque 7 — Tests

Eliminar/reescribir tests que validan explícitamente el editor antiguo.

Mantener y ampliar:

```text
Builder Django
Assets
Public Renderer
RSVP
Permissions
Dashboard
```
