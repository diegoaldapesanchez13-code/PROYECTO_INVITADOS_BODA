from dataclasses import dataclass

from django.core.exceptions import ValidationError

from invitaciones.models import Invitado


@dataclass(frozen=True)
class GuestCapacity:
    capacidad: int
    emitidos: int
    confirmados: int
    pendientes: int
    no_asisten: int
    reservados: int
    liberados: int
    disponibles: int | None
    sobrecupo: int

    def as_dict(self):
        return {
            "capacidad": self.capacidad,
            "emitidos": self.emitidos,
            "confirmados": self.confirmados,
            "pendientes": self.pendientes,
            "no_asisten": self.no_asisten,
            "reservados": self.reservados,
            "liberados": self.liberados,
            "disponibles": self.disponibles,
            "sobrecupo": self.sobrecupo,
        }


def capacidad_objetivo(evento):
    """
    Prefer contractual capacity. Fall back to estimated capacity.
    Zero means "no hard capacity configured".
    """
    return max(
        int(evento.capacidad_contratada or 0)
        or int(evento.numero_invitados_estimado or 0),
        0,
    )


def resumen_cupo_evento(evento, *, excluir_grupo=None):
    qs = Invitado.objects.filter(grupo__evento=evento)
    if excluir_grupo is not None:
        qs = qs.exclude(grupo=excluir_grupo)

    emitidos = qs.count()
    confirmados = qs.filter(asistira=True).count()
    no_asisten = qs.filter(asistira=False).count()
    pendientes = emitidos - confirmados - no_asisten

    # A "NO" remains a real person/invitation for history and visibility, but
    # does not reserve a seat anymore.
    reservados = confirmados + pendientes
    capacidad = capacidad_objetivo(evento)
    disponibles = max(capacidad - reservados, 0) if capacidad else None
    sobrecupo = max(reservados - capacidad, 0) if capacidad else 0

    return GuestCapacity(
        capacidad=capacidad,
        emitidos=emitidos,
        confirmados=confirmados,
        pendientes=pendientes,
        no_asisten=no_asisten,
        reservados=reservados,
        liberados=no_asisten,
        disponibles=disponibles,
        sobrecupo=sobrecupo,
    )


def validar_nuevos_lugares(evento, nueva_cantidad, *, excluir_grupo=None):
    nueva_cantidad = max(int(nueva_cantidad or 0), 0)
    resumen = resumen_cupo_evento(evento, excluir_grupo=excluir_grupo)
    if not resumen.capacidad:
        return resumen

    if resumen.reservados + nueva_cantidad > resumen.capacidad:
        disponibles = max(resumen.capacidad - resumen.reservados, 0)
        raise ValidationError(
            f"La capacidad configurada es de {resumen.capacidad} lugares. "
            f"Disponibles para nuevas invitaciones: {disponibles}."
        )
    return resumen
