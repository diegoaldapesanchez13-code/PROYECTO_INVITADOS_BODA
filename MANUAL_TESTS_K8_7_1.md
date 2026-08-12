# Pruebas manuales K.8.7.1 — Event Dashboard V3

1. Abrir `/dashboard/?evento=<id>` y confirmar navegación: Resumen, Servicios, Agenda, Tareas, Finanzas, Documentos, Invitados, Invitación y Equipo (si aplica).
2. Resumen: confirmar que las alertas llevan al tab correcto y que no aparecen formularios de Banquete/Decoración/Música.
3. Servicios: abrir un ServicioEvento y confirmar que entra a su workspace K.8.4–K.8.6.
4. Crear un servicio manual desde el desplegable. Confirmar que aparece como nueva tarjeta y que no altera proveedores/catálogos maestros.
5. Agenda: confirmar que las actividades ligadas a ServicioEvento muestran el servicio y las generales muestran “Evento general”.
6. Tareas: confirmar responsable, fecha, estado y vínculo al servicio; una tarea general debe seguir visible sin servicio.
7. Finanzas: comprobar que Contrato base + extras/upgrades se muestran separados de gastos/pagos operativos. Comparar al menos un gasto real con sus pagos.
8. Documentos: un documento general debe aparecer en “Evento”; uno vinculado debe aparecer en “Servicios” y abrir su workspace.
9. Invitados: confirmar que el flujo existente de RSVP sigue funcionando y que Mesas abre su workspace especializado.
10. Invitación: “Abrir Builder” debe abrir exactamente el Builder actual; no debe haber cambios visuales o funcionales dentro del Builder.
11. Compatibilidad temporal: abrir “Contenido heredado” y “Operación heredada” y confirmar que las funciones antiguas siguen disponibles durante la transición.
12. Cambiar de evento en el selector y confirmar que ningún dato del evento anterior permanece en Servicios, Agenda, Tareas, Finanzas o Documentos.
