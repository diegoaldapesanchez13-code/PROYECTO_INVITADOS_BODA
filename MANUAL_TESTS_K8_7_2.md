# Pruebas manuales — K.8.7.2 Planner Dashboard V3

1. Inicia sesión como Wedding Planner y abre su dashboard.
2. La navegación principal debe contener únicamente **Hoy / Trabajo / Mis eventos / Agenda**.
3. No debe existir un módulo independiente de Proveedores, ni formularios `Asignar proveedor` o `Guardar servicio`.
4. En **Trabajo**, confirma que existan tres columnas: **Cliente / Proveedor / Interno**.
5. Genera o usa una aprobación pendiente del cliente: debe aparecer en Cliente con texto entendible y responsable.
6. Genera o usa una cotización ENVIADA del proveedor: debe aparecer en Proveedor como `Revisar cotización del proveedor` y responsable Planner.
7. Una tarea asignada al Planner debe aparecer en Interno; si está vencida debe resaltarse.
8. Abre una acción Cliente y confirma que vaya al workspace con canal `CLIENTE_PLANNER`.
9. Abre una acción Proveedor y confirma que vaya al workspace con canal `PLANNER_PROVEEDOR`.
10. En **Mis eventos**, abre Servicios, Agenda y Tareas de un evento. Todos deben llevar al Event Dashboard V3, no a pantallas legacy.
11. Crea un evento desde `+ Nuevo evento`; debe quedar asignado al Planner y aparecer en Mis eventos.
12. Cambia el estado de un evento desde su tarjeta y confirma que se conserve.
13. En **Agenda**, valida que Citas estén separadas de Actividades/Hitos.
14. Una cita con cliente/proveedor pendiente debe aumentar los contadores de confirmaciones.
15. Cambia a otro Planner/tenant y confirma que no vea eventos, acciones, tareas o citas de la empresa anterior.
16. Smoke test: abre el Event Dashboard V3 y el Builder desde sus rutas normales; ambos deben seguir funcionando.
