# K.8.7.8.3 — Diagnóstico y modernización del suite global

## Resultado observado

El gate global llegó a 353 pruebas y terminó con 44 fallos y 14 errores.

La inspección mostró que el bloque restante está dominado por pruebas PRE-K8 que
siguen describiendo componentes retirados intencionalmente.

## Contratos retirados

Se marcan explícitamente como históricos 52 tests dentro del
monolito `invitaciones/tests.py`.

### Clase InvitadoTests
Contrato histórico del renderer HTML/editor anterior.

Actualmente estas responsabilidades están cubiertas por:
- tests_builder_public.py
- tests_builder_django.py
- tests_builder_v4.py
- tests_guest_domain_v2.py
- tests_guest_rsvp_v2.py
- eventos/tests_client_guests_v3.py

### Clase PortalTests
Contrato histórico de Portal Cliente / Proveedor anterior.

Actualmente cubierto por:
- eventos/tests_client_portal_v3.py
- eventos/tests_provider_portal_v3.py
- presupuesto/tests_client_payments_k8741.py
- colaboracion/tests_k877_collaboration_ux.py

### Diez pruebas de personalización legacy dentro de DashboardReportesTests
Cubren preview, plantillas y media del editor anterior.
Se retiran únicamente esas pruebas.
El resto de DashboardReportesTests continúa activo.

## Pruebas activas que NO se retiran

Siguen activas, entre otras:
- multiempresa;
- aislamiento por tenant;
- roles;
- empresa;
- Planner;
- catálogos;
- usuarios;
- proveedores;
- paquetes;
- operación;
- catering/decoración/entretenimiento;
- invitados;
- mesas;
- métricas;
- exportaciones;
- calendario;
- alertas.

## Assertions V2 modernizados

`tests_builder_j1_2.py`
- "Datos que alimentan Builder" -> "Invitación digital"
- "Builder Assets" -> "Abrir Builder"

`tests_dashboard_product_v2.py`
- deja de exigir el tab monolítico `operacion`;
- exige los paneles V3 `servicios`, `agenda`, `tareas`, `finanzas`,
  `documentos`, `invitados` e `invitacion`.

`tests_role_redirect_k3.py`
- conserva la prohibición de enlazar Inicio a `/`;
- ya no exige un link decorativo "Inicio" que Portal Cliente V3 no utiliza;
- valida "Mi evento" y "Cerrar sesión".

## Lo que NO hace este hotfix

- no modifica Builder;
- no modifica vistas;
- no restaura endpoints legacy;
- no modifica modelos;
- no crea migraciones;
- no toca la base;
- no cambia permisos;
- no cambia producción.

La finalidad es que el gate global pruebe el producto K8 vigente en vez de
intentar restaurar arquitectura retirada.
