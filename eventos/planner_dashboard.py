from collections import defaultdict
from datetime import date, datetime

from django.db.models import Q
from django.utils import timezone

from invitaciones.models import EventoBoda
from itinerario.models import ActividadItinerario
from tareas.models import TareaEvento


TERMINALES = {"FINALIZADO", "CANCELADO", "ARCHIVADO"}


def _fecha_evento(evento):
    valor = evento.fecha_inicio or evento.fecha_fiesta
    if not valor:
        return None
    if isinstance(valor, datetime):
        if timezone.is_aware(valor):
            valor = timezone.localtime(valor)
        return valor.date()
    if isinstance(valor, date):
        return valor
    return None


def construir_planner_home_k9(*, empresa, planner):
    """
    Planner Home is intentionally operational, not a reduced Company dashboard.

    It only consumes events assigned to the planner inside the selected tenant.
    """
    hoy = timezone.localdate()

    eventos = list(
        EventoBoda.objects.filter(
            empresa=empresa,
            wedding_planner=planner,
        )
        .exclude(estado="ARCHIVADO")
        .select_related("sede", "wedding_planner")
        .order_by("-fecha_creacion")
    )
    evento_ids = [evento.id for evento in eventos]

    tareas = list(
        TareaEvento.objects.filter(
            evento_id__in=evento_ids,
            responsable=planner,
            archivado_en__isnull=True,
        )
        .exclude(estado__in=["COMPLETADA", "CANCELADA"])
        .select_related("evento")
        .order_by("fecha_limite", "-prioridad", "id")
    )

    agenda = list(
        ActividadItinerario.objects.filter(
            evento_id__in=evento_ids,
            archivado_en__isnull=True,
            fecha__gte=hoy,
        )
        .exclude(estado="CANCELADA")
        .filter(
            Q(responsable=planner)
            | Q(participantes__usuario=planner)
            | Q(responsable__isnull=True)
        )
        .select_related("evento", "servicio_evento")
        .distinct()
        .order_by("fecha", "hora_inicio", "orden", "id")
    )

    eventos_cards = []
    for evento in eventos:
        fecha = _fecha_evento(evento)
        razones = []
        if evento.estado not in TERMINALES:
            if not fecha:
                razones.append("Fecha por definir")
            if not evento.sede_id:
                razones.append("Sin sede")
            if not evento.clientes.exists():
                razones.append("Sin cliente")

        tareas_evento = [t for t in tareas if t.evento_id == evento.id]
        vencidas = sum(1 for tarea in tareas_evento if tarea.esta_vencida)
        if vencidas:
            razones.append(f"{vencidas} tarea(s) vencida(s)")

        eventos_cards.append(
            {
                "evento": evento,
                "fecha": fecha,
                "atencion": razones,
                "tareas_pendientes": len(tareas_evento),
            }
        )

    activos = [
        item for item in eventos_cards
        if item["evento"].estado not in TERMINALES
    ]
    proximos = [
        item for item in activos
        if item["fecha"] and item["fecha"] >= hoy
    ]
    proximos.sort(key=lambda item: item["fecha"])

    tareas_hoy = [
        tarea for tarea in tareas
        if tarea.fecha_limite == hoy or tarea.fecha_inicio == hoy
    ]
    tareas_vencidas = [tarea for tarea in tareas if tarea.esta_vencida]
    atencion = [
        item for item in activos
        if item["atencion"]
    ]
    atencion.sort(key=lambda item: (-len(item["atencion"]), item["fecha"] or date.max))

    agenda_hoy = [actividad for actividad in agenda if actividad.fecha == hoy]

    return {
        "kpis": {
            "eventos": len(activos),
            "tareas_hoy": len(tareas_hoy),
            "tareas_vencidas": len(tareas_vencidas),
            "agenda_hoy": len(agenda_hoy),
        },
        "proximos_eventos": proximos[:5],
        "tareas_prioritarias": (tareas_vencidas + [
            tarea for tarea in tareas
            if tarea not in tareas_vencidas
        ])[:7],
        "agenda_proxima": agenda[:7],
        "requiere_atencion": atencion[:5],
        "eventos_recientes": activos[:6],
    }
