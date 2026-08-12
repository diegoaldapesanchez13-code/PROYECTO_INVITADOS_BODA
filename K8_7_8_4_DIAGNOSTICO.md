# K.8.7.8.4 — Diagnóstico de regresiones restantes

## Regresión real corregida
El Event Dashboard V3 permitía al Planner seleccionar por POST un proveedor
activo del mismo tenant aunque `visible_para_wedding_planners=False`.

Corrección:
- `proveedor_empresa_para_evento()` filtra visibilidad para Planner;
- un `proveedor_id` oculto, ajeno o inválido produce 404;
- el selector del Event Dashboard solo entrega proveedores visibles al Planner;
- DIRTEC y Admin Empresa conservan catálogo completo del tenant.

Se agregan pruebas contra las rutas K8 actuales:
- Planner no muta evento no asignado;
- Planner no usa proveedor oculto;
- Planner no usa proveedor de otra empresa;
- el selector no filtra mal.

## Contratos PRE-K8 retirados/modernizados
- CRUD de ServicioEvento dentro del Planner Dashboard V2: retirado; el Planner V3
  abre Event Dashboard/Service Workspace.
- Generación automática de pendientes desde el panel monolítico de contratos:
  diferida al futuro rediseño de contratos/paquetes.
- métricas RSVP: ahora son por `Invitado`, no por campos agregados de grupo.
- buffet: usa `menu_asignado`; `menu_infantil` boolean ya no es la autoridad.
- calendario: `ACTIVIDAD` se presenta como `Actividad operativa`.
- Dashboard Empresa/Event Dashboard: assertions actualizados a UI V3.
- denegación de Admin Empresa al dashboard Planner se conserva (403), pero el
  test deja de exigir el logger específico del dashboard viejo porque el tenant
  gate bloquea antes.

## No modificado
- Builder interno;
- modelos/migraciones;
- base de datos;
- renderer público;
- pagos;
- archivos;
- PostgreSQL/deploy.

## Nota K.8.7.8 baseline
- `DetalleProduccionEvento` desde el panel monolitico de contrato queda
  clasificado como CONTRATO PRE-K8 retirado.
- CRUD monolitico de banquete/decoracion/musica/canciones desde Event Dashboard
  queda clasificado como CONTRATO PRE-K8 retirado.
- Calendario de tareas usa el ancla V3 `#tareas`, no `#operacion`.
- Invitados valida `menu_asignado`; `menu_infantil` ya no es autoridad.
