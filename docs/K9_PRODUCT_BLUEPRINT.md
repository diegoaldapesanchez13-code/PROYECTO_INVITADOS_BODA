# K9 Product Blueprint — DIRTEC Event Studio

## Vision
DIRTEC Event Studio is a multi-tenant SaaS product of DIRTEC. `dirtech.me/` remains reserved for the wider DIRTEC ecosystem. Event Studio begins directly at login and redirects automatically according to role.

## Product principles
- Event is the operational center.
- Company manages the business; Planner manages work; Event Workspace concentrates execution.
- Backend complexity must not leak into UX.
- Initial creation must be simple; unknown values may remain “Por definir”.
- Warnings are preferred to artificial mandatory fields.
- Contract and operation are distinct authorities.
- Errors may be deleted when safe; real history is cancelled/archived.
- Every action preserves user context.
- Mobile and desktop are first-class requirements.
- Tenant security and permissions are non-negotiable.
- Branding is controlled by DIRTEC; no arbitrary tenant CSS.

## Product hierarchy
DIRTEC Console
- Empresas
- Usuarios
- Suscripciones
- Branding
- Auditoría
- Almacenamiento

Empresa
- Inicio
- Eventos
- Calendario
- Clientes
- Planners
- Proveedores
- Catálogo
- Paquetes
- Finanzas
- Configuración

Planner
- Inicio
- Mis eventos
- Calendario
- Mis tareas

Event Workspace
- Resumen
- Datos
- Comercial
- Servicios
- Tareas
- Agenda
- Invitados
- Documentos
- Finanzas
- Invitación
- Actividad
- Configuración

Portales
- Cliente
- Proveedor

## Login
No role selector and no three-button landing. User authenticates and backend routes to the correct dashboard.

## Event Workspace
Company and Planner share the same Event Workspace. Permissions decide visibility/actions. Desktop uses persistent header + sidebar. Mobile uses compact header + bottom navigation + Quick Create + “Más”.

## Return context
Post/async actions preserve event, section, filters and useful view state. Never accept arbitrary external `next` targets.

## Generic Event
Internal legacy model name may remain `EventoBoda` temporarily. UI always presents “Evento”.
Minimal creation:
- Nombre required
- Tipo optional
- Cliente optional
- Planner optional
- Fecha optional

General states:
BORRADOR, ACTIVO, FINALIZADO, CANCELADO, ARCHIVADO.

## Catalog and packages
Catalog service creation should require only name; category/description/media/provider compatibility are optional.
Package creation should be simple, then edited by General, Precio, Servicios, Multimedia, Avanzado.
Visible pricing modes: POR_DEFINIR, FIJO, POR_PERSONA, MIXTO.
PaqueteServicio must support add/edit/remove/reorder.

## Commercial flow
Evento -> Propuesta -> Aceptación -> Contrato -> Operación.
Contract is frozen. Later customer changes become modifications/adendas or replacements, not silent snapshot edits.

## Operational services
ServicioEvento is operational truth: provider/company/undefined, costs, status, dates, tasks, documents, workspace and payments. Changing provider does not modify contract and must be audited.

## Guests
Separate Registro, RSVP and Cupo.
Registro: ACTIVO, BLOQUEADO, ARCHIVADO.
RSVP: PENDIENTE, SI, NO.
Cupo: OCUPADO, LIBERADO.
A NO response may release capacity while preserving history.
`guest_analytics.py` should become the single metric authority.

## Finance
ContratoEvento = sale.
PagoClienteEvento = customer cash received.
GastoEvento = operational cost.
PagoEvento = operational cash paid.
Margin = sale - cost.
Cash flow = received - paid.

## Branding
Central brand context: logo, hero, login image, primary/secondary/accent colors and future favicon. No arbitrary CSS.

## Responsive
Validate new screens at 375, 390, 430, 768, 1024 and 1440 px.
Mobile converts tables to cards, dropdowns to bottom sheets and desktop sidebars to bottom navigation.

## Acceptance questions
1. Is it easier than before?
2. Does it work well on mobile?
3. Does it preserve context?
4. Does it respect tenant/permissions?
5. Does it reduce technical debt?
