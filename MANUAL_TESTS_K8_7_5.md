# Pruebas manuales — K.8.7.5 Provider Portal V3

1. Inicia sesión como proveedor y abre `/proveedor/dashboard/`.
2. La navegación debe ser **Inicio / Servicios / Cotizaciones / Agenda / Tareas / Documentos / Pagos**.
3. No debe existir **Respuesta operativa**, `ExpedienteServicio`, ni el bloque legacy de colaboración.
4. En Inicio deben aparecer solo acciones de sus propios servicios.
5. Crea una cotización con cambios solicitados por Planner. Debe aparecer **Enviar nueva cotización**.
6. Envía una nueva versión desde Cotizaciones; debe regresar al Portal Proveedor y crear la siguiente versión.
7. Comprueba que el proveedor no vea la propuesta enviada al cliente, cargo adicional, valor contratado ni precio final del cliente.
8. Crea una cita para ese proveedor. Debe poder **Confirmar / Reprogramar / No asistiré**.
9. Crea una tarea asignada al usuario proveedor y ligada a su servicio. Debe aparecer; una tarea del Planner no.
10. Desde Planner/Empresa, sube al servicio un documento con `Visible para proveedor = OFF`: el proveedor no debe verlo.
11. Activa `Visible para proveedor`: ahora sí debe verlo.
12. El proveedor sube un documento desde su portal; debe quedar ligado al ServicioEvento, `visible_proveedor=True` y `visible_cliente=False`.
13. Asigna un segundo proveedor al mismo evento. El primero no debe ver servicios, tareas, documentos, cotizaciones ni pagos del segundo.
14. Registra un `PagoClienteEvento` desde Portal Cliente. El proveedor NO debe verlo.
15. Registra un `GastoEvento` y `PagoEvento` de la empresa hacia el proveedor. Debe aparecer únicamente en **Pagos** del proveedor correspondiente.
16. Abre el workspace de un servicio. El proveedor solo debe tener canal **Planner ↔ Proveedor**, nunca Cliente ↔ Planner ni Interno.
17. En el workspace, un documento interno no compartido no debe aparecer al proveedor.
18. Revisa responsive en móvil: navegación horizontal, cards en una columna, agenda y cotizaciones utilizables.
19. Smoke test: Portal Cliente V3, Planner V3, Company V3 y Event Dashboard V3 siguen funcionando.
20. Smoke test Builder: abrirlo desde su flujo actual y confirmar que no cambió.
