from collections import defaultdict

from django.utils import timezone

from documentos.models import DocumentoEvento
from itinerario.models import ActividadItinerario
from proveedores.models import ServicioEvento
from tareas.models import TareaEvento


def _safe_count(queryset):
    try:
        return queryset.count()
    except Exception:
        return 0


def construir_resumen_workspace(*, evento, user):
    """
    Read-only operational snapshot for the Event Workspace.

    R4A intentionally avoids mutating or recalculating contract truth. It only
    summarizes existing operational data and highlights missing setup.
    """
    hoy = timezone.localdate()

    tareas_qs = TareaEvento.objects.filter(
        evento=evento,
        archivado_en__isnull=True,
    ).exclude(estado__in=["COMPLETADA", "CANCELADA"])

    servicios_qs = ServicioEvento.objects.filter(
        evento=evento,
        archivado_en__isnull=True,
    ).exclude(estado_operativo="CANCELADO")

    agenda_qs = ActividadItinerario.objects.filter(
        evento=evento,
        archivado_en__isnull=True,
        fecha__gte=hoy,
    ).exclude(estado="CANCELADA")

    documentos_qs = DocumentoEvento.objects.filter(
        evento=evento,
        archivado_en__isnull=True,
    )

    tareas = list(tareas_qs)
    servicios = list(servicios_qs.select_related("proveedor"))
    agenda = list(
        agenda_qs.order_by("fecha", "hora_inicio", "orden", "id")[:5]
    )

    tareas_vencidas = [t for t in tareas if t.esta_vencida]
    servicios_sin_proveedor = [
        s for s in servicios
        if s.prestacion_tipo == "PROVEEDOR" and not s.proveedor_id
    ]

    checklist = [
        {
            "key": "fecha",
            "label": "Fecha del evento",
            "done": bool(evento.fecha_inicio or evento.fecha_fiesta),
            "detail": (
                (evento.fecha_inicio or evento.fecha_fiesta).strftime("%d %b %Y")
                if (evento.fecha_inicio or evento.fecha_fiesta)
                else "Por definir"
            ),
        },
        {
            "key": "sede",
            "label": "Sede",
            "done": bool(evento.sede_id),
            "detail": evento.sede.nombre if evento.sede_id else "Por definir",
        },
        {
            "key": "planner",
            "label": "Planner responsable",
            "done": bool(evento.wedding_planner_id),
            "detail": (
                evento.wedding_planner.get_full_name().strip()
                or evento.wedding_planner.username
                if evento.wedding_planner_id
                else "Por definir"
            ),
        },
        {
            "key": "cliente",
            "label": "Cliente",
            "done": evento.clientes.exists(),
            "detail": (
                (
                    evento.clientes.first().get_full_name().strip()
                    or evento.clientes.first().username
                )
                if evento.clientes.exists()
                else "Por definir"
            ),
        },
    ]

    alertas = []
    if tareas_vencidas:
        alertas.append({
            "level": "danger",
            "title": f"{len(tareas_vencidas)} tarea(s) vencida(s)",
            "text": "Revisa prioridades y fechas límite.",
        })
    if servicios_sin_proveedor:
        alertas.append({
            "level": "warning",
            "title": f"{len(servicios_sin_proveedor)} servicio(s) sin proveedor",
            "text": "Aún requieren asignación operativa.",
        })
    pendientes_setup = sum(1 for item in checklist if not item["done"])
    if pendientes_setup:
        alertas.append({
            "level": "info",
            "title": f"{pendientes_setup} dato(s) general(es) por completar",
            "text": "Puedes seguir trabajando aunque todavía estén por definir.",
        })

    return {
        "workspace_kpis": {
            "tareas_pendientes": len(tareas),
            "tareas_vencidas": len(tareas_vencidas),
            "servicios_activos": len(servicios),
            "agenda_proxima": _safe_count(agenda_qs),
            "documentos": _safe_count(documentos_qs),
        },
        "workspace_checklist": checklist,
        "workspace_alertas": alertas,
        "workspace_agenda": agenda,
        "workspace_tareas": sorted(
            tareas,
            key=lambda t: (
                0 if t.esta_vencida else 1,
                t.fecha_limite or timezone.localdate().replace(year=9999),
                t.id,
            ),
        )[:5],
        "workspace_servicios_sin_proveedor": servicios_sin_proveedor[:5],
        "workspace_progress": round(
            (sum(1 for item in checklist if item["done"]) / len(checklist)) * 100
        ) if checklist else 0,
    }
