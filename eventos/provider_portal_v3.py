from datetime import time

from django.db.models import Q
from django.urls import reverse
from django.utils import timezone

from colaboracion.models import CotizacionServicio
from documentos.models import DocumentoEvento
from itinerario.models import ActividadItinerario, ParticipanteActividad
from presupuesto.models import GastoEvento
from proveedores.models import ServicioEvento
from tareas.models import TareaEvento


def _workspace_url(servicio):
    return (
        reverse("colaboracion_workspace_servicio", args=[servicio.id])
        + "?canal=PLANNER_PROVEEDOR"
    )


def _nombre_servicio(servicio):
    return servicio.nombre_servicio or "Servicio"


def construir_contexto_portal_proveedor_v3(evento, proveedor, usuario):
    hoy = timezone.localdate()

    servicios = list(
        ServicioEvento.objects.filter(
            evento=evento,
            proveedor=proveedor,
        )
        .exclude(estado_operativo="CANCELADO")
        .select_related("evento", "proveedor")
        .prefetch_related("cotizaciones_workspace")
        .order_by("fecha_servicio", "hora_inicio", "nombre_servicio", "id")
    )
    servicio_ids = [s.id for s in servicios]

    cotizaciones = list(
        CotizacionServicio.objects.filter(
            servicio_evento_id__in=servicio_ids,
        )
        .select_related("servicio_evento", "creado_por")
        .order_by("servicio_evento_id", "-version", "-id")
    )
    ultima_cotizacion = {}
    for cotizacion in cotizaciones:
        ultima_cotizacion.setdefault(cotizacion.servicio_evento_id, cotizacion)

    tareas = list(
        TareaEvento.objects.filter(
            evento=evento,
            servicio_evento_id__in=servicio_ids,
            responsable=usuario,
        )
        .exclude(estado__in=["COMPLETADA", "CANCELADA"])
        .select_related("servicio_evento")
        .order_by("fecha_limite", "prioridad", "titulo")
    )

    participaciones = list(
        ParticipanteActividad.objects.filter(
            actividad__evento=evento,
            actividad__servicio_evento_id__in=servicio_ids,
            actividad__tipo="CITA",
            proveedor=proveedor,
        )
        .select_related("actividad", "actividad__servicio_evento")
        .order_by("actividad__fecha", "actividad__hora_inicio", "id")
    )
    citas = [
        p for p in participaciones
        if p.actividad.fecha >= hoy and p.actividad.estado != "CANCELADA"
    ]
    citas_pendientes = [
        p for p in citas
        if p.requerido and p.estado in {"PENDIENTE", "REPROGRAMAR"}
    ]

    actividades = list(
        ActividadItinerario.objects.filter(
            evento=evento,
            servicio_evento_id__in=servicio_ids,
            proveedor=proveedor,
            fecha__gte=hoy,
            tipo__in=["ACTIVIDAD", "HITO"],
        )
        .exclude(estado="CANCELADA")
        .select_related("servicio_evento")
        .order_by("fecha", "hora_inicio", "orden")
    )

    documentos = list(
        DocumentoEvento.objects.filter(
            evento=evento,
            servicio_evento_id__in=servicio_ids,
        )
        .filter(Q(visible_proveedor=True) | Q(cargado_por=usuario))
        .select_related("servicio_evento", "cargado_por")
        .order_by("-fecha_carga")[:40]
    )

    gastos = list(
        GastoEvento.objects.filter(
            evento=evento,
            proveedor=proveedor,
            servicio_evento_id__in=servicio_ids,
        )
        .exclude(estado="CANCELADO")
        .select_related("servicio_evento")
        .prefetch_related("pagos")
        .order_by("fecha_limite", "concepto")
    )

    acciones = []
    servicios_ui = []
    for servicio in servicios:
        cotizacion = ultima_cotizacion.get(servicio.id)
        if cotizacion and cotizacion.estado == "CAMBIOS_SOLICITADOS":
            acciones.append({
                "tipo": "COTIZACION",
                "prioridad": 10,
                "titulo": "Enviar nueva cotización",
                "detalle": cotizacion.respuesta_planner or f"Cambios solicitados sobre v{cotizacion.version}.",
                "servicio": servicio,
                "url": f"{_workspace_url(servicio)}#decisiones-aprobaciones",
                "cta": "Actualizar cotización",
            })

        servicio_tareas = [t for t in tareas if t.servicio_evento_id == servicio.id]
        servicio_citas = [p for p in citas_pendientes if p.actividad.servicio_evento_id == servicio.id]
        if servicio_citas:
            cita = servicio_citas[0].actividad
            acciones.append({
                "tipo": "CITA",
                "prioridad": 20,
                "titulo": "Confirmar cita",
                "detalle": f"{cita.titulo} · {cita.fecha:%d/%m/%Y}",
                "servicio": servicio,
                "url": f"{_workspace_url(servicio)}#operacion-servicio",
                "cta": "Revisar cita",
            })
        for tarea in servicio_tareas[:3]:
            acciones.append({
                "tipo": "TAREA",
                "prioridad": 30 if tarea.esta_vencida else 40,
                "titulo": "Tarea vencida" if tarea.esta_vencida else "Tarea pendiente",
                "detalle": tarea.titulo,
                "servicio": servicio,
                "url": f"{_workspace_url(servicio)}#operacion-servicio",
                "cta": "Revisar tarea",
            })

        servicios_ui.append({
            "objeto": servicio,
            "nombre": _nombre_servicio(servicio),
            "estado": servicio.get_estado_operativo_display(),
            "fecha": servicio.fecha_servicio,
            "hora_inicio": servicio.hora_inicio,
            "hora_fin": servicio.hora_fin,
            "lugar": servicio.lugar,
            "cotizacion": cotizacion,
            "tareas_pendientes": len(servicio_tareas),
            "citas_pendientes": len(servicio_citas),
            "url": _workspace_url(servicio),
        })

    acciones.sort(
        key=lambda a: (
            a["prioridad"],
            a["servicio"].nombre_servicio,
            a["titulo"],
        )
    )

    pagos = []
    total_comprometido = 0
    total_pagado = 0
    for gasto in gastos:
        objetivo = gasto.monto_objetivo
        pagado = gasto.total_pagado
        total_comprometido += objetivo
        total_pagado += pagado
        for pago in gasto.pagos.all():
            pagos.append({
                "objeto": pago,
                "gasto": gasto,
                "servicio": gasto.servicio_evento,
            })
    pagos.sort(key=lambda x: (x["objeto"].fecha_pago, x["objeto"].id), reverse=True)
    saldo = max(total_comprometido - total_pagado, 0)

    agenda = []
    citas_por_actividad = {p.actividad_id: p for p in citas}
    for participacion in citas:
        agenda.append({
            "tipo": "CITA",
            "actividad": participacion.actividad,
            "participacion": participacion,
            "servicio": participacion.actividad.servicio_evento,
        })
    for actividad in actividades:
        agenda.append({
            "tipo": actividad.tipo,
            "actividad": actividad,
            "participacion": None,
            "servicio": actividad.servicio_evento,
        })
    agenda.sort(
        key=lambda x: (
            x["actividad"].fecha,
            x["actividad"].hora_inicio or time.min,
        )
    )

    return {
        "provider_v3": True,
        "provider_servicios_v3": servicios_ui,
        "provider_servicios_total_v3": len(servicios_ui),
        "provider_acciones_v3": acciones,
        "provider_acciones_total_v3": len(acciones),
        "provider_tareas_v3": tareas,
        "provider_tareas_total_v3": len(tareas),
        "provider_citas_pendientes_v3": len(citas_pendientes),
        "provider_agenda_v3": agenda[:30],
        "provider_documentos_v3": documentos,
        "provider_documentos_total_v3": len(documentos),
        "provider_gastos_v3": gastos,
        "provider_pagos_v3": pagos[:40],
        "provider_total_comprometido_v3": total_comprometido,
        "provider_total_pagado_v3": total_pagado,
        "provider_saldo_v3": saldo,
        "provider_cotizaciones_v3": cotizaciones[:40],
        "provider_tipos_documento_v3": DocumentoEvento.TIPOS,
    }
