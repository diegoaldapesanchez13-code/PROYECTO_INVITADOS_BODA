from collections import defaultdict

from django.utils import timezone

from eventos.dashboard_v3 import _enriquecer_servicios
from itinerario.models import ActividadItinerario, ParticipanteActividad
from proveedores.models import ServicioEvento
from tareas.models import TareaEvento


def _fecha_local(evento):
    fecha = getattr(evento, "fecha_fiesta", None)
    if not fecha:
        return None
    if hasattr(fecha, "date"):
        if timezone.is_aware(fecha):
            return timezone.localtime(fecha).date()
        return fecha.date()
    return fecha


def construir_contexto_dashboard_empresa_v3(*, empresa, eventos):
    """Resumen ejecutivo de empresa basado en Evento/ServicioEvento.

    La empresa administra recursos maestros y abre cada Evento para operarlo.
    Este contexto no usa ExpedienteServicio ni módulos operativos legacy.
    """
    eventos = list(eventos)
    hoy = timezone.localdate()
    evento_ids = [evento.id for evento in eventos]

    servicios = list(
        ServicioEvento.objects.filter(evento_id__in=evento_ids)
        .select_related("evento", "proveedor")
        .order_by("evento__fecha_fiesta", "nombre_servicio")
    )
    _enriquecer_servicios(servicios, None, hoy)

    tareas = list(
        TareaEvento.objects.filter(evento_id__in=evento_ids)
        .exclude(estado__in=["COMPLETADA", "CANCELADA"])
        .select_related("evento", "servicio_evento", "responsable")
        .order_by("fecha_limite", "prioridad", "titulo")
    )
    tareas_vencidas = [tarea for tarea in tareas if tarea.esta_vencida]

    citas = list(
        ActividadItinerario.objects.filter(
            evento_id__in=evento_ids,
            tipo="CITA",
            fecha__gte=hoy,
        )
        .exclude(estado__in=["COMPLETADA", "CANCELADA"])
        .select_related("evento", "servicio_evento", "proveedor")
        .prefetch_related("participantes")
        .order_by("fecha", "hora_inicio", "orden")
    )

    participaciones_pendientes = list(
        ParticipanteActividad.objects.filter(
            actividad__evento_id__in=evento_ids,
            actividad__tipo="CITA",
            actividad__fecha__gte=hoy,
            requerido=True,
            estado="PENDIENTE",
        ).select_related("actividad", "actividad__evento")
    )

    servicios_por_evento = defaultdict(list)
    cliente_por_evento = defaultdict(int)
    proveedor_por_evento = defaultdict(int)
    for servicio in servicios:
        servicios_por_evento[servicio.evento_id].append(servicio)
        if servicio.cliente_accion_v3:
            cliente_por_evento[servicio.evento_id] += 1
        if servicio.proveedor_accion_v3:
            proveedor_por_evento[servicio.evento_id] += 1

    tareas_por_evento = defaultdict(list)
    for tarea in tareas:
        tareas_por_evento[tarea.evento_id].append(tarea)

    citas_por_evento = defaultdict(list)
    for cita in citas:
        citas_por_evento[cita.evento_id].append(cita)

    confirmaciones_por_evento = defaultdict(int)
    for participante in participaciones_pendientes:
        confirmaciones_por_evento[participante.actividad.evento_id] += 1

    cards = []
    for evento in eventos:
        tareas_evento = tareas_por_evento.get(evento.id, [])
        citas_evento = citas_por_evento.get(evento.id, [])
        acciones_cliente = cliente_por_evento.get(evento.id, 0)
        acciones_proveedor = proveedor_por_evento.get(evento.id, 0)
        vencidas = sum(1 for tarea in tareas_evento if tarea.esta_vencida)
        confirmaciones = confirmaciones_por_evento.get(evento.id, 0)
        atencion = acciones_cliente + acciones_proveedor + vencidas + confirmaciones
        cards.append({
            "evento": evento,
            "fecha_local": _fecha_local(evento),
            "servicios": len(servicios_por_evento.get(evento.id, [])),
            "acciones_cliente": acciones_cliente,
            "acciones_proveedor": acciones_proveedor,
            "tareas_pendientes": len(tareas_evento),
            "tareas_vencidas": vencidas,
            "citas": len(citas_evento),
            "confirmaciones_pendientes": confirmaciones,
            "atencion": atencion,
        })

    cards.sort(key=lambda item: (
        0 if item["evento"].activo else 1,
        item["fecha_local"] or timezone.localdate().replace(year=9999),
        str(item["evento"]),
    ))

    acciones_cliente = [s for s in servicios if s.cliente_accion_v3]
    acciones_proveedor = [s for s in servicios if s.proveedor_accion_v3]
    eventos_sin_planner = [e for e in eventos if e.activo and not e.wedding_planner_id]

    return {
        "empresa_v3": True,
        "empresa_eventos_cards_v3": cards,
        "empresa_eventos_activos_v3": sum(1 for e in eventos if e.activo),
        "empresa_eventos_atencion_v3": sum(1 for card in cards if card["atencion"]),
        "empresa_eventos_sin_planner_v3": eventos_sin_planner,
        "empresa_acciones_cliente_v3": acciones_cliente,
        "empresa_acciones_proveedor_v3": acciones_proveedor,
        "empresa_tareas_vencidas_v3": tareas_vencidas,
        "empresa_confirmaciones_pendientes_v3": participaciones_pendientes,
        "empresa_citas_proximas_v3": citas[:8],
        "empresa_sedes_activas_v3": empresa.sedes.filter(activa=True).count(),
        "empresa_proveedores_activos_v3": empresa.proveedores.filter(activo=True).count(),
        "empresa_paquetes_activos_v3": empresa.paquetes.filter(activo=True).count(),
        "empresa_servicios_catalogo_v3": empresa.servicios_catalogo.filter(activo=True).count(),
    }
