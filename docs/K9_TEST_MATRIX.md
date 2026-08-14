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

Tests propuestos:

- proveedor ofrece multiples servicios;
- servicio es ofrecido por multiples proveedores;
- puente rechaza tenant cruzado;
- `Proveedor.tipo_proveedor` sigue funcionando en vistas legacy;
- adaptador desde `ServicioCatalogoProveedor` mantiene datos historicos;
- proveedor inactivo no aparece como opcion operativa.

## K9.4 Motor comercial

Tests propuestos:

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

## K9.5 Contrato y visibilidad

Tests propuestos:

- crear snapshot v2 al aceptar propuesta;
- snapshot v2 congela sede, duracion, tarifas, cantidades y lineas;
- modificar paquete/catalogo despues no cambia contrato;
- contrato v1 legacy se renderiza;
- contrato v2 se renderiza;
- cliente no ve costo/margen/notas privadas;
- proveedor no ve contrato completo;
- planner solo si evento asignado;
- empresa solo su tenant;
- DIRTEC operativo puede auditar segun permiso.

## K9.6 Materializacion v2

Tests propuestos:

- materializa incluidos;
- materializa adicionales;
- materializa cortesias con cargo cliente cero;
- servicio nace con proveedor `null`;
- re-ejecutar no duplica;
- master eliminado no rompe;
- cambio de proveedor posterior no cambia `valor_contratado`;
- cambio de costo posterior no cambia snapshot;
- workspace se abre sobre `ServicioEvento`.

## K9.7 Presupuesto

Tests propuestos:

- pago cliente no crea `PagoEvento`;
- pago operativo no crea `PagoClienteEvento`;
- saldo cliente usa contrato y pagos cliente;
- costo operativo usa gastos y pagos operativos;
- proveedor no revisa pagos cliente;
- cliente no ve pagos proveedor;
- margen solo roles internos autorizados;
- gasto asociado a servicio exige mismo evento.

## K9.8 CRUD operativo

Tests propuestos:

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

## K9.10 Builder mobile

Tests propuestos:

- desktop no cambia visualmente;
- mobile no tiene overflow horizontal;
- canvas usa altura estable con `100dvh`;
- drawers/bottom sheets no tapan toolbar critica;
- shortcuts no disparan dentro de input/textarea/select/contenteditable;
- Delete/Backspace/Ctrl-C/Ctrl-V/Ctrl-X/Ctrl-Z/redo/Ctrl-D/Enter/Escape funcionan en canvas.
