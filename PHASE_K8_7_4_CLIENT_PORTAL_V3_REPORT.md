# K.8.7.4 — Client Portal V3

## Objetivo
Sustituir el portal Cliente incremental/legacy por una experiencia orientada a acciones.

## Navegación
- Inicio
- Servicios
- Agenda
- Tareas
- Documentos
- Invitados
- Invitación

## Regla principal
El cliente ve primero **qué necesita hacer**:
- aprobaciones pendientes;
- propuestas pendientes;
- citas por confirmar;
- tareas asignadas directamente a su usuario.

## Servicios
Cada ServicioEvento abre únicamente el canal `CLIENTE_PLANNER`.

## Privacidad
No se exponen:
- cotizaciones/costos del proveedor;
- margen;
- notas internas;
- documentos no visibles al cliente;
- tareas de Planner/equipo;
- citas de otros clientes;
- actividades operativas de servicio que no son una cita del cliente.

Se endureció además el `Service Workspace`: `cotizaciones_workspace` no se consulta para Cliente.

## Legacy retirado del portal
El template ya no incluye `colaboracion/_cliente.html` y la vista deja de construir `ExpedienteServicio`/presupuesto legacy para renderizar el portal.

Las rutas legacy de ExpedienteServicio permanecen físicamente mientras otros roles pendientes de migración todavía puedan referenciarlas; no son parte del Client Portal V3.

## Migraciones
No requiere migraciones.
