# Matriz KEEP / MIGRATE / DELETE

## KEEP — dominio permanente

Estas piezas no son legacy visual:

| Pieza | Razón |
|---|---|
| `EventoBoda` | Dominio del evento |
| `Grupoinvitacion` | Invitación individual, pases y RSVP |
| `Invitado` | Personas del grupo |
| `DisenoInvitacion` | Source of truth del Documento Builder |
| `VersionDisenoInvitacion` | Historial/publicaciones |
| `AssetInvitacion` | Biblioteca persistente |
| `PersonaCeremonia` | Datos de negocio/contenido |
| regalos/itinerario/mapas | Datos del evento |
| permisos por empresa | Seguridad |
| auditoría | Trazabilidad |

`EventoBoda` puede seguir teniendo campos históricos de contenido mientras
definimos bindings en una fase posterior. No se deben borrar por limpiar el editor.

---

## MIGRATE — conservar temporalmente

### `PlantillaInvitacion`

No conviene borrarla todavía.

Puede evolucionar de:

```text
configuración legacy
```

a:

```text
Documento Builder template
```

Se migra en una fase específica de Templates.

### `SeccionInvitacion`

Ya no debe controlar el diseño, pero puede contener media/datos históricos.

Acción:

```text
E.2 → dejar de crear/consultar en runtime
G   → migrar/exportar y eliminar tabla
```

### `MediaSeccionInvitacion`

Depende directamente de `SeccionInvitacion`.

Mismo tratamiento: datos congelados hasta Database Cleanup.

### `ComponenteInvitacion`

El nuevo Builder ya tiene nodes en el Documento V3.

Acción:

```text
E.2 → eliminar API/runtime
G   → eliminar modelo/tabla
```

### Campos legacy de `DisenoInvitacion`

```text
configuracion_borrador
configuracion_publicada
```

No se usarán en runtime después de E.2, pero no se borran hasta la migración
de base de datos.

---

## DELETE EN E.2 — runtime visual antiguo

### Templates

```text
invitaciones/templates/invitaciones/editor_invitacion.html
invitaciones/templates/invitaciones/ver_invitacion.html
```

### JavaScript

```text
invitaciones/static/invitaciones/js/editor_invitacion.js
invitaciones/static/invitaciones/js/invitacion.js
```

### CSS

```text
invitaciones/static/invitaciones/css/editor_invitacion.css
invitaciones/static/invitaciones/css/invitacion.css
```

### Fuente duplicada

```text
invitaciones/static/invitaciones/js/builder_v3/
```

Tiene 132 archivos y ya no debe coexistir con:

```text
DIRTEC_STUDIO_BUILD/builder/
```

### Engine experimental

```text
builder_engine/build/build_static.py
```

Se elimina. El build oficial es el del workspace `DIRTEC_STUDIO_BUILD`.

---

## DELETE EN E.2 — rutas legacy

```text
/dashboard/editor-invitacion/<id>/legacy/
/dashboard/editor-invitacion/<id>/guardar/
/dashboard/editor-invitacion/<id>/publicar/
/dashboard/editor-invitacion/<id>/plantilla/aplicar/
/dashboard/editor-invitacion/<id>/versiones/restaurar/
/dashboard/editor-invitacion/<id>/contenido/guardar/
/dashboard/editor-invitacion/<id>/contenido/item/
/dashboard/editor-invitacion/<id>/invitados/grupo/
/dashboard/editor-invitacion/<id>/invitados/persona/
/dashboard/editor-invitacion/<id>/invitados/importar/
/dashboard/editor-invitacion/<id>/assets/subir/
/dashboard/editor-invitacion/<id>/assets/asignar/
/dashboard/editor-invitacion/<id>/assets/eliminar/
/dashboard/editor-invitacion/<id>/componentes/
/dashboard/editor-invitacion/<id>/componentes/<id>/
/invitacion-legacy/<uuid>/
```

La administración de invitados seguirá existiendo desde el dashboard normal;
lo que desaparece son endpoints creados exclusivamente para el editor viejo.

---

## DELETE EN E.2 — dashboard legacy

Retirar:

```text
invitaciones/templates/invitaciones/dashboard/partials/_secciones_invitacion.html
```

y:

```text
accion = editar_seccion_invitacion
secciones_editor
posiciones_fondo_seccion
```

El dashboard conservará el acceso al Builder y a la invitación pública.
