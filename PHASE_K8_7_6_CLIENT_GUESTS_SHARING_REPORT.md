# K.8.7.6 — Client Guests & Invitation Sharing

## Objetivo
Completar la gestión de invitados desde Portal Cliente sin depender del Builder.

## Fuente de verdad
Se reutilizan los modelos existentes:
- `Grupoinvitacion`: invitación/UUID/grupo.
- `Invitado`: persona real autorizada.

No se crea un segundo dominio de invitados.

## Funciones Cliente
- crear invitación personal;
- crear invitación familiar;
- agregar/editar/eliminar personas;
- gestionar acompañantes extra autorizados;
- ver RSVP por persona;
- ver capacidad contratada/disponible;
- abrir invitación UUID;
- copiar enlace;
- compartir por WhatsApp.

## Seguridad
- Cliente solo administra grupos de sus propios eventos.
- No se permite eliminar personas con RSVP o mesa.
- No se permite eliminar grupos con RSVP o personas asignadas a mesa.
- Si `capacidad_contratada > 0`, no se pueden crear lugares por encima del contrato.

## Compartir
La URL continúa siendo:
`/invitacion/<uuid>/`

Esto mantiene el compartir independiente del motor visual que renderice la invitación.

## Builder
No se modifica.
Portal Cliente no recibe acceso Builder en esta fase.
Los permisos/capacidades de Builder se implementarán en una fase posterior independiente.

## Migraciones
No requiere migraciones.
