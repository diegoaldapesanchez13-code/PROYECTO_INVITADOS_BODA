# Arquitectura objetivo después de E.2

```text
DIRTEC_EVENT_STUDIO/
│
├── DIRTEC_STUDIO_BUILD/
│   └── builder/                   # única fuente visual
│
├── invitaciones/
│   ├── builder/
│   │   ├── views.py               # editor/API
│   │   ├── public_views.py        # publicación/RSVP
│   │   ├── services.py
│   │   └── assets.py
│   │
│   ├── templates/invitaciones/
│   │   └── builder/
│   │       ├── editor.html
│   │       └── public_invitation.html
│   │
│   └── static/invitaciones/
│       └── builder/               # generado
│
└── manage.py
```

## Flujo editor

```text
Dashboard
→ Builder
→ documento_builder_borrador
→ Publicar
→ documento_builder_publicado
```

## Flujo invitado

```text
UUID
→ Grupoinvitacion
→ Evento
→ Documento publicado
→ UniversalRenderer
→ RSVP API
```

## No existirán en runtime

```text
editor_invitacion.*
ver_invitacion.*
builder_v3 duplicate
builder_engine experimental
SeccionInvitacion UI
ComponenteInvitacion API
legacy fallback
```

Las tablas históricas solo permanecerán esperando PHASE G.
