# K.8.2 — Event Domain Foundation

## Objetivo

Crear una base Event-Centric modular sin romper la version estable actual.
Esta fase NO rediseña dashboards, NO elimina modelos legacy y NO modifica el Builder.

## Arquitectura introducida

### Nueva app `eventos`

- `ParticipanteEvento`: relacion explicita evento/usuario/rol/permisos.
- `ContratoEvento`: contrato versionado y snapshot comercial.
- `services.py`: compatibilidad y sincronizacion con relaciones legacy.
- `selectors.py`: lecturas centralizadas del dominio.
- `signals.py`: mantiene `EventoBoda.wedding_planner` y `EventoBoda.clientes` sincronizados durante la transicion.

### Catalogo de proveedores

En `proveedores` se agregan:

- `EtiquetaProveedor`
- `ServicioCatalogoProveedor`

Estos son recursos maestros de empresa; no son servicios contratados de una boda.

### `ServicioEvento` reforzado

Se conserva como fuente central de operacion y ahora distingue:

- origen: manual / catalogo / paquete
- modalidad: incluido / adicional / upgrade
- estado comercial
- estado operativo
- costo proveedor
- precio cliente
- ajuste cliente
- snapshots de proveedor y catalogo
- notas internas
- referencia opcional al servicio maestro de catalogo

Los campos legacy (`estado`, `costo_total`, documentos directos, etc.) se conservan temporalmente para compatibilidad.

## Multiempresa

Se agregaron validaciones para impedir:

- proveedor de otra empresa en un `ServicioEvento`
- servicio de catalogo de otra empresa/proveedor
- planner/colaborador sin membresia activa en la empresa del evento

## Migracion de datos

`eventos.0002_backfill_participantes_legacy` crea participantes desde:

- `EventoBoda.wedding_planner` -> `ParticipanteEvento(PLANNER)`
- `EventoBoda.clientes` -> `ParticipanteEvento(CLIENTE)`

`proveedores.0007_event_domain_foundation` conserva servicios existentes y copia:

- `costo_total` -> `costo_proveedor`
- `costo_total` -> `precio_cliente`
- proveedor actual -> `proveedor_nombre_snapshot`
- origen inicial -> `MANUAL`
- modalidad inicial -> `ADICIONAL`

No se borra informacion existente.

## Compatibilidad transitoria

Las vistas actuales pueden seguir escribiendo sobre `wedding_planner` y `clientes`.
Signals de K.8.2 sincronizan automaticamente el nuevo modelo de participantes.
Esto permite migrar la UX por fases sin mantener dos fuentes divergentes.

## Gates ejecutados

- `manage.py check`: OK
- `makemigrations --check --dry-run`: OK
- migracion real sobre copia de `db.sqlite3`: OK
- 8 tests especificos K.8.2: OK
- suite completa legacy: el primer fallo reproducible tambien falla en el ZIP estable original (`DashboardReportesTests.test_dashboard_avanzado_empresa_crea_operacion_sin_admin`), por una expectativa textual antigua del dashboard. No es regresion de K.8.2.

## Siguiente fase

K.8.3 — Package Snapshot & Service Materialization:

`PaqueteBoda` maestro -> snapshot contractual del evento -> materializacion de `ServicioEvento` independientes.
