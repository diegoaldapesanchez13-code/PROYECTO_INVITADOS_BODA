# K9 Master Plan

Estado: borrador K9.0, documental, sin cambios de negocio.

## 1. Baseline exacta

- Branch actual: `feature/mobile-ux-operational-polish`.
- Commit base observado: `1cb608fca833df53e4e07d5a19b9a0211867f242`.
- Commit corto: `1cb608f`.
- Descripcion del commit: `fix(builder): preserve inspector focus during live editing`.
- Working tree observado al iniciar K9.0: `M DIRTEC_STUDIO_BUILD/builder/demo_r3_07.js`.
- Interpretacion: hay un cambio local preexistente del Builder. K9.0 no lo modifica ni lo revierte.
- Baseline recomendada para desarrollo K9: crear rama nueva desde el commit base estable, por ejemplo `feature/k9-commercial-core`.
- Restriccion: no mezclar K9 con hotfix productivo ni hacer push/deploy desde K9.0.

## 2. Inventario actual

### Apps y modelos principales

- `organizaciones`: `EmpresaSuscriptora`, `SedeEvento`, `MembresiaEmpresa`.
- `invitaciones`: `EventoBoda`, invitacion/editor, invitados, RSVPs y `DetalleProduccionEvento`.
- `eventos`: `ParticipanteEvento`, `ContratoEvento`.
- `paquetes`: `PaqueteBoda`, `ServicioPaquete`, `PaqueteEvento`.
- `proveedores`: `Proveedor`, `EtiquetaProveedor`, `ServicioCatalogoProveedor`, `ServicioEvento`, `PersonalEvento`.
- `presupuesto`: `CategoriaGasto`, `GastoEvento`, `PagoEvento`, `PagoClienteEvento`.
- `colaboracion`: expediente legacy y workspace K8 sobre `ServicioEvento`.
- `documentos`: `DocumentoEvento`.
- `tareas`: `TareaEvento`.
- `itinerario`: `ActividadItinerario`, `ParticipanteActividad`.
- `aprobaciones`: `AprobacionEvento`.

### Views y URLs

- `config/urls.py` monta `core`, `suscripciones`, `colaboracion/`, `presupuesto/` e `invitaciones`.
- No se observaron `proveedores/urls.py` ni `paquetes/urls.py`; gran parte de la operacion vive dentro de `invitaciones/views.py`.
- `colaboracion/urls.py` expone workspace, mensajes, adjuntos, referencias, decisiones, cotizaciones, propuestas, aprobaciones, tareas, agenda, documentos, gastos y pagos por servicio.
- `presupuesto/urls.py` expone pagos reportados por cliente y revision por equipo.
- `core/urls.py` expone login/logout, redireccion por rol, password reset y descargas seguras.

### Services

- `paquetes/services.py`: snapshot y materializacion de paquetes hacia `ServicioEvento`.
- `colaboracion/services.py`: reglas de canales, mensajes, referencias, decisiones y limpieza.
- `core/services/authorization.py`: permisos por rol y acceso a eventos.
- `core/services/tenant_context.py`: resolucion de tenant.
- `core/services/permisos.py` y `core/services/suscripciones.py`: roles, DIRTEC y estado SaaS.

### Templates

- Login y password reset en `core/templates/core/`.
- Dashboards y portales en `invitaciones/templates/invitaciones/`.
- Workspace en `colaboracion/templates/colaboracion/`.
- Builder en `invitaciones/templates/invitaciones/builder/`.

### Tests existentes relevantes

- `paquetes/tests_k83.py`: snapshot, materializacion idempotente, tenant del paquete.
- `proveedores/tests_event_domain_k82.py`: tenant proveedor y snapshot de catalogo proveedor.
- `colaboracion/tests_k84.py`, `tests_k86.py`, `tests_k877_collaboration_ux.py`: workspace, canales y UX.
- `presupuesto/tests_client_payments_k8741.py`: separacion de pago cliente vs pago operativo.
- `core/tests.py`, `core/tests_tenant_authorization_k.py`: login, roles, tenant y admin DIRTEC.
- `eventos/tests_*_v3.py`: dashboards planner, empresa, cliente, proveedor y hardening operativo.

### Permisos actuales

- DIRTEC operativo tiene bypass controlado para operacion/admin.
- Empresa admin/ventas operan por `EmpresaSuscriptora`.
- Planner opera solo eventos asignados.
- Cliente opera solo eventos propios.
- Proveedor opera solo servicios propios.
- Workspace separa canales `CLIENTE_PLANNER`, `PLANNER_PROVEEDOR`, `INTERNO`.

## 3. Que reutilizamos

- `EmpresaSuscriptora` como limite tenant.
- `EventoBoda` como evento actual mientras no exista estrategia de renombre.
- `SedeEvento` como sede tenant.
- `PaqueteBoda`, `ServicioPaquete`, `PaqueteEvento` como base K8 compatible.
- `construir_snapshot_paquete`, `capturar_snapshot_paquete`, `materializar_servicios_paquete`.
- `ServicioEvento` como instancia operativa central.
- `GastoEvento`, `PagoEvento`, `PagoClienteEvento` como sistema financiero unico.
- Workspace de colaboracion actual sobre `ServicioEvento`.
- `ContratoEvento.snapshot_comercial` como candidato para snapshot contractual K9 versionado.
- `core.services.authorization` como punto central de permisos.

## 4. Que queda legacy

- `EventoBoda`, `PaqueteBoda`, `WEDDING_PLANNER`, `wedding_planner` y `visible_para_wedding_planners` son nombres legacy. No renombrar sin fase propia.
- `Proveedor.tipo_proveedor` sirve como compatibilidad, pero no debe definir el dominio futuro completo.
- `ServicioCatalogoProveedor` describe servicios dependientes del proveedor; no sustituye el catalogo general por empresa.
- `ServicioPaquete.tipo_servicio` es un enum legacy; debe convivir con un futuro FK a catalogo.
- `EventoBoda.precio_por_persona`, `presupuesto_total`, `monto_pagado` y `DetalleProduccionEvento` contienen datos comerciales/operativos historicos.
- Landing publica actual centrada en invitaciones/boda es legacy visible.
- Eliminaciones fisicas desde dashboard legacy deben auditarse antes de K9 operativo.

## 5. Que hay que crear

- App pequena `catalogo/` o equivalente con `ServicioCatalogo` por empresa.
- Modelo puente futuro `ServicioCatalogoProveedor` generalizado o nuevo puente `ProveedorServicioCatalogo`.
- Modelo/servicio comercial de propuesta testeable.
- Snapshot contractual K9 v2, sin reemplazar v1.
- DTOs de contrato/propuesta para vistas de Empresa, Planner, Cliente, Proveedor y DIRTEC.
- Politica central de visibilidad comercial vs operativa/financiera.
- Tests de pricing, snapshot v2, cortesias, adicionales, permisos y SaaS.

## 6. Modelo de dominio K9 propuesto

Ver `docs/K9_DOMAIN_MODEL.md`.

Resumen contractual:

1. Catalogo describe.
2. Paquete vende.
3. Evento define cantidades.
4. Proveedor define costo operativo posteriormente.
5. Contrato congela el acuerdo.
6. ServicioEvento es la instancia operativa.
7. Presupuesto registra costos y pagos.
8. Colaboracion opera sobre ServicioEvento.

## 7. Flujo comercial completo

1. Empresa/Planner crea o selecciona evento.
2. Define sede tentativa/acordada.
3. Captura adultos y ninos.
4. Selecciona paquete.
5. Motor comercial calcula base por adulto/nino/cargo fijo.
6. Presenta incluidos del paquete.
7. Agrega adicionales desde catalogo o manuales.
8. Agrega cortesias con cargo cliente cero y valor informativo.
9. Aplica descuentos visibles.
10. Genera total estimado/acordado.
11. Cliente acepta.
12. Se emite `ContratoEvento` con snapshot v2.

Las formulas deben vivir en service layer, no en templates.

## 8. Flujo operativo completo

1. Contrato aceptado congela venta.
2. Materializacion crea/actualiza `ServicioEvento` idempotente.
3. Cada `ServicioEvento` puede iniciar sin proveedor.
4. Planner/Empresa asigna proveedor, empresa interna o deja por definir.
5. Se abren workspace/canales existentes por servicio.
6. Se vinculan tareas, citas, documentos, gastos y pagos.
7. Costos operativos pueden cambiar sin recalcular contrato cliente.
8. Presupuesto registra pagos de cliente a empresa y pagos empresa a proveedores/costos.

## 9. Contrato y visibilidad

- Cliente ve paquete, cantidades, incluidos, adicionales, cortesias, descuentos visibles, total, estado y documentos permitidos.
- Planner ve lo anterior mas informacion operativa segun permiso.
- Empresa ve contrato completo y capa financiera/operativa.
- DIRTEC ve administracion/soporte segun rol operativo.
- Proveedor ve solo sus `ServicioEvento`, entregables, workspace correspondiente y documentos permitidos.
- Nadie debe crear dos contratos para el mismo acuerdo; se usan proyecciones de datos.

## 10. Estrategia snapshot v1 -> v2

- Mantener `snapshot_paquete` v1 y `materializacion_version=1` para K8.
- Introducir v2 aditivo en `ContratoEvento.snapshot_comercial` o nuevo campo versionado.
- No mutar snapshots firmados.
- Lectores deben soportar v1 legacy y v2 K9.
- Migracion historica puede ser lazy: contratos K8 se interpretan con adaptador v1.

## 11. Estrategia materializacion

- Mantener `MATERIALIZACION_VERSION = 1` hasta implementar K9.
- K9 debe subir a version 2 con datos de contrato, incluidos, adicionales y cortesias.
- Usar claves de origen estables para evitar duplicados.
- Preservar servicios si desaparece el maestro.
- `precio_incluido`/valor comercial sigue siendo `valor_contratado`, nunca costo proveedor.

## 12. Estrategia proveedor post-contrato

- `ServicioEvento.proveedor` ya es nullable: conservar.
- Agregar estado conceptual de prestacion: empresa interna, proveedor externo, por definir.
- No crear proveedor ficticio para servicios internos.
- Proveedor se asigna despues del contrato y afecta operacion/costo, no el total cliente congelado.

## 13. Estrategia financiera

- No crear segundo sistema financiero.
- Venta cliente: contrato y `PagoClienteEvento`.
- Costo operativo: `GastoEvento` y `PagoEvento`.
- `ServicioEvento` puede ser concepto puente, no fuente para recalcular venta congelada.
- Reportes deben separar ingreso, costo, saldo cliente, saldo proveedor y margen.

## 14. Hallazgos seguridad

Ver `docs/K9_SECURITY_MATRIX.md`.

Hallazgos principales:

- `SaasSubscriptionMiddleware.PATHS_OPERATIVOS` no incluye `/colaboracion/`.
- Tampoco incluye `/presupuesto/`, aunque esa app esta montada como URL independiente.
- Algunas descargas en `secure_files.py` tienen fallback proveedor menos estricto que `_es_proveedor_servicio`.
- Login central hereda `next` de Django sin validar destino por usuario nuevo.

## 15. Plan de migraciones aditivas

Ver `docs/K9_MIGRATION_STRATEGY.md`.

Reglas:

- No borrar modelos.
- No renombrar tablas.
- No renombrar `EventoBoda`.
- No renombrar `WEDDING_PLANNER`.
- No hacer reemplazos globales.
- Mantener K8 hasta que K9 este cubierto por tests.

## 16. Plan por fases

- K9.1: seguridad y pruebas de borde (`/colaboracion/`, `/presupuesto/`, `next`, secure files).
- K9.2: app `catalogo/` y modelo `ServicioCatalogo` por empresa.
- K9.3: puente catalogo-proveedor y adaptadores desde `ServicioCatalogoProveedor`.
- K9.4: motor comercial de propuesta, DTOs y pricing adulto/nino/fijo/adicionales.
- K9.5: contrato snapshot v2 y vistas de contrato por rol.
- K9.6: materializacion v2 hacia `ServicioEvento` con cortesias.
- K9.7: presupuesto/reportes integrados sin duplicar finanzas.
- K9.8: CRUD operativo soft-delete/cancelar/archivar.
- K9.9: landing, terminologia visible, branding multiempresa y navegacion contextual.
- K9.10: Builder mobile y shortcuts, separado del dominio comercial.

## 17. Archivos previstos por fase

- K9.1: `core/middleware.py`, `core/views.py`, `core/secure_files.py`, tests de `core`, `colaboracion`, `presupuesto`.
- K9.2: nueva app `catalogo/`, modelos, admin, migrations, tests.
- K9.3: modelos puente, services/adapters, admin, tests de tenant.
- K9.4: `paquetes/services.py` o nuevo `comercial/services.py`, DTOs, tests de pricing.
- K9.5: `eventos/models.py`, `eventos/services.py`, templates de contrato por rol.
- K9.6: `paquetes/services.py`, `proveedores/models.py`, tests de materializacion.
- K9.7: `presupuesto/`, dashboards, reportes.
- K9.8: `invitaciones/views.py`, workspace, modelos operativos segun auditoria.
- K9.9: templates publicos/dashboards y copy visible.
- K9.10: Builder static/templates y tests visuales/manuales.

## 18. Tests por fase

Ver `docs/K9_TEST_MATRIX.md`.

## 19. Riesgo de regresion

- Alto: seguridad de tenant, `ServicioEvento`, materializacion, pagos y visibilidad.
- Medio: paquetes y propuesta comercial.
- Medio: login/logout y navegacion contextual.
- Bajo si se aisla: landing, copy visible y documentacion.
- Builder mobile debe ir aislado para no afectar desktop.

## 20. Criterios de aceptacion

- K8 sigue pasando tests existentes.
- K9 no rompe snapshots v1 ni materializacion v1.
- No se filtran costos/margen/notas privadas al cliente o proveedor.
- Suscripcion suspendida bloquea rutas operativas independientes.
- Login no hereda destinos privados no autorizados.
- Contrato aceptado no se recalcula por cambios posteriores de costo proveedor.
- Nuevas migraciones son aditivas y reversibles en fase.

## 21. Documentacion creada/modificada

- `docs/K9_MASTER_PLAN.md`
- `docs/K9_DOMAIN_MODEL.md`
- `docs/K9_MIGRATION_STRATEGY.md`
- `docs/K9_SECURITY_MATRIX.md`
- `docs/K9_TEST_MATRIX.md`

## 22. Git diff esperado

K9.0 solo debe agregar/modificar documentacion en `docs/`.

No debe incluir:

- cambios en codigo de negocio;
- cambios en Builder;
- migraciones;
- deploy;
- Caddy;
- PostgreSQL productivo;
- commit;
- push.
