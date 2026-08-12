# K.8.7.3 — Company Dashboard V3

## Objetivo
Convertir el dashboard de Empresa en administración del negocio, no en un segundo dashboard operativo del evento.

## Fuente de verdad
- Empresa: tenant, usuarios, clientes, equipo, proveedores maestros, catálogos, plan.
- Evento: operación completa de una celebración.
- ServicioEvento: ejecución de un servicio contratado.

## Cambios
- Nuevo `eventos/company_dashboard_v3.py` para métricas Event-Centric.
- Resumen ejecutivo del portafolio con acciones de Cliente/Proveedor, tareas vencidas y confirmaciones.
- Tarjetas de evento con salud operativa y un único acceso `Abrir evento`.
- Se retiran accesos operativos duplicados a Builder/Mesas/Calendario desde Empresa.
- Se conserva administración de la ficha del evento (datos base, estado, Planner, sede).
- Se mantienen módulos separados Clientes / Equipo / Proveedores / Catálogos.
- Se agrega Configuración para identidad, suscripción/capacidad y permisos.
- No usa `ExpedienteServicio` ni módulos legacy para construir el resumen de empresa.

## Migraciones
No requiere migraciones.

## Builder
No se modifica.
