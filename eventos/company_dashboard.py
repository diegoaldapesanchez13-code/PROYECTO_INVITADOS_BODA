from collections import defaultdict
from datetime import date, datetime

from django.utils import timezone

from invitaciones.models import EventoBoda
from proveedores.models import ServicioEvento
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


def construir_dashboard_empresa_k9(*, empresa):
    eventos = list(
        EventoBoda.objects.filter(empresa=empresa)
        .select_related("sede", "wedding_planner")
        .prefetch_related("clientes")
        .order_by("-fecha_creacion")
    )
    ids = [e.id for e in eventos]
    hoy = timezone.localdate()

    tareas = list(
        TareaEvento.objects.filter(evento_id__in=ids, archivado_en__isnull=True)
        .exclude(estado__in=["COMPLETADA", "CANCELADA"])
        .select_related("evento")
    )
    servicios = list(
        ServicioEvento.objects.filter(evento_id__in=ids, archivado_en__isnull=True)
        .exclude(estado_operativo="CANCELADO")
        .select_related("evento", "proveedor")
    )

    tareas_evento = defaultdict(list)
    for tarea in tareas:
        tareas_evento[tarea.evento_id].append(tarea)

    servicios_evento = defaultdict(list)
    for servicio in servicios:
        servicios_evento[servicio.evento_id].append(servicio)

    cards = []
    for evento in eventos:
        fecha = _fecha_evento(evento)
        t_evento = tareas_evento[evento.id]
        s_evento = servicios_evento[evento.id]

        razones = []
        if evento.estado not in TERMINALES:
            if not fecha:
                razones.append("Fecha por definir")
            if not evento.wedding_planner_id:
                razones.append("Sin planner")
            if not evento.sede_id:
                razones.append("Sin sede")
            if not evento.clientes.exists():
                razones.append("Sin cliente")

        vencidas = sum(1 for tarea in t_evento if tarea.esta_vencida)
        if vencidas:
            razones.append(f"{vencidas} tarea(s) vencida(s)")

        sin_proveedor = sum(
            1 for servicio in s_evento
            if servicio.prestacion_tipo == "PROVEEDOR" and not servicio.proveedor_id
        )
        if sin_proveedor:
            razones.append(f"{sin_proveedor} servicio(s) sin proveedor")

        cards.append({
            "evento": evento,
            "fecha": fecha,
            "tareas_pendientes": len(t_evento),
            "servicios": len(s_evento),
            "razones_atencion": razones,
            "atencion": len(razones),
        })

    activos = [c for c in cards if c["evento"].estado not in TERMINALES and c["evento"].estado != "BORRADOR"]
    borradores = [c for c in cards if c["evento"].estado == "BORRADOR"]
    proximos = [
        c for c in cards
        if c["evento"].estado not in TERMINALES and c["fecha"] and c["fecha"] >= hoy
    ]
    proximos.sort(key=lambda c: c["fecha"])
    atencion = [c for c in cards if c["atencion"] and c["evento"].estado not in TERMINALES]
    atencion.sort(key=lambda c: (-c["atencion"], c["fecha"] or date.max))

    recientes = [c for c in cards if c["evento"].estado != "ARCHIVADO"][:8]

    return {
        "kpis": {
            "activos": len(activos),
            "proximos": len(proximos),
            "borradores": len(borradores),
            "atencion": len(atencion),
        },
        "proximos": proximos[:5],
        "atencion": atencion[:6],
        "recientes": recientes,
    }
