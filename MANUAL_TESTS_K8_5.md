# Pruebas manuales K.8.5

Ejecutar despues de `py manage.py migrate` y `python scripts/verify_phase_k8_5.py`.

1. **Planner / decision:** abrir un ServicioEvento > Workspace, registrar una decision. Debe quedar en Decisiones y no crear otro servicio ni expediente.
2. **Proveedor / privacidad:** entrar como proveedor. Debe ver su canal y Cotizaciones, pero **no** Propuestas al cliente, Aprobaciones del cliente ni Notas internas.
3. **Proveedor / cotizacion:** enviar una cotizacion de prueba. Enviar otra; debe aparecer como v2 y la anterior quedar historica/reemplazada cuando corresponda.
4. **Planner / cotizacion:** aceptar una cotizacion. Confirmar que queda Aceptada. El costo proveedor del ServicioEvento se actualiza con el costo aceptado.
5. **Planner / propuesta:** crear una propuesta al cliente indicando INCLUIDO, UPGRADE o ADICIONAL y el cargo adicional real.
6. **Cliente / privacidad:** entrar como cliente. Debe ver Propuestas y Aprobaciones, pero **nunca** el costo de las cotizaciones del proveedor ni el canal Planner-Proveedor.
7. **Cliente / propuesta:** aprobar una propuesta UPGRADE de prueba. Debe quedar Aprobada y actualizar modalidad/cargo adicional del ServicioEvento.
8. **Planner / aprobacion:** solicitar una aprobacion (ej. "Aprobar centro de mesa").
9. **Cliente / aprobacion:** responder Aprobar / Pedir cambios / Rechazar. La respuesta debe quedar trazada con usuario y fecha.
10. **Regresion K.8.4.1:** enviar imagen, verla como miniatura, quitarla antes de enviar y eliminar un adjunto propio despues de enviar.

No avanzar si el cliente ve costos de proveedor o si el proveedor ve propuestas/aprobaciones privadas del cliente.
