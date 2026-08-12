from django.urls import reverse
from django.utils import timezone

from colaboracion.models import AprobacionServicio, PropuestaServicioCliente
from documentos.models import DocumentoEvento
from itinerario.models import ActividadItinerario, ParticipanteActividad
from proveedores.models import ServicioEvento
from presupuesto.models import PagoClienteEvento
from tareas.models import TareaEvento


def _servicio_nombre(servicio):
    return servicio.nombre_servicio or "Servicio"


def _proveedor_nombre(servicio):
    if servicio.proveedor_id:
        return servicio.proveedor.nombre_comercial
    return servicio.proveedor_nombre_snapshot or "Equipo del evento"


def _workspace_url(servicio):
    return (
        reverse("colaboracion_workspace_servicio", args=[servicio.id])
        + "?canal=CLIENTE_PLANNER"
    )


def construir_contexto_portal_cliente_v3(evento, usuario):
    hoy = timezone.localdate()

    servicios = list(
        ServicioEvento.objects.filter(evento=evento)
        .exclude(estado_comercial="CANCELADO")
        .exclude(estado_operativo="CANCELADO")
        .select_related("proveedor")
        .prefetch_related(
            "propuestas_workspace",
            "aprobaciones_workspace",
            "decisiones_workspace",
        )
        .order_by("fecha_servicio", "nombre_servicio", "id")
    )

    propuestas_pendientes = list(
        PropuestaServicioCliente.objects.filter(
            servicio_evento__evento=evento,
            estado="ENVIADA",
        )
        .select_related("servicio_evento")
        .order_by("-fecha_envio", "-id")
    )
    aprobaciones_pendientes = list(
        AprobacionServicio.objects.filter(
            servicio_evento__evento=evento,
            estado="PENDIENTE",
        )
        .select_related("servicio_evento")
        .order_by("-fecha_solicitud", "-id")
    )
    tareas = list(
        TareaEvento.objects.filter(
            evento=evento,
            responsable=usuario,
        )
        .exclude(estado__in=["COMPLETADA", "CANCELADA"])
        .select_related("servicio_evento")
        .order_by("fecha_limite", "prioridad", "id")
    )

    participaciones = list(
        ParticipanteActividad.objects.filter(
            actividad__evento=evento,
            actividad__tipo="CITA",
            usuario=usuario,
        )
        .select_related(
            "actividad",
            "actividad__servicio_evento",
            "actividad__proveedor",
        )
        .order_by("actividad__fecha", "actividad__hora_inicio", "id")
    )
    citas_cliente = [
        p for p in participaciones
        if p.actividad.fecha >= hoy and p.actividad.estado != "CANCELADA"
    ]
    citas_pendientes = [
        p for p in citas_cliente
        if p.requerido and p.estado in {"PENDIENTE", "REPROGRAMAR"}
    ]

    acciones = []
    for aprobacion in aprobaciones_pendientes:
        servicio = aprobacion.servicio_evento
        acciones.append({
            "tipo": "APROBACION",
            "prioridad": 10,
            "titulo": "Aprobar decisión",
            "detalle": aprobacion.titulo,
            "servicio": _servicio_nombre(servicio),
            "url": f"{_workspace_url(servicio)}#decisiones-aprobaciones",
            "cta": "Revisar aprobación",
        })
    for propuesta in propuestas_pendientes:
        servicio = propuesta.servicio_evento
        acciones.append({
            "tipo": "PROPUESTA",
            "prioridad": 20,
            "titulo": "Revisar propuesta",
            "detalle": propuesta.descripcion or propuesta.get_modalidad_display(),
            "servicio": _servicio_nombre(servicio),
            "url": f"{_workspace_url(servicio)}#decisiones-aprobaciones",
            "cta": "Revisar propuesta",
        })
    for participante in citas_pendientes:
        actividad = participante.actividad
        servicio = actividad.servicio_evento
        acciones.append({
            "tipo": "CITA",
            "prioridad": 30,
            "titulo": (
                "Confirmar cita"
                if participante.estado == "PENDIENTE"
                else "Revisar reprogramación"
            ),
            "detalle": actividad.titulo,
            "servicio": _servicio_nombre(servicio) if servicio else "Evento general",
            "url": (
                f"{_workspace_url(servicio)}#operacion-servicio"
                if servicio else "#agenda"
            ),
            "cta": "Ver cita",
        })
    for tarea in tareas:
        acciones.append({
            "tipo": "TAREA",
            "prioridad": 40,
            "titulo": "Tarea pendiente",
            "detalle": tarea.titulo,
            "servicio": (
                _servicio_nombre(tarea.servicio_evento)
                if tarea.servicio_evento_id else "Evento general"
            ),
            "url": (
                f"{_workspace_url(tarea.servicio_evento)}#operacion-servicio"
                if tarea.servicio_evento_id else "#tareas"
            ),
            "cta": "Revisar tarea",
        })
    acciones.sort(key=lambda item: (item["prioridad"], item["servicio"], item["detalle"]))

    servicios_ui = []
    for servicio in servicios:
        aprobacion = next(
            (a for a in servicio.aprobaciones_workspace.all() if a.estado == "PENDIENTE"),
            None,
        )
        propuesta = next(
            (p for p in servicio.propuestas_workspace.all() if p.estado == "ENVIADA"),
            None,
        )
        if aprobacion:
            estado_cliente = "Requiere tu aprobación"
            detalle_cliente = aprobacion.titulo
            requiere_accion = True
        elif propuesta:
            estado_cliente = "Propuesta esperando respuesta"
            detalle_cliente = propuesta.descripcion or propuesta.get_modalidad_display()
            requiere_accion = True
        else:
            estado_cliente = servicio.get_estado_operativo_display()
            detalle_cliente = "Sin acciones pendientes para ti."
            requiere_accion = False
        servicios_ui.append({
            "objeto": servicio,
            "nombre": _servicio_nombre(servicio),
            "proveedor": _proveedor_nombre(servicio),
            "estado": estado_cliente,
            "detalle": detalle_cliente,
            "requiere_accion": requiere_accion,
            "url": _workspace_url(servicio),
        })

    actividades = list(
        ActividadItinerario.objects.filter(
            evento=evento,
            fecha__gte=hoy,
        )
        .exclude(estado="CANCELADA")
        .select_related("servicio_evento", "proveedor")
        .order_by("fecha", "hora_inicio", "orden")[:20]
    )
    citas_ids_cliente = {p.actividad_id: p for p in citas_cliente}
    agenda = []
    for actividad in actividades:
        participacion = citas_ids_cliente.get(actividad.id)
        # Una cita privada solo se muestra si este cliente fue invitado.
        if actividad.tipo == "CITA" and not participacion:
            continue
        # Actividades/hitos operativos ligados a un servicio no se exponen
        # automáticamente: el cliente consulta el servicio por su canal propio.
        if actividad.tipo != "CITA" and actividad.servicio_evento_id:
            continue
        agenda.append({
            "objeto": actividad,
            "participacion": participacion,
            "servicio": (
                _servicio_nombre(actividad.servicio_evento)
                if actividad.servicio_evento_id else "Evento general"
            ),
        })

    documentos = (
        DocumentoEvento.objects.filter(
            evento=evento,
            visible_cliente=True,
        )
        .select_related("servicio_evento")
        .order_by("-fecha_carga")
    )

    pagos_cliente = list(
        PagoClienteEvento.objects.filter(
            evento=evento,
        )
        .select_related(
            "servicio_evento",
            "revisado_por",
        )
        .order_by("-fecha_pago", "-id")[:30]
    )
    for pago in pagos_cliente:
        if pago.estado == "OBSERVADO":
            acciones.append({
                "tipo": "PAGO",
                "prioridad": 15,
                "titulo": "Revisar pago observado",
                "detalle": pago.comentario_equipo or "La empresa o planner dejó una observación sobre este pago.",
                "servicio": _servicio_nombre(pago.servicio_evento) if pago.servicio_evento_id else "Pago general del evento",
                "url": "#pagos",
                "cta": "Ver comprobante",
            })
    acciones.sort(key=lambda item: (item["prioridad"], item["servicio"], item["detalle"]))

    return {
        "cliente_acciones_v3": acciones,
        "cliente_acciones_total_v3": len(acciones),
        "cliente_aprobaciones_pendientes_v3": len(aprobaciones_pendientes),
        "cliente_propuestas_pendientes_v3": len(propuestas_pendientes),
        "cliente_citas_pendientes_v3": len(citas_pendientes),
        "cliente_tareas_pendientes_v3": len(tareas),
        "cliente_servicios_v3": servicios_ui,
        "cliente_agenda_v3": agenda,
        "cliente_tareas_v3": tareas,
        "cliente_documentos_v3": documentos[:30],
        "cliente_documentos_total_v3": documentos.count(),
        "cliente_pagos_v3": pagos_cliente,
        "cliente_pagos_total_v3": len(pagos_cliente),
        "metodos_pago_cliente_v3": PagoClienteEvento.METODOS,
        "cliente_servicios_pago_v3": servicios_ui,
    }
