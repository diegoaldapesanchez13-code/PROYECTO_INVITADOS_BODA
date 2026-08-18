# K9 Lifecycle Matrix

## Definitions
Editar = update a live record.
Cancelar = it existed but no longer applies/will occur.
Archivar = remove from daily operation while preserving history.
Restaurar = return archived record.
Eliminar = remove an erroneous record with no relevant history.
Purgar = permanent administrative deletion of archived data when integrity allows.

## Roles
DIRTEC: administrative control and safe purge.
Admin Empresa: full lifecycle within tenant, including safe purge.
Planner: operational lifecycle and deletion of simple errors when authorized; no historical purge.
Cliente/Proveedor: only portal-specific actions.

## Evento
Edit/cancel/archive/restore: yes.
Delete: only erroneous event without relevant history.
Purge: DIRTEC/Admin Empresa if safe.
Protected by contracts, payments, operational history, meaningful documents/RSVP/workspace.

## Paquete maestro
Edit/duplicate/archive/restore.
Delete only when safe/unreferenced.
Historical contracts survive through snapshots.

## ServicioCatalogo
Edit/archive/restore.
Delete only if no meaningful references.
Archived services disappear from new selectors.

## Proveedor
Edit/deactivate/archive/restore.
Delete only without operational history.

## Propuesta
Editable in BORRADOR/PROPUESTA/EN_REVISION.
Cancel/archive.
Delete only draft/error without contractual history.

## Contrato
Before real acceptance/activity: safe delete may be allowed.
After acceptance: never silently edit snapshot; cancel, replace or add modification/adenda.
Purge is exceptional.

## ServicioEvento
Edit provider, prestation, responsibility, costs, status, dates and notes.
Cancel/archive/restore.
Delete only if error and no contractual/workspace/financial history.

## Tarea
Edit/cancel/archive/restore.
Delete simple error without relevant activity.

## Agenda/Cita
Edit/cancel/archive/restore.
Delete duplicate/error without meaningful history.

## Documento
Edit metadata/archive/restore.
Delete only erroneous/non-protected documents.
Private access must remain authorized.

## GastoEvento
Edit/cancel/archive/restore.
Delete only without active payments/relevant history.

## PagoEvento
Reverse through ANULAR, not normal delete after registration.
Purging is exceptional administration.
Anulled payment no longer affects aggregates.

## PagoClienteEvento
Corrections limited. Cancel/anul according to existing semantics.
Do not normally delete consolidated payments.

## Invitado
Edit/archive/restore.
Delete error if no meaningful history.
RSVP NO is preserved and may release cupo.

## GrupoInvitacion
Edit/archive/restore.
Delete only when dependencies allow while preserving UUID public behavior.

## RSVP model
Registro: ACTIVO/BLOQUEADO/ARCHIVADO.
RSVP: PENDIENTE/SI/NO.
Cupo: OCUPADO/LIBERADO.

## Deletion evaluation
Sensitive deletion goes through a service layer:
`evaluar_eliminacion(objeto, usuario)`
Return: permitido, motivos, dependencias, impacto, almacenamiento estimado if useful.

## Return context
Lifecycle actions return to the same Event Workspace module/filter.

## Audit
Audit cancellation, archive/restore, provider changes, contract modifications, payment annulments, RSVP/capacity locks/releases, deletes and purges.
Before purge, record enough metadata for audit to survive physical deletion.
