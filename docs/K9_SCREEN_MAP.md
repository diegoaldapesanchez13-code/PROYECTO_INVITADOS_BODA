# K9 Screen Map

## Access
### Login
User/password, show password, forgot password. Automatic role redirect.

### Password recovery
Email -> confirmation -> reset link -> new password -> login.

## DIRTEC Console
Inicio, Empresas, Usuarios, Suscripciones, Branding, Almacenamiento, Auditoría, Configuración.

## Company Dashboard
Inicio, Eventos, Calendario, Clientes, Planners, Proveedores, Catálogo, Paquetes, Finanzas, Configuración.
Home shows branding, KPIs, upcoming events, attention items and activity.

## Planner Home
Inicio, Mis eventos, Calendario, Mis tareas. Shows today, assigned events and attention items.

## Events list
Search, filters, cards/list, + Nuevo evento.
Filters: activos, próximos, sin fecha, finalizados, cancelados, archivados.

## Create Event
Nombre, tipo, cliente, planner, fecha. Returns directly to Event Workspace > Resumen.

## Event Workspace
Desktop: persistent header + sidebar.
Mobile: compact header + bottom nav + Quick Create + Más.

Sections:
Resumen, Datos, Comercial, Servicios, Tareas, Agenda, Invitados, Documentos, Finanzas, Invitación, Actividad, Configuración.

### Resumen
Contract/cash KPIs, services, tasks, guests, upcoming milestones and “Requiere atención”.

### Datos
General, date/time, location, responsibilities, details. Save remains on the same page.

### Comercial
Resumen comercial, Propuesta, Contrato, Modificaciones.
Proposal shows counts, package, included items, additions, courtesies, discount and full price breakdown.
Contract is visual and supports view/download/cancel/modification/replacement based on state.

### Servicios
Filters: todos, por definir, proveedor, empresa, activos, cancelados, archivados.
Actions: create, edit, assign/change provider, cancel, archive, delete if safe.
Detail: general, prestación, costs, tasks, docs, conversation, payments, activity.

### Tareas
List + Kanban. Filters: all, mine, today, overdue, archived.

### Agenda
Timeline + calendar + list. Create/edit/cancel/archive/restore/delete-error.

### Invitados
KPIs: activos, sí, no, pendientes, histórico, occupied/free capacity.
Filters by RSVP, registration state, table, group, invitation status and confirmation lock.
Subsections: Lista, Mesas, RSVP, Comunicaciones.

### Documentos
Search/filter, upload, secure open, metadata edit, archive, restore, safe delete.

### Finanzas
Resumen, Cliente, Gastos, Proveedores.
Show sale, received, customer balance, estimated/committed/real cost, margin, cash flow.

### Invitación
State, URL, preview, RSVP settings, Open Builder.

### Actividad
Human-readable audit feed with category filters.

### Configuración
General, RSVP, Notifications, Permissions, Lifecycle, Danger Zone.

## Company Catalog
Servicios, Paquetes, Proveedores.
Package editor: General, Precio, Servicios, Multimedia, Avanzado.
PaqueteServicio supports add/edit/remove/reorder.

## Client Portal
Resumen, Contrato, Pagos, Decisiones, Documentos, Invitación. No margins/internal costs.

## Provider Portal
Assigned services, tasks, conversation, documents, quotes, permitted payments. No full customer contract/margins.

## Builder
Desktop remains specialized. Mobile future: canvas + bottom toolbar + layers/assets drawers + inspector sheet.

## Return rule
All Event Workspace actions return to the same event/section/filter, never to a generic dashboard unless the user explicitly navigates there.
