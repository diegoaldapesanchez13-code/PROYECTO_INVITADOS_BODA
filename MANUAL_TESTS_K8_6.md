# Pruebas manuales — K.8.6

Ejecutar después de `python scripts/verify_phase_k8_6.py`.

## 1. Workspace del Planner
1. Inicia sesión como Planner.
2. Abre un evento y entra a un `ServicioEvento` mediante **Abrir workspace**.
3. Baja a **K.8.6 · Operación vinculada**.
4. Deben existir: Tareas, Agenda/citas, Documentos, Finanzas del servicio y Vincular registros existentes.

## 2. Crear tarea vinculada
1. Crea `Confirmar montaje K86`.
2. Pon prioridad Alta y una fecha límite.
3. Recarga el workspace: debe seguir dentro del mismo servicio.
4. Abre el dashboard operativo normal del evento: la tarea debe seguir siendo una `TareaEvento` normal (no una copia de colaboración).

## 3. Crear cita / actividad
1. Crea `Prueba de montaje K86` con fecha y hora.
2. Debe aparecer en Agenda/citas del servicio.
3. Si el servicio tiene proveedor, la actividad debe quedar asociada automáticamente a ese proveedor.
4. Entra como proveedor: debe poder ver esa cita desde el workspace de su servicio, pero no Finanzas.

## 4. Documento y privacidad cliente
1. Como Planner sube un PDF llamado `Plano visible K86` y marca **Visible para cliente**.
2. Sube otro llamado `Documento interno K86` sin marcar la casilla.
3. Entra como cliente y abre el mismo servicio.
4. Debe ver `Plano visible K86` y NO `Documento interno K86`.

## 5. Gasto y pago
1. Como Planner crea un gasto `Upgrade floral K86`.
2. Registra un pago parcial con monto, método y, opcionalmente, comprobante.
3. El gasto debe mostrar total pagado y saldo.
4. Entra como cliente: NO debe aparecer el concepto del gasto, ni el pago, ni el bloque **Finanzas del servicio**.
5. Entra como proveedor: tampoco debe aparecer Finanzas.

## 6. Vincular un registro existente
1. Desde el dashboard normal crea una tarea del evento que todavía no tenga servicio.
2. Regresa al workspace y usa **Vincular registros existentes**.
3. Selecciona esa tarea.
4. Debe aparecer en Tareas sin haberse duplicado.
5. Pulsa **Desvincular**: debe desaparecer de ese servicio, pero la tarea debe seguir existiendo en el dashboard del evento.

## 7. Aislamiento entre eventos
No debe ser posible vincular desde este workspace registros pertenecientes a otro evento. Los desplegables solo deben listar registros del mismo evento.

## 8. Builder — smoke test
K.8.6 no toca Builder. Abre una invitación existente en el editor visual y confirma que carga igual que antes. No hace falta modificar ni guardar diseño para esta prueba.

## Gate manual
Aprobar K.8.6 solo si las pruebas 1–7 funcionan. La prueba 8 confirma que no hubo regresión visual accidental.
