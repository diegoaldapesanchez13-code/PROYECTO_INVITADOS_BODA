# Pruebas manuales K.8.4.1

1. Cliente: iniciar sesión y abrir `Portal Cliente > Servicios`. Deben aparecer los `ServicioEvento` del evento aunque no tengan `ExpedienteServicio` legacy. Abrir `Conversar` y confirmar que entra a `Cliente ↔ Planner`.
2. Cliente: confirmar que NO aparecen `Planner ↔ Proveedor` ni `Notas internas`.
3. Proveedor: confirmar que sigue entrando únicamente a `Planner ↔ Proveedor`.
4. Adjuntos: seleccionar 2 o más imágenes. Deben mostrarse miniaturas antes de enviar. Usar `×` para quitar una y confirmar que solo se envían las restantes.
5. Imagen enviada: debe verse como miniatura dentro del mensaje. PDF/documento debe verse como tarjeta compacta `PDF`/`FILE`.
6. Eliminación propia: cliente o proveedor puede eliminar un adjunto que él mismo envió. El archivo debe desaparecer del mensaje.
7. Seguridad: cliente/proveedor no debe poder eliminar adjuntos enviados por otra persona. Planner/operador sí puede retirar adjuntos del workspace.
8. Referencia protegida: guardar un adjunto como referencia e intentar eliminarlo. Debe impedirse y mostrar el aviso de que primero debe resolverse la referencia.
9. Privacidad referencias: una referencia creada desde `Planner ↔ Proveedor` no debe aparecer al cliente; una referencia de `Cliente ↔ Planner` no debe aparecer al proveedor.
