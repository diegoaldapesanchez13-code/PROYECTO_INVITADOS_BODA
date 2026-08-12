# Pruebas manuales — K.8.7.7 Collaboration UX & Planner Cleanup

1. Entra como Planner y abre un ServicioEvento → workspace.
2. Cambia entre **Cliente ↔ Planner / Planner ↔ Proveedor / Notas internas**.
3. Confirma que cada canal tenga una descripción clara de quién puede verlo.
4. Envía varios mensajes como Planner, Cliente y Proveedor. Los propios deben mostrarse visualmente a la derecha.
5. Adjunta imágenes/PDF y confirma que las miniaturas siguen funcionando.
6. Como Planner, elimina un mensaje individual sin referencias. Debe desaparecer.
7. Como Cliente/Proveedor, confirma que NO aparezca el botón de eliminar mensaje completo.
8. Promueve un adjunto a Referencia e intenta borrar su mensaje: debe bloquearse y pedir eliminar primero la referencia.
9. Desde la columna Referencias, elimina esa referencia y después elimina el mensaje.
10. Crea mensajes en Cliente↔Planner y Planner↔Proveedor.
11. En Cliente↔Planner usa **Herramientas del Planner → Vaciar historial de este canal**.
12. Solo Cliente↔Planner debe quedar vacío; Planner↔Proveedor debe conservar sus mensajes.
13. Antes de limpiar, registra una Decisión estructurada vinculada a un mensaje. Después de limpiar, la Decisión debe seguir existiendo.
14. Confirma que las referencias originadas en el canal limpiado sí desaparezcan.
15. Crea un Tema, úsalo en un mensaje y pulsa `×` para archivarlo. El mensaje debe permanecer.
16. Entra como Cliente: solo ve Cliente↔Planner, sin herramientas destructivas.
17. Entra como Proveedor: solo ve Planner↔Proveedor, sin herramientas destructivas.
18. En móvil confirma que chat, composer, adjuntos, herramientas y referencias sean utilizables.
19. Prueba Ctrl+Enter (o Cmd+Enter) en el textarea: debe enviar; Enter normal debe crear nueva línea.
20. Smoke test Portal Cliente, Portal Proveedor, Planner V3 y Event Dashboard V3.
