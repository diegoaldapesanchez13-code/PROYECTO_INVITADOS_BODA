# K9 Test Matrix

Estado: matriz inicial K9.0. No ejecuta cambios.

## Cobertura existente a preservar

| Area | Tests observados | Debe seguir pasando |
| --- | --- | --- |
| Login/roles | `core/tests.py` | SI |
| Tenant/autorizacion | `core/tests_tenant_authorization_k.py` | SI |
| Paquetes snapshot | `paquetes/tests_k83.py` | SI |
| Proveedor/ServicioEvento | `proveedores/tests_event_domain_k82.py` | SI |
| Workspace | `colaboracion/tests_k84.py`, `tests_k86.py`, `tests_k877_collaboration_ux.py` | SI |
| Pagos cliente | `presupuesto/tests_client_payments_k8741.py` | SI |
| Portales v3 | `eventos/tests_*_v3.py` | SI |
| Builder | `invitaciones/tests_builder_*` | SI, sin tocar en K9.0 |

## Matriz minima solicitada

| Caso | Fase | Tipo | Resultado esperado |
| --- | --- | --- | --- |
| Empresa A vs Empresa B | K9.1/K9.2 | Django unit/integration | A no ve catalogo/eventos/contratos de B. |
| Planner A vs evento no asignado | K9.1/K9.5 | Django integration | 403/404 sin datos filtrados. |
| Cliente A vs evento B | K9.1/K9.5 | Django integration | Cliente no ve contrato ni servicios de otro evento. |
| Proveedor A vs servicio B | K9.1/K9.6 | Django integration | Proveedor no ve workspace/archivo/servicio ajeno. |
| Suscripcion suspendida | K9.1 | Middleware tests | Bloquea GET/POST en `/colaboracion/` y `/presupuesto/`. |
| IDs manipulados | K9.1+ | Integration | IDs ajenos devuelven 403/404. |
| Canales workspace | K9.1/K9.6 | Integration | Cliente/proveedor no ven canales indebidos. |
| Secure files | K9.1 | Integration | Descargas respetan helper central y visibilidad. |
| Snapshot v1 | K9.5 | Unit | Contratos K8 se reconstruyen igual. |
| Snapshot futuro v2 | K9.5 | Unit | Contrato congela cantidades/tarifas/lineas/total. |
| Materializacion idempotente | K9.6 | Unit | Re-ejecutar no duplica `ServicioEvento`. |
| Tarifa adulto | K9.4 | Unit | Adultos * precio adulto. |
| Tarifa nino | K9.4 | Unit | Ninos * precio nino. |
| Adicional fijo | K9.4 | Unit | Subtotal fijo correcto. |
| Adicional por persona | K9.4 | Unit | Adultos+ninos * tarifa. |
| Cortesia | K9.6 | Unit/integration | Cargo cliente cero, valor informativo, costo operativo posible. |
| Descuento | K9.4/K9.5 | Unit | Resta del total segun regla. |
| Contrato congelado | K9.5 | Unit/integration | Cambios posteriores no modifican snapshot firmado. |
| Proveedor asignado despues | K9.6 | Integration | Servicio sin proveedor pasa a proveedor sin cambiar contrato. |
| Cambio costo proveedor sin alterar contrato | K9.7 | Unit/integration | Margen cambia, total cliente no. |
| Cliente visualiza contrato | K9.5 | View test | Ve paquete, cantidades, incluidos, adicionales, cortesias, total. |
| Planner visualiza contrato | K9.5 | View test | Ve contrato y capa operativa si asignado. |
| Empresa visualiza contrato | K9.5 | View test | Ve contrato completo de su tenant. |
| Cliente NO visualiza margen/costo interno | K9.5/K9.7 | View test | HTML/JSON no contiene costo, margen, pagos proveedor ni notas privadas. |

## K9.1 Seguridad

Tests propuestos:

- `test_saas_bloquea_colaboracion_get_empresa_suspendida`.
- `test_saas_bloquea_colaboracion_post_empresa_suspendida`.
- `test_saas_bloquea_presupuesto_get_empresa_suspendida`.
- `test_saas_bloquea_presupuesto_post_empresa_suspendida`.
- `test_secure_documento_proveedor_inactivo_no_descarga`.
- `test_secure_documento_proveedor_otro_tenant_no_descarga`.
- `test_secure_pago_operativo_no_visible_a_cliente`.
- `test_login_descarta_next_privado_de_usuario_anterior`.
- `test_login_honra_next_solo_si_usuario_autorizado`.

## K9.2 Catalogo

Tests implementados en `catalogo.tests_k92`:

- empresa crea servicio catalogo propio;
- nombre duplicado dentro de empresa se valida segun constraint;
- misma denominacion permitida en otra empresa si se decide;
- admin empresa no ve catalogo de otra empresa;
- planner puede consultar catalogo de su empresa;
- cliente y proveedor no administran catalogo;
- servicio catalogo no exige costo ni precio cliente;
- media/PDF respeta validadores;
- imagen/PDF de catalogo se guardan fuera de `MEDIA_ROOT`;
- media comercial privada del catalogo no se sirve por `MEDIA_URL`;
- vistas autorizadas permiten descarga a Empresa/DIRTEC/Planner mismo tenant y bloquean otro tenant, cliente y proveedor;
- empresa suspendida no accede a `/catalogo/`;
- POST no puede forzar `empresa` ajena;
- desactivar preserva el registro.

## K9.3 Proveedor-servicio

Tests implementados en `catalogo.tests_k93`:

- proveedor ofrece multiples servicios;
- servicio es ofrecido por multiples proveedores;
- puente rechaza tenant cruzado;
- proveedor sin empresa rechaza catalogo K9;
- empresa gestiona relaciones propias;
- planner lee y no gestiona;
- cliente/proveedor no administran;
- DIRTEC accede segun autorizacion central;
- helpers excluyen proveedor, servicio o relacion inactiva;
- `Proveedor.tipo_proveedor` sigue funcionando en vistas legacy;
- `ServicioCatalogoProveedor` mantiene datos historicos;
- `ServicioEvento` actual no se rompe.

## K9.4 Motor comercial

Tests implementados en `paquetes.tests_k94`:

- base adulto/nino/fijo;
- paquete sin precio nino usa regla definida;
- capacidad minima/maxima genera advertencia no bloqueo;
- adicional `FIJO`;
- adicional `POR_ADULTO`;
- adicional `POR_NINO`;
- adicional `POR_PERSONA`;
- adicional `POR_UNIDAD`;
- adicional `MANUAL`;
- descuento no deja total negativo salvo politica explicita;
- DTO no depende de template.
- adicional manual sin catalogo;
- cortesias visibles con cargo cliente cero;
- Empresa A no ve propuesta B;
- Empresa A no usa paquete B;
- Planner no usa evento no asignado;
- Cliente y proveedor no administran propuestas;
- POST no fuerza tenant;
- paquete inactivo no puede seleccionarse para nueva propuesta;
- servicio catalogo inactivo no se agrega como nueva linea;
- modificar paquete maestro no corrompe desglose persistido;
- legacy `PaqueteBoda`, `ServicioPaquete` y snapshot K8 siguen funcionando;
- media privada de paquete queda fuera de `MEDIA_ROOT` y se descarga por vista autorizada.

## K9.5 Contrato y visibilidad

Tests implementados en `eventos.tests_k95`:

- crear contrato v2 desde propuesta `ACEPTADO`;
- rechazar generacion desde `BORRADOR`, `PROPUESTA` y `EN_REVISION`;
- cambiar `PropuestaEvento` a `CONTRATADO` solo despues de crear el contrato;
- idempotencia: segunda generacion devuelve el mismo contrato;
- `snapshot_version=2` en modelo y JSON;
- snapshot congela adultos, ninos, paquete, incluidos, adicionales, cortesias, descuento y total;
- recalc server-side ignora totales manipulados en la propuesta;
- modificar paquete, catalogo, propuesta o proveedor despues no cambia el contrato;
- snapshot no contiene costo proveedor ni margen;
- cliente autorizado ve contrato publico;
- cliente ajeno no ve contrato;
- cliente no ve campos internos;
- planner asignado ve contrato;
- planner no asignado no ve contrato;
- empresa ve solo contratos de su tenant;
- proveedor no ve contrato completo;
- DIRTEC autorizado ve contrato;
- lector v1 mantiene legible `PaqueteEvento.snapshot_paquete`;
- snapshot/materializacion K8 sigue funcionando;
- generar contrato no crea `ServicioEvento`, `GastoEvento`, `PagoEvento` ni `PagoClienteEvento`;
- POST manipulado no cruza tenant;
- lector publico no expone metadata interna.

## K9.6 Materializacion v2

Tests implementados en `eventos.tests_k96`:

- materializa incluidos;
- materializa adicionales;
- materializa cortesias;
- cortesia con cargo cliente cero;
- servicio nace con proveedor `null`;
- servicio manual funciona sin catalogo;
- master catalogo ausente no rompe;
- master catalogo inactivo no rompe snapshot historico;
- dos llamadas no duplican;
- tres llamadas no duplican;
- lineas distintas del mismo catalogo no colisionan;
- contrato incorrecto/no v2 no materializa;
- contrato no contratado no materializa;
- contrato cancelado no materializa;
- tenant cruzado rechaza vinculo de catalogo;
- valor contratado viene del snapshot;
- cambio tarifa/catalogo no cambia valor;
- cambio paquete no cambia valor;
- proveedor asignado despues se conserva al rematerializar;
- costo proveedor se conserva;
- notas operativas se conservan;
- estado operativo se conserva;
- no crea `GastoEvento`;
- no crea `PagoEvento`;
- no crea `PagoClienteEvento`;
- no altera total de `ContratoEvento`;
- registra `materializado_en`;
- `materializacion_version = 2`;
- rollback completo si falla una linea;
- workspace se abre sobre `ServicioEvento`;
- proveedor no asignado no obtiene acceso;
- cliente solo obtiene canal permitido, sin acceso operativo indebido.

## K9.7 Presupuesto

Tests implementados en `presupuesto.tests_k97`:

- total contratado sale de `ContratoEvento` v2;
- pagos cliente suman solo estados recibidos/validos;
- saldo cliente y sobrepago se calculan desde contrato y pagos cliente;
- costo estimado usa `GastoEvento.monto_estimado`;
- costo real suma solo `monto_real` registrado;
- costo comprometido usa `monto_real` cuando existe y `monto_estimado` cuando no;
- pagos operativos usan `PagoEvento`;
- saldo operativo separa costo de pagos realizados;
- margen estimado y real se calculan como venta menos costo;
- porcentaje de margen no divide entre cero;
- flujo neto de caja se calcula separado de margen;
- cambiar proveedor/costo/pago no altera total contractual;
- servicios `EMPRESA`, `PROVEEDOR` y `POR_DEFINIR` no requieren proveedor ficticio;
- costos pendientes generan advertencia;
- cliente no ve costos, margen ni pagos operativos;
- planner sin permiso financiero no ve margen/costos;
- planner asignado sin permiso financiero no ve resumen interno;
- planner con acceso central al evento y permiso financiero ve resumen interno;
- empresa del mismo tenant ve dashboard financiero;
- empresa de otro tenant queda bloqueada;
- proveedor no ve total contractual ni pagos cliente;
- compatibilidad K8 via `PaqueteEvento` sigue disponible con advertencia legacy.

Regresion ligera K9.7:

- `eventos.tests_k96`;
- `eventos.tests_k95`;
- `paquetes.tests_k94`;
- `presupuesto.tests_client_payments_k8741`.

## K9.8 CRUD operativo

Tests propuestos:

- editar, cancelar, archivar y eliminar tienen rutas/servicios semanticamente separados;
- eliminar servicio contratado bloqueado o convertido a cancelar;
- gasto con pagos no se elimina fisicamente;
- documento historico se archiva si aplica;
- tarea se cancela sin perder historial;
- cita se cancela desde `ActividadItinerario`;
- autor puede eliminar adjunto segun regla actual;
- operador puede archivar tema;
- cliente/proveedor no archivan canales no permitidos.

## K9.9 UX visible

Tests propuestos:

- landing contiene `DIRTEC Event Studio`;
- textos visibles de boda/wedding clasificados y corregidos por fase;
- rutas internas legacy siguen funcionando;
- botones volver usan destino por rol;
- branding tenant muestra logo/colores controlados;
- password reset renderiza sin filtrar existencia de usuario.

## Requisitos transversales futuros

### Invitados / RSVP

Tests propuestos:

- invitado bloqueado conserva historico;
- invitado bloqueado no cuenta como activo;
- invitado bloqueado no aparece en pendientes;
- invitado bloqueado no entra en mesas;
- invitado bloqueado no recibe comunicaciones;
- invitado bloqueado puede reactivarse;
- eliminacion fisica solo permitida si no hay historial relevante;
- dashboard, filtros y exportaciones usan la misma service/query layer;
- dashboard muestra total activos, confirmados si, confirmados no, pendientes y bloqueados/historico;
- cada KPI del dashboard filtra la lista correspondiente.

### Branding por empresa

Tests propuestos:

- DIRTEC configura logo, portada/hero, imagen encabezado, color principal y color secundario;
- Empresa, Planner, Cliente y Proveedor reciben branding consistente del tenant;
- login/portal aplica branding cuando corresponda;
- tenant no puede inyectar CSS arbitrario.

### Auditoria

Tests propuestos:

- cambio en contrato registra quien, que y cuando;
- cambio en servicio registra estado anterior/nuevo cuando aplique;
- cambio en paquete registra auditoria;
- cambio en invitado registra auditoria;
- accion operativa relevante registra auditoria.

### Estados comerciales

Tests propuestos:

- propuesta transiciona por `BORRADOR`, `PROPUESTA`, `EN REVISION`, `ACEPTADO`, `CONTRATADO`, `CANCELADO`;
- propuesta puede cambiar antes de aceptarse;
- contrato aceptado queda congelado y no cambia por modificaciones posteriores de propuesta/catalogo/paquete.

## K9.10 Builder mobile

Tests propuestos:

- desktop no cambia visualmente;
- mobile no tiene overflow horizontal;
- canvas usa altura estable con `100dvh`;
- drawers/bottom sheets no tapan toolbar critica;
- shortcuts no disparan dentro de input/textarea/select/contenteditable;
- Delete/Backspace/Ctrl-C/Ctrl-V/Ctrl-X/Ctrl-Z/redo/Ctrl-D/Enter/Escape funcionan en canvas.
