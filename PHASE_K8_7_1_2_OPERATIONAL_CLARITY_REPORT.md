# K.8.7.1.2 — Operational Clarity & Agenda

## Objetivo
Eliminar ambigüedad operativa antes de continuar con Planner Dashboard V3. Esta fase sustituye la compatibilidad visual legacy del Event Dashboard por una única navegación Event-Centric y formaliza la diferencia entre Tarea, Cita, Actividad e Hito.

## Cambios
- El Event Dashboard ya no incluye panels legacy.
- Cada ServicioEvento tiene card Cliente y card Proveedor con descripción de la acción y responsable.
- Se introduce `ActividadItinerario.tipo`: CITA / ACTIVIDAD / HITO.
- Se introduce `ParticipanteActividad` con confirmación individual.
- Crear una cita genera participantes Cliente/Planner/Colaborador y Proveedor del servicio.
- Cliente/Proveedor solo pueden responder su propia confirmación.
- Una tarea deja de ser tratada como cita aunque existan columnas legacy de hora.
- La migración convierte tareas antiguas con horario en citas y limpia las horas del registro de tarea.
- Agenda V3 separa `Próximas citas` de `Itinerario y actividades`.
- El Event Dashboard se reserva al equipo interno; cliente y proveedor son redirigidos a sus portales.
- El Event Dashboard deja de consultar/escribir Catering/Decoración/Entretenimiento legacy como dominios paralelos.

## Estrategia de eliminación
No se eliminan todavía tablas que otros dashboards legacy referencian. Eso no significa mantener compatibilidad funcional: quedan sin entrada desde Event Dashboard y se retirarán del esquema después de migrar los demás roles. Ver `LEGACY_RETIREMENT_MAP_K8_7_1_2.md`.

## Builder
Sin cambios.
