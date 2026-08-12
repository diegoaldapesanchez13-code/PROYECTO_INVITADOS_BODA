# Pruebas manuales K.8.7.4.1
1. Cliente abre **Pagos** y reporta un pago general del evento con foto/PDF.
2. El pago queda **Pendiente de revisión**.
3. Planner/Empresa abre el Event Dashboard V3 → **Finanzas** y ve el comprobante.
4. Marca **Recibido** y agrega comentario.
5. Cliente vuelve a Pagos y ve **Recibido por empresa / planner** y el comentario.
6. Repite y marca **Observado**; debe aparecer al cliente como acción pendiente.
7. El proveedor no debe ver ningún bloque, botón ni dato de estos pagos.
8. Confirma que `PagoEvento`/egresos internos no cambian.
9. Prueba pago general y pago opcionalmente relacionado a un ServicioEvento.
10. Verifica miniatura de imagen y apertura de PDF.
