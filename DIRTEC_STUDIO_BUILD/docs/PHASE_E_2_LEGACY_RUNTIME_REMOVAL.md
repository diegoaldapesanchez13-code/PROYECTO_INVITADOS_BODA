# PHASE E.2 — Legacy Runtime Removal

Esta fase corta el runtime visual antiguo sin eliminar todavía tablas históricas.

## Elimina
- editor_invitacion HTML/JS/CSS
- ver_invitacion HTML/JS/CSS
- panel dashboard `_secciones_invitacion`
- rutas/API del editor legacy
- `/invitacion-legacy/<uuid>/`
- `static/js/builder_v3/`
- `builder_engine/`

## Conserva
- modelos/tablas históricas `SeccionInvitacion`, `MediaSeccionInvitacion`, `ComponenteInvitacion`
- campos legacy de `DisenoInvitacion`
- `PlantillaInvitacion`
- todo el dominio Evento/Grupo/Invitado/RSVP
- `AssetInvitacion`
- `VersionDisenoInvitacion`

## Comportamiento público
Si no hay `documento_builder_publicado`, `/invitacion/<uuid>/` responde 404 controlado con `builder/not_published.html`. Nunca vuelve al renderer viejo.

## Nota
Las funciones Python legacy que queden sin ruta se purgarán junto con sus imports durante Source Cleanup, después de demostrar que E.2 no rompe runtime. No tienen consumidores web después de esta fase.
