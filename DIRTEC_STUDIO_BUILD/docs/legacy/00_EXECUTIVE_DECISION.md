# PHASE E.1 — Legacy Audit

## Decisión

El corte funcional ya ocurrió:

```text
Editor oficial  → DIRTEC Studio Builder
Public oficial  → UniversalRenderer
Persistencia    → Documento Builder V3
Assets          → AssetInvitacion + MEDIA_ROOT
RSVP público    → builder/public_views.py
```

Por tanto el editor visual anterior ya no debe seguir condicionando la arquitectura.

## Hallazgo principal

Los endpoints legacy del editor visual:

- guardar diseño;
- publicar legacy;
- plantillas legacy;
- restaurar versión legacy;
- contenido legacy;
- invitados desde editor legacy;
- assets legacy;
- componentes legacy;

no tienen consumidores fuera de sus propias rutas/views.

Esto permite retirarlos como un bloque en E.2.

## Excepción

El dashboard todavía contiene un panel de `SeccionInvitacion` y una acción POST
`editar_seccion_invitacion`.

Este panel sí debe retirarse del runtime antes de declarar muerto el sistema de
secciones.

Las tablas no se eliminan todavía.
