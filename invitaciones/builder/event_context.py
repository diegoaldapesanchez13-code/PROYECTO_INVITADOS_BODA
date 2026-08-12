"""Runtime event context for Builder data bindings.

J.1.2 exposes generic participant names in the Builder UI so the same template
works for weddings, XV, baptisms and other events. Legacy bride/groom keys are
kept in the runtime context only for documents created before this phase.
"""

from datetime import timezone as datetime_timezone

from django.utils import timezone


def _iso(value):
    if value is None:
        return None
    if timezone.is_naive(value):
        value = timezone.make_aware(
            value,
            timezone.get_current_timezone(),
        )
    return (
        value
        .astimezone(datetime_timezone.utc)
        .isoformat()
    )


def _local(value):
    if value is None:
        return None
    if timezone.is_naive(value):
        value = timezone.make_aware(
            value,
            timezone.get_current_timezone(),
        )
    return timezone.localtime(value)


def _date_text(value):
    local = _local(value)
    return local.strftime("%d/%m/%Y") if local else ""


def _time_text(value):
    local = _local(value)
    return local.strftime("%H:%M") if local else ""


def serializar_contexto_evento(evento):
    ceremony = getattr(
        evento,
        "fecha_misa",
        None,
    )
    reception = getattr(
        evento,
        "fecha_fiesta",
        None,
    )
    available = [
        value
        for value in (
            ceremony,
            reception,
        )
        if value is not None
    ]
    event_start = (
        min(available)
        if available
        else None
    )

    primary = str(
        evento.participante_principal
        or ""
    ).strip()
    secondary = str(
        evento.participante_secundario
        or ""
    ).strip()
    participant_names = " & ".join(
        value
        for value in (
            primary,
            secondary,
        )
        if value
    )

    legacy_groom = str(
        getattr(evento, "novio", "")
        or ""
    ).strip()
    legacy_bride = str(
        getattr(evento, "novia", "")
        or ""
    ).strip()

    return {
        "eventId": evento.id,
        "eventName": str(
            getattr(evento, "nombre_evento", "")
            or str(evento)
        ),
        "primaryName": primary,
        "secondaryName": secondary,
        "participantNames": participant_names,
        "ceremonyPlace": str(
            getattr(evento, "lugar_misa", "")
            or ""
        ),
        "receptionPlace": str(
            getattr(evento, "lugar_fiesta", "")
            or ""
        ),
        "eventDate": _iso(event_start),
        "ceremonyDate": _iso(ceremony),
        "receptionDate": _iso(reception),
        "ceremonyDateText": _date_text(ceremony),
        "ceremonyTimeText": _time_text(ceremony),
        "receptionDateText": _date_text(reception),
        "receptionTimeText": _time_text(reception),

        # Backward compatibility only. No longer exposed in the Inspector.
        "groomName": legacy_groom,
        "brideName": legacy_bride,
        "coupleNames": " & ".join(
            value
            for value in (
                legacy_groom,
                legacy_bride,
            )
            if value
        ),
    }
