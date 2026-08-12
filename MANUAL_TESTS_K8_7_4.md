# Pruebas manuales — K.8.7.4 Client Portal V3

1. Inicia sesión como cliente y abre `/cliente/dashboard/`.
2. La navegación debe ser: **Inicio / Servicios / Agenda / Tareas / Documentos / Invitados / Invitación**.
3. No debe aparecer el bloque legacy **Solicitudes y propuestas** ni **Nueva solicitud**.
4. En Inicio, si no hay pendientes debe aparecer **Todo al día**.
5. Solicita desde un ServicioEvento una aprobación al cliente. Debe aparecer como **Aprobar decisión**.
6. Envía una propuesta al cliente. Debe aparecer como **Revisar propuesta**.
7. Crea una cita con ese cliente como participante. Debe aparecer como **Confirmar cita** y poder responder desde Agenda.
8. Confirma la cita desde el portal. Debe regresar al portal Cliente, no quedarse en el workspace.
9. Crea una cita de otro cliente del mismo evento. No debe aparecer al cliente actual.
10. Crea una tarea asignada al cliente. Debe aparecer en Tareas; una tarea del Planner no debe aparecer.
11. Crea un documento `visible_cliente=True` y otro `False`. Solo debe mostrarse el primero.
12. Crea una cotización del proveedor con un importe reconocible. Ese costo **no debe aparecer** ni en Portal Cliente ni al abrir el workspace Cliente ↔ Planner.
13. Crea una actividad operativa ligada a un servicio (ej. montaje interno). No debe aparecer automáticamente en Agenda del cliente.
14. Crea un HITO general del evento (ej. ceremonia). Sí debe aparecer en Agenda.
15. En Servicios, cada tarjeta debe abrir únicamente el canal **Cliente ↔ Planner**.
16. Comprueba que el cliente no pueda ver canales **Planner ↔ Proveedor** ni **Interno**.
17. Revisa responsive en móvil: cards en una columna, agenda legible y botones de confirmación utilizables.
18. Smoke test: Planner V3, Company V3 y Event Dashboard V3 deben seguir abriendo normalmente.
