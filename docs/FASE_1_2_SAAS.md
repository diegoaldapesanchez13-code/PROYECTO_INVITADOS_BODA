# Fase 1 y 2 - Analisis SaaS DIRTEC

## Arbol actual relevante

```text
PROYECTO_INVITADOS_BODA-main/
├── aprobaciones/
├── auditoria/
├── catering/
├── config/
├── core/
│   └── services/
├── decoracion/
├── documentos/
├── entretenimiento/
├── invitaciones/
│   ├── migrations/
│   ├── static/
│   └── templates/
├── itinerario/
├── mesas/
├── notificaciones/
├── organizaciones/
├── paquetes/
├── presupuesto/
├── proveedores/
├── suscripciones/
├── tareas/
├── .env.example
├── db.sqlite3
├── manage.py
├── README.md
└── requirements.txt
```

## Aplicaciones actuales

- `invitaciones`: evento principal, invitacion publica, grupos, invitados, RSVP, personalizacion, dashboards.
- `organizaciones`: empresa suscriptora, sedes y membresias de usuarios por empresa.
- `proveedores`: catalogo de proveedores, servicios contratados y personal por evento.
- `catering`: categorias, alimentos, paquetes buffet y seleccion de catering por evento.
- `paquetes`: paquetes comerciales, servicios incluidos y paquetes asignados al evento.
- `decoracion`: elementos de decoracion por evento.
- `entretenimiento`: musica, artistas y canciones del evento.
- `itinerario`: actividades operativas.
- `mesas`: mesas y asignacion de invitados.
- `presupuesto`: categorias de gasto, gastos y pagos del evento.
- `tareas`: pendientes por evento.
- `documentos`: documentos del evento/proveedor/cliente.
- `aprobaciones`: aprobaciones del cliente.
- `notificaciones`: alertas internas.
- `core`: servicios centrales y middleware SaaS.
- `suscripciones`: planes, suscripciones y pagos comerciales DIRTEC.
- `auditoria`: registro de acciones criticas.

## Modelo de usuario

El proyecto usa `django.contrib.auth.models.User`; no existe `AUTH_USER_MODEL` personalizado.

Riesgo: cambiar `AUTH_USER_MODEL` despues de tener migraciones y datos es una migracion delicada. Puede romper llaves foraneas existentes hacia `auth.User`, sesiones, admin, grupos y datos ya capturados.

Estrategia actual: conservar `auth.User` y extender roles con `organizaciones.MembresiaEmpresa`. Si mas adelante se necesita un usuario personalizado, se debe planear una migracion separada con respaldo, scripts de conversion, pruebas en copia de BD y ventana de mantenimiento.

## Modelos actuales principales

- `organizaciones.EmpresaSuscriptora`: empresa SaaS reutilizada como entidad principal.
- `organizaciones.MembresiaEmpresa`: relacion usuario/empresa/rol.
- `organizaciones.SedeEvento`: sedes de una empresa.
- `invitaciones.EventoBoda`: evento generico, ya soporta boda, XV, baby shower, bautizo y otros.
- `invitaciones.Grupoinvitacion`: invitacion personal/familiar.
- `invitaciones.Invitado`: invitado individual dentro de grupo.
- `invitaciones.FotoEvento`, `EnlaceRegalo`, `PersonaCeremonia`, `ItinerarioEvento`, `MenuBoda`.
- `proveedores.Proveedor`, `ServicioEvento`, `PersonalEvento`.
- `paquetes.PaqueteBoda`, `ServicioPaquete`, `PaqueteEvento`.
- `catering.CategoriaAlimento`, `Alimento`, `PaqueteBuffet`, `CateringEvento`.
- `mesas.Mesa`, `AsignacionMesa`.
- `presupuesto.CategoriaGasto`, `GastoEvento`, `PagoEvento`.
- `documentos.DocumentoEvento`.
- `tareas.TareaEvento`.
- `aprobaciones.AprobacionEvento`.
- `notificaciones.Notificacion`.
- `suscripciones.PlanSuscripcion`, `SuscripcionEmpresa`, `PagoSuscripcion`.
- `auditoria.RegistroAuditoria`.

## Funciones existentes de invitaciones

- Invitacion publica por codigo unico: `/invitacion/<uuid>/`.
- Invitacion personal con acompanantes permitidos.
- Invitacion familiar con RSVP por invitado.
- Control de adultos/ninos para buffet.
- Dashboard avanzado por evento.
- Dashboard profesional por rol.
- Dashboard DIRTEC, empresa y wedding planner.
- Portales cliente/proveedor.
- Exportaciones Excel/resumen.
- Calendario operativo.
- Plano visual de mesas.
- Personalizacion visual de invitacion.
- Album, regalos, menus, mapas, dress code y RSVP.

## Modelos reutilizados

- No se crea un modelo nuevo `Empresa`: se reutiliza `EmpresaSuscriptora`.
- No se crea un nuevo `Evento`: se reutiliza `EventoBoda`.
- No se crea un nuevo `Invitado`: se reutiliza `Invitado`.
- No se duplica `PaqueteBoda`, `Proveedor`, `Mesa`, `DocumentoEvento` ni `PagoEvento`.

## Riesgos de migracion detectados

- El proyecto ya tiene migraciones y datos; cambiar el modelo de usuario ahora es riesgoso.
- Hay modelos operativos que dependen de `evento`, no todos tienen `empresa` directa. La empresa debe resolverse indirectamente por `evento.empresa` cuando aplique.
- Existen empresas antiguas sin suscripcion creada. Por eso `SAAS_REQUIRE_SUBSCRIPTION=False` queda como modo de compatibilidad.
- Los textos con codificacion danada existen en algunos archivos historicos; conviene limpiarlos gradualmente.
- SQLite sirve para desarrollo, pero produccion SaaS debe moverse a PostgreSQL.

## Arquitectura final propuesta

- `DIRTEC`: administra empresas, planes, suscripciones, pagos, limites y bloqueos.
- `Empresa`: administra operacion interna, usuarios, planners, clientes, proveedores, paquetes y eventos.
- `Wedding planner`: opera eventos asignados y usa catalogos autorizados.
- `Cliente`: consulta y aprueba informacion permitida.
- `Proveedor`: consulta servicios asignados y sube documentos permitidos.

Separacion:

- Backend filtra por empresa, evento y rol.
- Los dashboards no dependen solo de ocultar botones.
- Los servicios en `core/services/` concentran reglas comunes.
- El middleware `SaasSubscriptionMiddleware` valida acceso operativo.
- Auditoria registra bloqueos y queda lista para acciones criticas.

## Plan de migracion sin perdida de datos

1. Respaldar `db.sqlite3` y carpeta `media/`.
2. Aplicar migraciones nuevas: `python manage.py migrate`.
3. Crear planes base desde Django Admin o dashboard DIRTEC.
4. Crear una `SuscripcionEmpresa` por cada `EmpresaSuscriptora` existente.
5. Validar usuarios y membresias por empresa.
6. Activar `SAAS_REQUIRE_SUBSCRIPTION=True` solo cuando todas las empresas tengan suscripcion.
7. Ejecutar pruebas completas.
8. Antes de produccion, migrar a PostgreSQL con respaldo y validacion de conteos.

## Comandos

```bash
python manage.py makemigrations
python manage.py migrate
python manage.py check
python manage.py test
```

## Fase 2 implementada

- App `suscripciones`.
- App `auditoria`.
- App `core`.
- Modelos de planes, suscripciones y pagos de suscripcion.
- Modelo de auditoria.
- Middleware de validacion SaaS.
- Servicios de permisos, suscripciones, limites de plan y auditoria.
- Pantalla `/suscripcion/estado/`.
- Pruebas de bloqueo, gracia, vencimiento y suscripcion activa.

## Fase 3 base implementada

- Login central en `/login/`.
- Redireccion automatica post-login en `/redirigir/`.
- Recuperacion de contrasena en `/password-reset/`.
- Logout central en `/logout/`.
- Rutas SaaS limpias:
  - `/dirtec/dashboard/`
  - `/empresa/<slug>/dashboard/`
  - `/empresa/<slug>/wedding-planner/dashboard/`
  - `/cliente/dashboard/`
  - `/proveedor/dashboard/`
- Las rutas antiguas `/dashboard/...` y `/portal/...` se conservan por compatibilidad.
- El dashboard por slug valida membresia real en backend, no solo el nombre escrito en la URL.
- El middleware SaaS protege tambien las rutas nuevas.

## Dashboard comercial DIRTEC implementado

- `EmpresaSuscriptora` ahora guarda datos comerciales extra:
  - RFC.
  - Direccion.
  - Logotipo.
  - Colores de marca.
  - Estado comercial: activa, suspendida, bloqueada o inactiva.
- El dashboard DIRTEC administra:
  - Planes de suscripcion.
  - Alta transaccional de empresa, suscripcion, pago inicial y admin principal.
  - Suscripciones por empresa.
  - Bloqueo manual.
  - Periodo de gracia.
  - Reactivacion al registrar pago pagado.
  - Historial reciente de pagos por empresa.
- Las acciones criticas registran auditoria:
  - Creacion de plan.
  - Creacion de empresa SaaS.
  - Actualizacion de suscripcion.
  - Registro de pago.
- Se conserva el admin avanzado de Django solo como herramienta tecnica.

## Limites de plan en dashboard de empresa

- El dashboard de empresa muestra uso del plan:
  - Plan actual.
  - Estado de suscripcion.
  - Eventos activos usados contra limite contratado.
  - Usuarios usados contra limite contratado.
  - Wedding planners usados contra limite contratado.
- Antes de crear un evento se valida `limite_eventos_activos`.
- Antes de crear un wedding planner se valida:
  - `limite_usuarios`.
  - `limite_wedding_planners`.
- Si se excede un limite:
  - No se crea el registro.
  - Se muestra mensaje claro en dashboard.
  - Se registra auditoria con accion `LIMITE_PLAN_EXCEDIDO`.

## Clientes desde dashboard de empresa

- Se agrego la pestaña `Clientes` en el dashboard de empresa.
- El administrador de empresa puede:
  - Crear usuario cliente.
  - Crear membresia `CLIENTE`.
  - Asignar el cliente a un evento activo.
  - Ver clientes registrados de la empresa.
- El alta de cliente valida:
  - `limite_usuarios`.
  - `limite_clientes`.
- La asignacion usa `EventoBoda.clientes`, por lo que el portal del cliente reutiliza el flujo existente sin duplicar modelos.

## Creacion de eventos desde dashboard wedding planner

- El dashboard del wedding planner ahora tiene pestaña `Crear evento`.
- El planner puede crear eventos base dentro de empresas donde tenga membresia `WEDDING_PLANNER`.
- El evento queda autoasignado al planner autenticado.
- Antes de crear se valida `limite_eventos_activos` del plan.
- Si se excede el limite:
  - No se crea el evento.
  - Se muestra aviso en el dashboard del planner.
  - Se registra auditoria con accion `LIMITE_PLAN_EXCEDIDO`.
- Cuando el evento se crea correctamente, se registra auditoria con accion `CREAR_EVENTO_PLANNER`.
