# Hallazgos de dependencias

## Rutas

La URL pública oficial ya es:

```text
/invitacion/<uuid>/
→ builder_public_views.public_invitation
```

La URL del editor oficial ya es:

```text
/dashboard/editor-invitacion/<id>/
→ builder_views.editor
```

Esto confirma que el legacy ya no es el flujo principal.

## Legacy editor APIs

La auditoría de nombres de rutas encontró que los endpoints del editor antiguo
solo aparecen en:

```text
invitaciones/urls.py
invitaciones/views.py
```

No hay templates ni JS nuevos consumiéndolos.

Por ello se pueden eliminar juntos.

## Public legacy

`views.ver_invitacion` todavía tiene dos dependencias reales:

1. `/invitacion-legacy/<uuid>/`
2. fallback de `builder/public_views.py` cuando no existe Documento publicado.

Al eliminar ambas en E.2, `ver_invitacion` queda sin función runtime.

## Secciones legacy

`SeccionInvitacion` todavía es utilizado por:

```text
dashboard POST editar_seccion_invitacion
dashboard context secciones_editor
_secciones_invitacion.html
admin
legacy views
legacy tests
```

Por eso el panel del dashboard debe retirarse antes de Database Cleanup.

## AssetInvitacion

Debe permanecer.

Aunque conserva un FK nullable a `SeccionInvitacion`, los nuevos assets Builder
se crean con:

```text
seccion = NULL
```

En Database Cleanup retiraremos ese FK.

## VersionDisenoInvitacion

Debe permanecer.

Las nuevas publicaciones Builder ya crean versiones con:

```text
_format = DIRTEC_BUILDER_V3
document = Documento V3
```

Las versiones históricas legacy pueden conservarse sin ser cargadas por el runtime nuevo.
