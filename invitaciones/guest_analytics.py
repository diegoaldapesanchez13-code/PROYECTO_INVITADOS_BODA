"""Guest analytics V2.

R.4 centralizes event-level guest metrics around Invitado.

Source of truth:
- Invitado = attendance / person / buffet decision.
- Grupoinvitacion = grouping and UUID metadata.

Legacy group RSVP fields remain compatibility-only.
"""


def _effective_menu(invitado):
    if invitado.menu_asignado == "ADULTO":
        return "ADULTO"
    if invitado.menu_asignado == "INFANTIL":
        return "INFANTIL"
    return "INFANTIL" if invitado.tipo_persona == "NINO" else "ADULTO"


def resumen_invitados_evento(evento, *, incluir_mesas=False):
    """Return canonical RSVP and buffet metrics for one event."""
    if evento is None:
        return {
            "total_personas": 0,
            "confirmados": 0,
            "no_asisten": 0,
            "pendientes": 0,
            "porcentaje_asistencia": 0,
            "adultos_persona": 0,
            "ninos_persona": 0,
            "adultos_confirmados_persona": 0,
            "ninos_confirmados_persona": 0,
            "buffet_adultos": 0,
            "buffet_infantiles": 0,
            "confirmados_sin_mesa": 0,
        }

    from .models import Invitado

    invitados = list(
        Invitado.objects
        .filter(grupo__evento=evento)
        .select_related("grupo")
        .order_by("grupo_id", "orden", "id")
    )

    total = len(invitados)
    confirmados = [
        invitado
        for invitado in invitados
        if invitado.asistira is True
    ]
    no_asisten = sum(
        1
        for invitado in invitados
        if invitado.asistira is False
    )
    pendientes = total - len(confirmados) - no_asisten

    adultos_persona = sum(
        1
        for invitado in invitados
        if invitado.tipo_persona == "ADULTO"
    )
    ninos_persona = sum(
        1
        for invitado in invitados
        if invitado.tipo_persona == "NINO"
    )
    adultos_confirmados_persona = sum(
        1
        for invitado in confirmados
        if invitado.tipo_persona == "ADULTO"
    )
    ninos_confirmados_persona = sum(
        1
        for invitado in confirmados
        if invitado.tipo_persona == "NINO"
    )

    buffet_adultos = sum(
        1
        for invitado in confirmados
        if _effective_menu(invitado) == "ADULTO"
    )
    buffet_infantiles = len(confirmados) - buffet_adultos

    porcentaje = (
        round((len(confirmados) / total) * 100, 2)
        if total
        else 0
    )

    confirmados_sin_mesa = 0
    if incluir_mesas and confirmados:
        confirmados_sin_mesa = _confirmados_sin_mesa(
            confirmados
        )

    return {
        "total_personas": total,
        "confirmados": len(confirmados),
        "no_asisten": no_asisten,
        "pendientes": pendientes,
        "porcentaje_asistencia": porcentaje,
        "adultos_persona": adultos_persona,
        "ninos_persona": ninos_persona,
        "adultos_confirmados_persona": adultos_confirmados_persona,
        "ninos_confirmados_persona": ninos_confirmados_persona,
        "buffet_adultos": buffet_adultos,
        "buffet_infantiles": buffet_infantiles,
        "confirmados_sin_mesa": confirmados_sin_mesa,
    }


def resumen_invitados_eventos(eventos):
    """Canonical aggregate RSVP metrics for a visible event queryset."""
    from .models import Invitado

    event_ids = list(eventos.values_list("id", flat=True))
    if not event_ids:
        return {
            "confirmados": 0,
            "pendientes": 0,
            "no_asisten": 0,
            "total_personas": 0,
        }

    qs = Invitado.objects.filter(
        grupo__evento_id__in=event_ids
    )
    total = qs.count()
    confirmados = qs.filter(asistira=True).count()
    no_asisten = qs.filter(asistira=False).count()

    return {
        "total_personas": total,
        "confirmados": confirmados,
        "no_asisten": no_asisten,
        "pendientes": total - confirmados - no_asisten,
    }


def _confirmados_sin_mesa(confirmados):
    """Count confirmed people that do not have an individual table assignment."""
    from mesas.models import AsignacionMesa

    ids = [
        invitado.id
        for invitado in confirmados
    ]
    asignados = set(
        AsignacionMesa.objects
        .filter(invitado_id__in=ids)
        .values_list('invitado_id', flat=True)
    )
    return sum(
        1
        for invitado in confirmados
        if invitado.id not in asignados
    )
