# Pruebas manuales — K.8.7.6 Invitados + compartir desde Portal Cliente

1. Inicia sesión como cliente y abre **Invitados**.
2. Crea una invitación **Personal**. Debe crear automáticamente a la persona principal.
3. Crea una invitación **Familiar** con 2 personas y 1 acompañante extra.
4. Verifica que el total de lugares y disponibles respete `capacidad_contratada` del evento.
5. Intenta superar la capacidad contratada. El sistema debe rechazarlo sin crear la invitación.
6. En una familia, agrega una nueva persona y luego edita nombre/tipo/teléfono/correo.
7. Elimina una persona que todavía no tenga RSVP ni mesa. Debe eliminarse.
8. Marca una persona con RSVP y trata de eliminarla. Debe bloquearse.
9. Revisa una tarjeta de grupo: debe mostrar **Ver invitación / Copiar enlace / WhatsApp**.
10. Abre **Ver invitación** y confirma que use el UUID único de ese grupo.
11. Pulsa **Copiar enlace**. Debe copiar la URL individual.
12. Pulsa **WhatsApp**. Si hay teléfono, abre conversación con ese número; sin teléfono, abre selector genérico de WhatsApp.
13. Confirma que RSVP se muestre por persona como Confirmó / No asiste / Pendiente.
14. Edita acompañantes extra del grupo y valida que el roster se actualice.
15. No reduzcas acompañantes que ya tengan RSVP/mesa: debe bloquearse.
16. Entra como cliente de otro evento y confirma que no pueda editar ni borrar grupos del primero.
17. En **Mi invitación**, confirma que no exista botón `Editar en Builder`.
18. Smoke test: Portal Proveedor V3, Planner V3, Company V3 y Event Dashboard V3 siguen funcionando.
19. Smoke test Builder desde su flujo actual: debe abrir exactamente igual y no haber sido modificado.
