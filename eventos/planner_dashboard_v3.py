from collections import defaultdict
from datetime import timedelta

from django.utils import timezone

from colaboracion.models import AprobacionServicio, CotizacionServicio, PropuestaServicioCliente
from eventos.dashboard_v3 import _enriquecer_servicios
from itinerario.models import ActividadItinerario, ParticipanteActividad
from presupuesto.models import GastoEvento
from proveedores.models import ServicioEvento
from tareas.models import TareaEvento


PRIORIDAD_NIVEL = {
    "danger": 0,
    "warning": 1,
    "info": 2,
    "success": 3,
}


def _fecha_evento_local(evento):
    fecha = getattr(evento, "fecha_fiesta", None)
    if not fecha:
        return None
    if hasattr(fecha, "date"):
        return timezone.localtime(fecha).date() if timezone.is_aware(fecha) else fecha.date()
    return fecha


def _accion_servicio(servicio, lado, accion):
    canal = "CLIENTE_PLANNER" if lado == "CLIENTE" else "PLANNER_PROVEEDOR"
    return {
        "tipo": "SERVICIO",
        "lado": lado,
        "nivel": accion["nivel"],
        "titulo": accion["titulo"],
        "detalle": accion["detalle"],
        "responsable": accion["responsable"],
        "evento": servicio.evento,
        "servicio": servicio,
        "canal": canal,
        "fecha": None,
    }


def _accion_tarea(tarea):
    nivel = "danger" if tarea.esta_vencida else ("warning" if tarea.fecha_limite == timezone.localdate() else "info")
    detalle = "Sin fecha límite"
    if tarea.fecha_limite:
        detalle = f"Vence {tarea.fecha_limite:%d/%m/%Y}"
    return {
        "tipo": "TAREA",
        "lado": "INTERNO",
        "nivel": nivel,
        "titulo": tarea.titulo,
        "detalle": detalle,
        "responsable": "Planner",
        "evento": tarea.evento,
        "servicio": tarea.servicio_evento,
        "tarea": tarea,
        "fecha": tarea.fecha_limite,
    }


def _accion_gasto(gasto):
    return {
        "tipo": "FINANZAS",
        "lado": "INTERNO",
        "nivel": "danger",
        "titulo": f"Pago vencido · {gasto.concepto}",
        "detalle": f"Saldo ${gasto.saldo_pendiente:,.2f}",
        "responsable": "Planner",
        "evento": gasto.evento,
        "servicio": gasto.servicio_evento,
        "gasto": gasto,
        "fecha": gasto.fecha_limite,
    }


def _orden_accion(item):
    fecha = item.get("fecha") or timezone.localdate() + timedelta(days=3650)
    return (PRIORIDAD_NIVEL.get(item.get("nivel"), 9), fecha, item.get("titulo", ""))


def construir_contexto_dashboard_planner_v3(*, eventos, planner, empresa):
    """Bandeja de trabajo Event-Centric para Wedding Planner.

    No usa ExpedienteServicio ni CRUD financiero paralelo.
    de proveedores. El Planner coordina y abre Evento/ServicioEvento.
    """
    eventos = list(eventos)
    hoy = timezone.localdate()
    ahora = timezone.now()
    evento_ids = [e.id for e in eventos]

    servicios = list(
        ServicioEvento.objects.filter(evento_id__in=evento_ids)
        .select_related("evento", "proveedor")
        .order_by("evento__fecha_fiesta", "nombre_servicio")
    )
    _enriquecer_servicios(servicios, None, hoy)

    acciones_cliente = []
    acciones_proveedor = []
    for servicio in servicios:
        if servicio.cliente_accion_v3:
            acciones_cliente.append(_accion_servicio(servicio, "CLIENTE", servicio.cliente_accion_v3))
        if servicio.proveedor_accion_v3:
            acciones_proveedor.append(_accion_servicio(servicio, "PROVEEDOR", servicio.proveedor_accion_v3))

    tareas = list(
        TareaEvento.objects.filter(
            evento_id__in=evento_ids,
            responsable=planner,
        )
        .exclude(estado__in=["COMPLETADA", "CANCELADA"])
        .select_related("evento", "servicio_evento")
        .order_by("fecha_limite", "prioridad", "titulo")
    )
    tareas_vencidas = [t for t in tareas if t.esta_vencida]
    tareas_hoy = [t for t in tareas if t.fecha_limite == hoy]

    gastos = list(
        GastoEvento.objects.filter(evento_id__in=evento_ids)
        .exclude(estado="CANCELADO")
        .select_related("evento", "servicio_evento", "proveedor")
        .order_by("fecha_limite", "concepto")
    )
    gastos_vencidos = [g for g in gastos if g.esta_vencido]

    acciones_internas = [_accion_tarea(t) for t in tareas]
    acciones_internas.extend(_accion_gasto(g) for g in gastos_vencidos)

    actividades = list(
        ActividadItinerario.objects.filter(
            evento_id__in=evento_ids,
            fecha__gte=hoy,
        )
        .exclude(estado__in=["COMPLETADA", "CANCELADA"])
        .select_related("evento", "servicio_evento", "proveedor", "responsable")
        .prefetch_related("participantes__usuario", "participantes__proveedor")
        .order_by("fecha", "hora_inicio", "orden")
    )
    citas = [a for a in actividades if a.tipo == "CITA"]
    actividades_operativas = [a for a in actividades if a.tipo in {"ACTIVIDAD", "HITO"}]
    citas_pendientes = [c for c in citas if c.confirmaciones_pendientes]
    citas_hoy = [c for c in citas if c.fecha == hoy]
    actividades_hoy = [a for a in actividades_operativas if a.fecha == hoy]

    participaciones_pendientes = list(
        ParticipanteActividad.objects.filter(
            actividad__evento_id__in=evento_ids,
            actividad__tipo="CITA",
            actividad__fecha__gte=hoy,
            requerido=True,
            estado="PENDIENTE",
        )
        .select_related("actividad", "actividad__evento", "actividad__servicio_evento", "usuario", "proveedor")
        .order_by("actividad__fecha", "actividad__hora_inicio", "rol", "id")
    )

    pendientes_cliente = sum(1 for p in participaciones_pendientes if p.rol == "CLIENTE")
    pendientes_proveedor = sum(1 for p in participaciones_pendientes if p.rol == "PROVEEDOR")

    todas_acciones = sorted(
        acciones_cliente + acciones_proveedor + acciones_internas,
        key=_orden_accion,
    )

    # Métricas por evento para las tarjetas de directorio.
    servicios_por_evento = defaultdict(list)
    for servicio in servicios:
        servicios_por_evento[servicio.evento_id].append(servicio)

    tareas_por_evento = defaultdict(list)
    for tarea in tareas:
        tareas_por_evento[tarea.evento_id].append(tarea)

    citas_por_evento = defaultdict(list)
    for cita in citas:
        citas_por_evento[cita.evento_id].append(cita)

    acciones_por_evento = defaultdict(int)
    for accion in acciones_cliente + acciones_proveedor:
        acciones_por_evento[accion["evento"].id] += 1
    for accion in acciones_internas:
        acciones_por_evento[accion["evento"].id] += 1

    eventos_cards = []
    for evento in eventos:
        fecha = _fecha_evento_local(evento)
        proximas_citas_evento = citas_por_evento.get(evento.id, [])
        eventos_cards.append({
            "evento": evento,
            "fecha_local": fecha,
            "servicios": len(servicios_por_evento.get(evento.id, [])),
            "acciones": acciones_por_evento.get(evento.id, 0),
            "tareas": len(tareas_por_evento.get(evento.id, [])),
            "tareas_vencidas": sum(1 for t in tareas_por_evento.get(evento.id, []) if t.esta_vencida),
            "citas_pendientes": sum(c.confirmaciones_pendientes for c in proximas_citas_evento),
            "proxima_cita": proximas_citas_evento[0] if proximas_citas_evento else None,
        })

    proximos_eventos = []
    for evento in eventos:
        fecha = getattr(evento, "fecha_fiesta", None)
        if not fecha:
            continue
        if hasattr(fecha, "date"):
            if fecha >= ahora:
                proximos_eventos.append(evento)
        elif fecha >= hoy:
            proximos_eventos.append(evento)
    proximos_eventos.sort(key=lambda e: e.fecha_fiesta)
    proximo_evento = proximos_eventos[0] if proximos_eventos else None

    eventos_activos = sum(1 for e in eventos if getattr(e, "activo", True))
    acciones_criticas = sum(1 for a in todas_acciones if a["nivel"] == "danger")

    return {
        "planner_v3": True,
        "planner_eventos_cards_v3": eventos_cards,
        "planner_eventos_activos_v3": eventos_activos,
        "planner_proximo_evento_v3": proximo_evento,
        "planner_proximos_eventos_v3": proximos_eventos[:6],
        "planner_acciones_cliente_v3": sorted(acciones_cliente, key=_orden_accion),
        "planner_acciones_proveedor_v3": sorted(acciones_proveedor, key=_orden_accion),
        "planner_acciones_internas_v3": sorted(acciones_internas, key=_orden_accion),
        "planner_acciones_v3": todas_acciones,
        "planner_acciones_criticas_v3": acciones_criticas,
        "planner_tareas_v3": tareas,
        "planner_tareas_vencidas_v3": tareas_vencidas,
        "planner_tareas_hoy_v3": tareas_hoy,
        "planner_citas_v3": citas[:20],
        "planner_citas_hoy_v3": citas_hoy,
        "planner_citas_pendientes_v3": citas_pendientes,
        "planner_actividades_v3": actividades_operativas[:20],
        "planner_actividades_hoy_v3": actividades_hoy,
        "planner_confirmaciones_cliente_v3": pendientes_cliente,
        "planner_confirmaciones_proveedor_v3": pendientes_proveedor,
        "planner_confirmaciones_pendientes_v3": len(participaciones_pendientes),
        "planner_gastos_vencidos_v3": gastos_vencidos,
        "planner_hoy_tiene_trabajo_v3": bool(tareas_hoy or citas_hoy or actividades_hoy),
    }
