"""Reusable invitation runtime context.

Generic Text bindings do not expose invitation/group fields in the product UI
after J.1.2, but this context remains the canonical source for RSVP and backward
compatibility with documents that already stored INVITATION_GROUP bindings.
"""


def _guest_payload(invitado):
    effective_menu = invitado.menu_buffet_efectivo
    return {
        "id": invitado.id,
        "name": str(invitado),
        "attending": invitado.asistira,
        "personType": invitado.tipo_persona,
        "personTypeLabel": invitado.get_tipo_persona_display(),
        "menuType": effective_menu,
        "menuLabel": (
            "Menú infantil"
            if effective_menu == "INFANTIL"
            else "Menú adulto"
        ),
        "extraCompanion": invitado.es_acompanante_extra,
    }


def serializar_contexto_invitacion(
    grupo,
    invitados=None,
    *,
    include_guests=False,
):
    if grupo is None:
        data = {
            "invitationId": "",
            "groupName": "Invitación de ejemplo",
            "groupType": "",
            "groupTypeLabel": "Vista previa",
            "totalGuests": 0,
            "confirmedGuests": 0,
            "respondedGuests": 0,
            "pendingGuests": 0,
        }
        if include_guests:
            data["guests"] = []
        return data

    people = list(
        invitados
        if invitados is not None
        else grupo.invitados.all().order_by(
            "orden",
            "id",
        )
    )
    confirmed = sum(
        1
        for person in people
        if person.asistira is True
    )
    responded = sum(
        1
        for person in people
        if person.asistira is not None
    )

    data = {
        "invitationId": str(grupo.codigo),
        "groupName": grupo.nombre_grupo,
        "groupType": grupo.tipo,
        "groupTypeLabel": grupo.get_tipo_display(),
        "totalGuests": len(people),
        "confirmedGuests": confirmed,
        "respondedGuests": responded,
        "pendingGuests": len(people) - responded,
    }

    if include_guests:
        data["guests"] = [
            _guest_payload(person)
            for person in people
        ]

    return data
