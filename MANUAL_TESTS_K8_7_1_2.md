# Pruebas manuales K.8.7.1.2 — Operational Clarity & Agenda

## Gate 1 — Event Dashboard sin legacy
1. Entrar como Planner/empresa a `/dashboard/?evento=<id>`.
2. Confirmar que **NO** aparece `Compatibilidad temporal`, `Contenido heredado` ni `Operación heredada`.
3. Confirmar navegación: Resumen, Servicios, Agenda, Tareas, Finanzas, Documentos, Invitados, Invitación y Equipo.

## Gate 2 — Cards Cliente / Proveedor
1. Abrir `Servicios`.
2. Cada ServicioEvento debe mostrar dos cards: **CLIENTE** y **PROVEEDOR**.
3. En Cliente deben aparecer acciones como aprobación, propuesta, cambios del cliente o confirmación de cita.
4. En Proveedor deben aparecer acciones como revisar cotización, esperar nueva versión, confirmar cita o asignar proveedor.
5. Cada acción debe indicar explícitamente `Responsable · Cliente / Planner / Proveedor`.
6. Costos internos/margen no deben aparecer en ninguna card compartida.

## Gate 3 — Tarea ya no es Cita
1. Abrir `Tareas` y crear `Revisar contrato K8712` con fecha límite.
2. Confirmar que el formulario **no pide hora de inicio/fin**.
3. Confirmar que la tarea aparece con responsable, rol, fecha límite y servicio/evento general.
4. Abrir Calendario y comprobar que la tarea aparece como elemento de día completo, no como reunión.

## Gate 4 — Crear Cita real
1. Abrir `Agenda > + Nuevo elemento de agenda`.
2. Tipo `Cita`, título `Prueba de menú K8712`, seleccionar el servicio Banquete, fecha/hora y ubicación.
3. Guardar.
4. Confirmar que aparece en `Próximas citas`, separada del itinerario.
5. Deben aparecer participantes del evento y el proveedor del servicio con estado de confirmación.

## Gate 5 — Confirmación Cliente
1. Entrar con el usuario Cliente.
2. Si intenta `/dashboard/?evento=<id>`, debe ser redirigido a Portal Cliente.
3. Desde su Servicio > Conversar, localizar `Prueba de menú K8712`.
4. Confirmar asistencia.
5. Volver como Planner: la persona debe aparecer `Confirmado`.

## Gate 6 — Confirmación Proveedor
1. Entrar con el usuario Proveedor.
2. Si intenta `/dashboard/?evento=<id>`, debe ser redirigido a Portal Proveedor.
3. Abrir el workspace del servicio y confirmar la cita.
4. Volver como Planner y confirmar el cambio de estado.
5. Cliente no debe poder responder por el proveedor y viceversa.

## Gate 7 — Actividad vs Hito
1. Crear `Actividad` = `Montaje decoración`.
2. Crear `Hito` = `Ceremonia`.
3. Ambos deben aparecer en `Itinerario y actividades`, no en `Próximas citas`.
4. No deben solicitar confirmación individual.

## Gate 8 — Migración de tareas con hora
Si en la base existía una TareaEvento con hora_inicio/hora_fin antes de esta fase:
1. Después de `migrate`, debe existir una CITA equivalente en Agenda.
2. La tarea original conserva su función de tarea pero sus horas legacy quedan limpias.
3. No deben existir dos reuniones visibles para el mismo registro.

## Gate 9 — Privacidad
1. Dashboard del Evento solo debe ser operativo interno.
2. Cliente usa Portal Cliente y canal Cliente ↔ Planner.
3. Proveedor usa Portal Proveedor y canal Planner ↔ Proveedor.
4. Notas internas, costo proveedor y margen siguen privados.

## Gate 10 — Builder
Abrir Invitación > Builder y confirmar que funciona exactamente como antes.
