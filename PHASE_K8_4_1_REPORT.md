# K.8.4.1 — Client Workspace Access + Attachment UX/Security

## Problema corregido
El portal del cliente seguía mostrando colaboración únicamente a través de `ExpedienteServicio` legacy. Por eso un `ServicioEvento` válido podía tener workspace funcional y aun así no aparecer al cliente.

## Solución
- El portal cliente proyecta directamente los `ServicioEvento` del evento.
- Cada servicio expone acceso directo al canal `CLIENTE_PLANNER`.
- El bloque legacy de solicitudes/propuestas se conserva temporalmente para compatibilidad.

## Adjuntos
- Miniaturas reales para imágenes.
- Tarjetas compactas para PDF/otros archivos.
- Vista previa de selección antes de enviar.
- Eliminación individual de archivos seleccionados antes de enviar.
- Eliminación posterior permitida al autor del adjunto o al equipo operativo.
- Un usuario no puede eliminar adjuntos ajenos fuera de su canal visible.
- Adjuntos ya promovidos a referencia quedan protegidos contra eliminación accidental.
- Si un mensaje queda sin texto ni adjuntos después de borrar su único archivo, se elimina el mensaje vacío.

## Privacidad adicional
Las referencias ahora se filtran por los canales visibles del usuario. Cliente no puede ver referencias nacidas de `PLANNER_PROVEEDOR`/`INTERNO`; proveedor no puede ver referencias de `CLIENTE_PLANNER`.

## Migraciones
No requiere migración de base de datos.

## Gates ejecutados
- `manage.py check`: OK
- `makemigrations --check`: sin cambios
- regresión dominio K.8.1.1–K.8.4.1: 38/38 OK
