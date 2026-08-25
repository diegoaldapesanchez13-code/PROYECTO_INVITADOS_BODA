# K9 Security Matrix

Estado: diagnostico K9.0.

## Hallazgos principales

1. `SaasSubscriptionMiddleware.PATHS_OPERATIVOS` no incluye `/colaboracion/`.
2. `SaasSubscriptionMiddleware.PATHS_OPERATIVOS` no incluye `/presupuesto/`.
3. `secure_files.py` tiene fallbacks de proveedor menos estrictos que `_es_proveedor_servicio`.
4. `LoginCentralView` no valida `next` por usuario nuevo antes de redirigir.
5. CRUD legacy usa eliminaciones fisicas en entidades operativas; debe clasificarse por permisos y auditoria.

No corregir en K9.0. Documentar para K9.1.

## Autorizacion actual derivada del repositorio

| Area | Estado actual | Riesgo K9 |
| --- | --- | --- |
| Empresa A vs B | `tenant_context` y validaciones de modelos cubren varios casos. | Mantener tests en catalogo/contrato. |
| Planner | `usuario_puede_evento` exige evento asignado. | Propuesta y contrato deben usar la misma regla. |
| Cliente | Acceso por `evento.clientes` y `ParticipanteEvento` en pagos. | Vista contrato publico debe filtrar costos. |
| Proveedor | Acceso por `ServicioEvento.proveedor.usuario`. | Servicios sin proveedor no deben exponerse. |
| Workspace | Canales visibles por servicio y rol. | Mantener canales; no crear chats paralelos. |
| Django admin | `admin.site.has_permission` usa `Actions.DJANGO_ADMIN`. | Conservar reservado a DIRTEC. |
| IDs directos | Tests K8 cubren varios 403/404. | K9.5 cubre contrato/propuesta; mantener catalogo y materializacion. |
| Archivos privados | `secure_files.py` centraliza descargas. | Unificar fallbacks proveedor. |
| Media comercial catalogo | K9.2 guarda `ServicioCatalogo.imagen_principal` y `ServicioCatalogoArchivo.archivo` en `PRIVATE_MEDIA_ROOT`. | No servir `PRIVATE_MEDIA_ROOT` por Caddy/Nginx; acceso solo por vistas Django autorizadas. |

## SaaS middleware

Actual:

```text
PATHS_OPERATIVOS = /dirtec/, /empresa/, /cliente/, /proveedor/, /dashboard/, /portal/, /api/, /exportar-
```

Rutas independientes observadas:

- `/colaboracion/` montada desde `config/urls.py`.
- `/presupuesto/` montada desde `config/urls.py`.

Riesgo:

- una empresa suspendida podria seguir accediendo a workspace o pagos si la vista autentica y autoriza pero no pasa por estado SaaS.

Cambio recomendado K9.1:

- agregar `/colaboracion/` y `/presupuesto/` a rutas operativas;
- auditar futuras apps `catalogo/` y contrato cuando se monten;
- tests GET y POST con empresa suspendida.

K9.5: `/eventos/` se agrega a `PATHS_OPERATIVOS` para proteger las rutas de contrato bajo estado SaaS del tenant.

## Secure files

K9.2: la media comercial privada del catalogo no se sirve por `MEDIA_URL`.

- `ServicioCatalogo.imagen_principal` y `ServicioCatalogoArchivo.archivo` usan storage privado bajo `PRIVATE_MEDIA_ROOT`.
- Las plantillas de catalogo no usan `.url` de los `FileField`.
- Las descargas pasan por vistas autorizadas de `catalogo/` y `FileResponse`.
- En desarrollo, `DEBUG=True` solo publica `MEDIA_ROOT`; los archivos de catalogo quedan fuera de esa raiz.
- En produccion, `PRIVATE_MEDIA_ROOT` no debe montarse como ruta publica del servidor web.

Helpers centrales:

- `_es_cliente_evento(user, evento)`;
- `_es_proveedor_servicio(user, servicio)`.

Fallbacks a revisar:

- `documento_evento`: si `visible_proveedor`, permite `documento.proveedor.usuario_id == user.id` aunque no pase por `_es_proveedor_servicio`.
- `pago_operativo_comprobante`: permite proveedor del gasto por `usuario_id` directo.

Riesgo:

- proveedor inactivo, proveedor de otra relacion, o documento no vinculado a `ServicioEvento` podria ser mas permisivo que la politica central.

Cambio recomendado:

- crear helper comun para proveedor por servicio y proveedor por documento/gasto con validacion de empresa, activo y rol proveedor;
- documentar si un proveedor puede ver comprobantes operativos; por defecto, cliente nunca;
- tests con proveedor inactivo, proveedor de otro tenant, proveedor no asignado al servicio y documento visible.

## Matriz de visibilidad K9

Leyenda: `SI`, `NO`, `Segun permiso`.

| Dato | DIRTEC | Empresa | Planner | Cliente | Proveedor |
| --- | --- | --- | --- | --- | --- |
| Contrato total | SI | SI | SI si evento asignado | SI si cliente del evento | NO |
| Nombre paquete | SI | SI | SI | SI | Segun servicio asignado |
| Adultos/ninos contratados | SI | SI | SI | SI | NO por defecto |
| Servicios incluidos | SI | SI | SI | SI | Solo si le corresponde |
| Adicionales | SI | SI | SI | SI | Solo si le corresponde |
| Cortesias | SI | SI | SI | SI | Solo si le corresponde |
| Descuentos visibles | SI | SI | SI | SI | NO |
| Costo proveedor | SI | SI | Segun permiso financiero | NO | Solo su cotizacion/costo si aplica |
| Costo operativo | SI | SI | Segun permiso financiero | NO | NO |
| Margen | SI | SI | Segun permiso financiero | NO | NO |
| Notas privadas | SI | SI | Segun permiso | NO | NO |
| Documentos comerciales permitidos | SI | SI | SI | SI si marcado visible | Segun visibilidad/proveedor |
| Documentos internos | SI | SI | SI segun permiso | NO | NO |
| Workspace cliente-planner | SI | SI/Planner | SI | SI | NO |
| Workspace planner-proveedor | SI | SI/Planner | SI | NO | SI si proveedor asignado |
| Workspace interno | SI | SI/Planner | SI | NO | NO |
| Pagos cliente | SI | SI | SI segun operacion | SI propios/evento | NO |
| Pagos proveedor/operativos | SI | SI | SI segun finanzas | NO | Solo si se decide exponer comprobante propio |

K9.5 implementado: la vista `eventos_contrato_detail` usa tenant por slug, filtra `ContratoEvento` por `evento__empresa`, exige `Actions.EVENT_VIEW` y entrega al cliente una proyeccion publica sin metadata interna. El proveedor no ve el contrato completo en K9.5.

K9.6 implementado: materializar contrato crea `ServicioEvento` con proveedor `null` y `prestacion_tipo=POR_DEFINIR`; un proveedor no asignado no obtiene acceso al workspace del servicio. Cliente conserva solo el canal cliente-planner permitido por las reglas existentes del workspace.

K9.7 implementado:

- `resumen_financiero_interno` entrega costos, pagos operativos, margen y flujo solo a DIRTEC, Empresa y planner autorizado.
- El planner requiere autorizacion central `usuario_puede_evento(..., Actions.EVENT_VIEW)`, asignacion activa al evento y `ParticipanteEvento.puede_ver_finanzas=True`.
- `resumen_financiero_cliente` entrega solo total contratado, pagos cliente, saldo, sobrepago y advertencias publicas.
- Cliente no recibe costos, margen, pagos operativos ni detalle de pagos a proveedor.
- Proveedor no recibe total contractual ni pagos cliente desde la capa financiera K9.7.
- El dashboard financiero filtra por `empresa_slug` validado y `evento__empresa`, sin aceptar tenant desde POST.

## Login/logout

Bug documentado:

```text
Usuario A -> ruta privada -> logout -> login Usuario B -> se conserva next/contexto anterior -> 403
```

Puntos revisados:

- `LoginCentralView` hereda `LoginView`.
- `LOGIN_REDIRECT_URL = /redirigir/`.
- `LogoutView(next_page='login')`.
- Static JS usa `localStorage` para tabs/paneles, no se observo `sessionStorage` de tenant/evento en busqueda general.
- `tenant_context` decide empresa por membresias/request, no por localStorage.

Politica K9:

- logout siempre lleva a login neutral;
- login normal lleva a dashboard por rol;
- `next` solo se honra si el usuario autenticado puede acceder a ese recurso;
- limpiar cualquier contexto de tenant/evento en sesion si se agrega en el futuro.

Tests recomendados:

- A accede a ruta privada y hace logout, B login sin `next` termina en dashboard de B.
- B intenta `?next=/cliente/...` de A y cae en dashboard o 403 controlado sin filtrado.
- usuario con rol correcto y objeto autorizado si puede usar `next`.

## CRUD operativo y permisos

Entidades auditadas:

- `ServicioEvento`: crear/editar/eliminar en dashboard legacy.
- `TareaEvento`: crear/editar/eliminar; estado incluye cancelada.
- `ActividadItinerario`: citas/agenda, estados incluyen cancelada.
- `DocumentoEvento`: crear/editar/eliminar con archivo.
- `GastoEvento`: crear/editar/eliminar.
- `PagoEvento`: crear/editar/eliminar.
- Workspace: crear tema/mensaje, eliminar adjunto/mensaje/referencia, limpiar historial, archivar tema.

Politica propuesta:

| Entidad | Crear | Editar | Eliminar | Cancelar | Archivar |
| --- | --- | --- | --- | --- | --- |
| ServicioEvento | Empresa/Planner | Empresa/Planner | Solo pre-contrato/error | SI si contratado | SI si historico |
| TareaEvento | Empresa/Planner | Responsable/Empresa/Planner | Solo error | SI | SI |
| ActividadItinerario | Empresa/Planner | Participantes segun accion | Solo error | SI | SI si completada/historica |
| DocumentoEvento | Empresa/Planner/proveedor segun canal | Cargador/operador | Cargador/operador con auditoria | No aplica | SI si historico |
| GastoEvento | Empresa/Planner financiero | Empresa/Planner financiero | Solo sin pagos | SI/anular | SI |
| PagoEvento | Empresa/Planner financiero | Empresa/Planner financiero | Solo error y con auditoria | SI/anular | SI |

## Navegacion contextual

Auditar botones visibles:

- Regresar;
- Volver;
- Dashboard;
- Atras.

Riesgo:

- `history.back()` puede devolver al usuario a contexto de otro rol, otro evento o pagina post-logout.

Politica:

- Cliente -> `/cliente/dashboard/` o portal con `evento` autorizado.
- Proveedor -> `/proveedor/dashboard/`.
- Planner -> `/empresa/<slug>/planner/dashboard/` o evento asignado. La ruta `/wedding-planner/dashboard/` queda sólo como alias legacy temporal.
- Empresa -> `/empresa/<slug>/dashboard/`.
- DIRTEC -> `/dirtec/dashboard/`.
- Workspace -> dashboard/portal por rol y servicio autorizado.

## Password reset

Actual:

- `PasswordResetView`;
- `PasswordResetDoneView`;
- `PasswordResetConfirmView`;
- `PasswordResetCompleteView`;
- templates en `core/templates/core/`.

Auditoria requerida para produccion:

- SMTP configurado sin secretos en repo;
- dominio HTTPS correcto;
- email no revela si usuario existe;
- mensajes neutros;
- rate limiting si se considera necesario;
- pruebas de render y envio con backend de desarrollo/test.

## Landing, terminologia y branding

Landing actual: legacy visible centrada en invitaciones/boda.

Objetivo visible futuro:

- `DIRTEC Event Studio`;
- gestion profesional de eventos e invitaciones digitales;
- editor desde contexto de evento.

Terminologia:

- cambios visibles primero;
- no renombrar modelos/campos/URLs sin estrategia.

Branding:

- usar configuracion controlada por empresa;
- no CSS arbitrario;
- logotipo, portada/hero, encabezados y colores controlados.
