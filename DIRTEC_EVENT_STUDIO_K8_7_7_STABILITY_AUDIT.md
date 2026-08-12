# DIRTEC Event Studio — Auditoría integral de estabilidad y seguridad

**Baseline auditado:** cadena acumulada hasta K.8.7.7.1  
**Objetivo:** decidir si el sistema está listo para checkpoint Git estable antes de capacidades/paquetes/plantillas.  
**Builder:** tratado como módulo congelado; se revisa únicamente su frontera de autorización/integración.

## 1. Conclusión ejecutiva

La arquitectura funcional actual es coherente y mucho más limpia que la etapa legacy: Empresa, Planner, Cliente y Proveedor ya tienen responsabilidades diferenciadas; `ServicioEvento` funciona como centro operativo; Tareas, Agenda, Documentos, Pagos y Colaboración están separados por significado; Cliente→Empresa y Empresa→Proveedor están financieramente separados; y el sistema de invitados tiene UUID/RSVP individual.

**Sin embargo, no recomiendo crear todavía el commit/tag final de “estable”.** Hay brechas de autorización por URL directa que deben cerrarse primero. No son fallos visibles en navegación normal porque los dashboards esconden correctamente las herramientas; son problemas de backend: ciertos endpoints usan “evento visible” cuando deberían exigir una acción concreta.

Recomiendo una última fase pequeña de hardening (**K.8.7.8 — Pre-commit Authorization & Stability Hardening**), luego ejecutar el gate completo y recién entonces crear commit/tag.

## 2. Flujo de entrada y autenticación

### Flujo actual
`/login/` → `LoginCentralView` → `/redirigir/` → rol/tenant:

- DIRTEC operativo → `/dirtec/dashboard/`
- ADMIN_EMPRESA / VENTAS → dashboard Empresa
- WEDDING_PLANNER → dashboard Planner
- CLIENTE → Portal Cliente
- PROVEEDOR → Portal Proveedor

### Positivo
- Autenticación soporta username, email o teléfono.
- Username/email/teléfono se validan como identidades únicas en el flujo moderno.
- Django admin está restringido por `Actions.DJANGO_ADMIN`; roles de empresa no obtienen acceso al admin solo por `is_staff`.
- CSRF middleware está activo.
- Secure cookies se activan cuando `DEBUG=False`.
- Tenant resolver rechaza cuentas no-DIRTEC asociadas simultáneamente a múltiples empresas activas, evitando ambigüedad de tenant.

### Pendiente de producción
- No hay rate limiting de login.
- No hay MFA/2FA para DIRTEC/superadministrador.
- Password reset usa backend de consola por defecto si no se configura email real.

## 3. Multiempresa y roles

### Positivo
- `TenantContext` centraliza empresa y roles.
- `validar_slug_tenant()` evita que una empresa cambie el slug en URL para entrar a otra.
- Planner se limita por `evento.wedding_planner == user`.
- Proveedor se vincula a un `Proveedor` con usuario y sus `ServicioEvento`.
- Cliente tiene relación explícita con evento y sincronización a `ParticipanteEvento`.
- Empresa y Planner ya no operan CRUD duplicado de servicios desde sus dashboards V3.

### Riesgo detectado
`eventos_visibles_usuario()` mezcla distintos significados de visibilidad: Admin/Planner, Cliente y Proveedor pueden recibir el mismo Evento por motivos diferentes. Es correcto para selectores generales, pero **no debe utilizarse como autorización para una operación interna**.

## 4. Hallazgos bloqueantes antes del commit estable

### CRÍTICO A — Builder usa visibilidad general, no permiso Builder
`invitaciones/builder/views.py::_evento_visible()` usa `eventos_visibles_usuario(request.user)`.

Consecuencia: un Cliente o Proveedor relacionado con el evento puede intentar abrir directamente:

`/dashboard/editor-invitacion/<evento_id>/`

Aunque el portal no muestre el enlace, el backend no exige `Actions.EVENT_BUILDER`.

También `_puede_ver_borrador()` en `builder/public_views.py` usa la misma visibilidad para `?preview=1`, por lo que una identidad externa relacionada podría acceder al borrador si conoce el UUID.

**Corrección requerida:** Builder y preview de borrador deben exigir `usuario_puede_evento(..., Actions.EVENT_BUILDER)` (DIRTEC/Admin/Planner por ahora). Más adelante el entitlement `BUILDER_CLIENTE` podrá ampliar esta frontera sin tocar el motor Builder.

### CRÍTICO B — Endpoints internos operativos accesibles por “evento visible”
Encontrados:

- `/dashboard/mesas/`
- `/dashboard/mesas/guardar-posiciones/`
- `/api/dashboard/metricas/`
- `/dashboard/calendario/`
- `/api/calendario/eventos/`
- `/exportar-excel/`
- `/exportar-resumen/`
- `/dashboard/marcar-envio/<grupo>/`
- `/dashboard/marcar-recordatorio/<grupo>/`

Varios consumen `obtener_evento_dashboard()` o `eventos_visibles_usuario()` sin exigir `EVENT_OPERATIONS`, `EVENT_TABLES` o `EVENT_GUESTS`.

Impacto potencial por URL directa:

- Proveedor puede leer calendario interno con tareas/pagos.
- Cliente/Proveedor pueden llegar a Mesas, nombres de invitados y asignaciones.
- `exportar_resumen` contiene costos/egresos que nunca deben llegar a Cliente/Proveedor.
- estado de envío/recordatorio puede modificarse sin permiso específico.

**Corrección requerida:** autorización de acción en servidor, no solo ocultar enlaces.

### CRÍTICO C — Portal Cliente usa queryset demasiado amplio
`eventos_para_cliente(user)` devuelve actualmente `eventos_visibles_usuario(user)`.

Un Proveedor relacionado con un evento puede intentar entrar directamente a `/cliente/dashboard/?evento=<id>`. Con K.8.7.6 el portal contiene datos de invitados, UUID de invitaciones y enlaces de compartir.

Las escrituras de invitados sí están protegidas por `_es_cliente()`, pero la lectura del portal debe estar igualmente protegida.

**Corrección requerida:** Portal Cliente debe construir su queryset únicamente con relación Cliente (`EventoBoda.clientes` / `ParticipanteEvento.CLIENTE`). No usar visibilidad genérica.

### ALTO D — Rutas legacy de `ExpedienteServicio` siguen activas
Aunque los dashboards V3 ya no las muestran, `colaboracion/urls.py` todavía publica endpoints legacy:

- cliente crear solicitud legacy
- mensajes de ExpedienteServicio
- asignación proveedor legacy
- cotización legacy
- propuesta legacy
- confirmación legacy

Esto permite volver a escribir en un dominio que declaramos retirado de la fuente de verdad y puede generar datos ocultos/inconsistentes.

**Corrección requerida antes del checkpoint:** retirar estas rutas de URL. Mantener modelos/tablas temporalmente para no hacer una migración destructiva en el mismo checkpoint.

### ALTO E — Herramientas destructivas de colaboración no generan auditoría de negocio
K.8.7.7 permite a Planner:

- eliminar mensaje
- vaciar historial
- eliminar referencia
- archivar tema

Los permisos están bien restringidos, pero estas acciones deben dejar `RegistroAuditoria` con usuario, empresa, evento, servicio/canal y cantidad de registros eliminados.

Además el borrado físico de archivos se realiza dentro de la transacción de BD. Si el storage se borra y la transacción de base se revierte después, podría restaurarse una fila apuntando a un archivo inexistente.

**Corrección recomendada:** registrar auditoría y mover eliminación física a `transaction.on_commit()`.

### ALTO F — Métodos GET que modifican estado
`marcar_envio_invitacion` y `marcar_recordatorio` modifican BD mediante vistas sin `@require_POST`.

**Corrección requerida:** POST + CSRF + `Actions.EVENT_GUESTS`.

## 5. Pruebas y definición de “estable”

### Positivo
Los gates de fase han ejercitado progresivamente:

- Event Dashboard V3
- Operational Clarity / Agenda
- Planner V3
- Company V3
- Client Portal V3
- pagos Cliente→Empresa
- Provider Portal V3
- Guests/Sharing
- Collaboration UX

Python del proyecto auditado compila estáticamente sin errores.

### Deuda importante
El repositorio conserva `invitaciones/tests.py` con pruebas históricas del editor antiguo y rutas ya retiradas (`/guardar/`, `/publicar/`, etc.). Los verificadores recientes ejecutan suites focalizadas y no toda la colección histórica.

**Antes del tag estable debe existir un gate integral:**

1. `manage.py check`
2. `manage.py makemigrations --check --dry-run`
3. comprobar migraciones aplicadas
4. `manage.py test` completo, o depurar/retirar formalmente tests legacy que ya prueban un producto eliminado
5. tests Node del Builder congelado
6. smoke manual por rol

Un repositorio marcado estable no debería contener pruebas descubiertas automáticamente que fallen por contratos obsoletos.

## 6. Finanzas

### Arquitectura correcta
- Cliente→Empresa/Planner: `PagoClienteEvento`.
- Empresa→Proveedor: `GastoEvento` → `PagoEvento`.
- Proveedor no recibe `PagoClienteEvento`.
- Cliente no recibe costo proveedor/margen/cotización interna.

### Recomendaciones futuras
- conciliación con `ContratoEvento` (total cobrado vs recibido)
- prevención opcional de duplicados por referencia
- estados de cobranza global del evento
- comprobantes protegidos por descarga autorizada

## 7. Invitados y RSVP

### Positivo
- `Grupoinvitacion` mantiene UUID por invitación.
- `Invitado` es fuente individual del RSVP.
- Cliente puede gestionar únicamente invitados de sus eventos en endpoints K.8.7.6.
- capacidad contratada se valida.
- no se permite borrar personas con RSVP/mesa.
- RSVP público solo puede cambiar invitados pertenecientes al UUID recibido.

### Riesgo operativo futuro
El UUID funciona como bearer token: cualquiera con el enlace puede responder RSVP. Es un diseño válido para invitaciones, pero conviene:

- rate limiting de RSVP
- registro de IP/fecha de modificaciones si se requiere trazabilidad
- opción de cerrar RSVP después de una fecha

## 8. Mensajería y colaboración

### Positivo
- separación real de canales:
  - Cliente↔Planner
  - Planner↔Proveedor
  - Interno
- autorización backend por canal.
- Cliente no recibe cotizaciones de proveedor en contexto.
- documentos tienen `visible_cliente` y `visible_proveedor` separados.
- referencias protegen adjuntos frente a borrado accidental.
- limpieza conserva Decisiones/Cotizaciones/Propuestas/Aprobaciones estructuradas.

### Antes del checkpoint
Añadir auditoría a borrados y limpieza de archivos post-commit de BD.

## 9. Documentos y almacenamiento

### Positivo
- validación de extensión y tamaño.
- límites distintos para imagen/video/audio/documento.
- visibilidad Cliente y Proveedor separada a nivel de aplicación.

### BLOQUEANTE antes de producción (no necesariamente antes del checkpoint Git)
Los `FileField` generan URLs bajo `/media/`. La privacidad actual controla **quién recibe el enlace**, pero si el servidor web expone `/media/` públicamente, conocer una URL puede saltarse `visible_cliente/visible_proveedor`.

Antes de producción, contratos, comprobantes y documentos privados deben usar:

- almacenamiento privado, o
- endpoint de descarga autenticado/autorizado, o
- URLs firmadas temporales.

También la validación actual es principalmente extensión+tamaño; para producción conviene validación real de MIME/contenido para imágenes/documentos.

## 10. Configuración de seguridad y despliegue

### Estado de desarrollo actual
- SQLite
- `DEBUG` default True
- `ALLOWED_HOSTS` default `*`
- fallback `SECRET_KEY` insegura
- `SAAS_REQUIRE_SUBSCRIPTION` default False
- email console backend por defecto

Esto está bien para desarrollo local pero **no debe convertirse directamente en configuración productiva**.

### Antes de producción
- PostgreSQL
- `DJANGO_DEBUG=False`
- SECRET_KEY obligatoria desde entorno
- ALLOWED_HOSTS explícitos
- CSRF_TRUSTED_ORIGINS explícitos
- `SAAS_REQUIRE_SUBSCRIPTION=True` después de materializar suscripciones
- `SECURE_PROXY_SSL_HEADER` si existe reverse proxy
- HSTS cuando HTTPS esté comprobado
- SMTP real
- backups automáticos de PostgreSQL y media privada
- WSGI/ASGI productivo; nunca `runserver`
- rate limiting login/password reset/RSVP
- MFA para DIRTEC recomendado

## 11. Legacy y deuda técnica

### Ya migrado funcionalmente
- Servicio → `ServicioEvento`
- Chat → Workspace ServicioEvento
- Tarea → `TareaEvento`
- Agenda → `ActividadItinerario`
- Confirmación de cita → `ParticipanteActividad`
- Documentos → `DocumentoEvento`
- Finanzas → `GastoEvento/PagoEvento` + `PagoClienteEvento`

### Todavía presente
- `ExpedienteServicio` y su antiguo stack
- `ServicioEvento.estado` legacy junto con `estado_comercial` y `estado_operativo`
- campos financieros legacy (`costo_total`, `precio_cliente`, `ajuste_cliente`)
- modelos especializados antiguos de catering/decoración/entretenimiento

### Recomendación
No eliminar tablas físicamente en el mismo commit estable. Primero:
1. desactivar rutas legacy;
2. crear checkpoint estable;
3. en una fase posterior ejecutar grep + migraciones de datos + eliminación de esquema de forma reversible.

## 12. Builder

### Estado
El código funcional de `DIRTEC_STUDIO_BUILD/builder` y `invitaciones/static/invitaciones/builder` está sincronizado; la diferencia observada corresponde a README/manifest/demo/tests del workspace Builder.

### Regla arquitectónica confirmada
Builder permanece congelado e independiente de plantillas.

### Única corrección permitida antes del checkpoint
Corregir **la frontera de autorización que lo rodea**, no el motor Builder:
- editor/API assets/document/publish → `EVENT_BUILDER`
- preview de borrador → `EVENT_BUILDER`

## 13. Documentación del repositorio

`README.md` y `ARCHITECTURE.md` están significativamente desactualizados: todavía describen el proyecto como `PROYECTO_INVITADOS_BODA`, SQLite como arquitectura general y una fase antigua del editor.

Antes del commit estable recomiendo actualizar documentos raíz para describir:
- DIRTEC Event Studio
- roles
- tenant model
- Event Dashboard V3
- Service Workspace
- pagos
- invitados
- Builder congelado
- futura separación Templates / Builder

## 14. Git y estrategia de checkpoint

El repositorio auditado está sobre:

`builder-v3-clean-rebuild` → `origin/builder-v3-clean-rebuild`

Ese nombre de rama ya no describe correctamente el alcance actual. Recomiendo crear una rama estable integrada después del hardening, por ejemplo:

`k8-event-platform-stable`

Commit sugerido después de corregir y pasar gates:

`stable(k8.7.8): harden authorization and freeze event platform baseline`

Tag sugerido:

`k8.7.8-event-platform-stable-v1`

No subir `db.sqlite3`, `media/`, `venv/`, `.env` ni ZIPs de fase.

## 15. Decisión final

### ¿Arquitectura funcional lista para checkpoint?
**Sí.**

### ¿Haría el commit estable exactamente con el código actual?
**No todavía.**

### Correcciones mínimas previas
1. Builder + preview con `EVENT_BUILDER`.
2. Cerrar endpoints internos (mesas/calendario/métricas/exports/envío) por acción.
3. Portal Cliente solo para identidades Cliente.
4. Desactivar rutas legacy `ExpedienteServicio`.
5. Hacer envío/recordatorio POST-only.
6. Auditar borrados de colaboración y ejecutar file-delete en `on_commit`.
7. Gate de pruebas integral y depuración de tests legacy.
8. Actualizar README/ARCHITECTURE para el baseline estable.

Después de esas correcciones, sí recomiendo crear commit + tag y cerrar K8 como baseline estable antes de paquetes/capacidades/plantillas.
