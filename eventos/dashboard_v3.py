from decimal import Decimal

from django.db.models import Count, Q
from django.utils import timezone

from colaboracion.models import (
    AprobacionServicio,
    CotizacionServicio,
    PropuestaServicioCliente,
)
from eventos.models import ParticipanteEvento
from itinerario.models import ActividadItinerario, ParticipanteActividad
from proveedores.models import ServicioEvento
from presupuesto.services import obtener_resumen_financiero_evento


def _decimal(value):
    return value if value is not None else Decimal('0')


def _primero_por_servicio(queryset):
    resultado = {}
    for obj in queryset:
        resultado.setdefault(obj.servicio_evento_id, obj)
    return resultado


def _accion(titulo, detalle, responsable, *, nivel='warning', etiqueta=None):
    return {
        'titulo': titulo,
        'detalle': detalle,
        'responsable': responsable,
        'nivel': nivel,
        'etiqueta': etiqueta or responsable,
    }


def _enriquecer_servicios(servicios, evento, hoy):
    ids = [servicio.id for servicio in servicios]
    if not ids:
        return servicios

    aprobaciones = _primero_por_servicio(
        AprobacionServicio.objects.filter(
            servicio_evento_id__in=ids,
            estado='PENDIENTE',
        ).order_by('servicio_evento_id', '-fecha_solicitud', '-id')
    )
    propuestas_enviadas = _primero_por_servicio(
        PropuestaServicioCliente.objects.filter(
            servicio_evento_id__in=ids,
            estado='ENVIADA',
        ).order_by('servicio_evento_id', '-version', '-id')
    )
    propuestas_cambios = _primero_por_servicio(
        PropuestaServicioCliente.objects.filter(
            servicio_evento_id__in=ids,
            estado='CAMBIOS_SOLICITADOS',
        ).order_by('servicio_evento_id', '-version', '-id')
    )
    cotizaciones_recibidas = _primero_por_servicio(
        CotizacionServicio.objects.filter(
            servicio_evento_id__in=ids,
            estado='ENVIADA',
        ).order_by('servicio_evento_id', '-version', '-id')
    )
    cotizaciones_cambios = _primero_por_servicio(
        CotizacionServicio.objects.filter(
            servicio_evento_id__in=ids,
            estado='CAMBIOS_SOLICITADOS',
        ).order_by('servicio_evento_id', '-version', '-id')
    )

    participaciones_cita = list(
        ParticipanteActividad.objects.filter(
            actividad__servicio_evento_id__in=ids,
            actividad__tipo='CITA',
            actividad__fecha__gte=hoy,
            requerido=True,
            estado='PENDIENTE',
            rol__in=['CLIENTE', 'PROVEEDOR'],
        ).select_related('actividad', 'usuario', 'proveedor').order_by(
            'actividad__fecha', 'actividad__hora_inicio', 'id'
        )
    )
    cita_cliente = {}
    cita_proveedor = {}
    for participante in participaciones_cita:
        destino = cita_cliente if participante.rol == 'CLIENTE' else cita_proveedor
        destino.setdefault(participante.actividad.servicio_evento_id, participante)

    for servicio in servicios:
        servicio.cliente_accion_v3 = None
        servicio.proveedor_accion_v3 = None

        propuesta_cambios = propuestas_cambios.get(servicio.id)
        aprobacion = aprobaciones.get(servicio.id)
        propuesta = propuestas_enviadas.get(servicio.id)
        cliente_cita = cita_cliente.get(servicio.id)

        if propuesta_cambios:
            servicio.cliente_accion_v3 = _accion(
                'Cliente solicitó cambios',
                f'Propuesta v{propuesta_cambios.version} requiere revisión del Planner.',
                'Planner',
                nivel='danger',
            )
        elif aprobacion:
            servicio.cliente_accion_v3 = _accion(
                'Esperando aprobación',
                aprobacion.titulo,
                'Cliente',
            )
        elif propuesta:
            servicio.cliente_accion_v3 = _accion(
                'Propuesta enviada',
                f'Versión {propuesta.version} · cargo adicional ${propuesta.cargo_adicional_cliente:,.2f}',
                'Cliente',
            )
        elif cliente_cita:
            cita = cliente_cita.actividad
            servicio.cliente_accion_v3 = _accion(
                'Confirmar cita',
                f'{cita.titulo} · {cita.fecha:%d/%m/%Y} {cita.hora_inicio:%H:%M}',
                'Cliente',
                nivel='info',
            )

        cotizacion = cotizaciones_recibidas.get(servicio.id)
        cotizacion_cambios = cotizaciones_cambios.get(servicio.id)
        proveedor_cita = cita_proveedor.get(servicio.id)
        if cotizacion:
            servicio.proveedor_accion_v3 = _accion(
                'Revisar cotización del proveedor',
                f'Cotización v{cotizacion.version} · ${cotizacion.costo_proveedor:,.2f}',
                'Planner',
                nivel='danger',
            )
        elif cotizacion_cambios:
            servicio.proveedor_accion_v3 = _accion(
                'Esperando nueva cotización',
                f'Se solicitaron cambios a la versión {cotizacion_cambios.version}.',
                'Proveedor',
            )
        elif proveedor_cita:
            cita = proveedor_cita.actividad
            servicio.proveedor_accion_v3 = _accion(
                'Confirmar cita',
                f'{cita.titulo} · {cita.fecha:%d/%m/%Y} {cita.hora_inicio:%H:%M}',
                'Proveedor',
                nivel='info',
            )
        elif not servicio.proveedor_id:
            servicio.proveedor_accion_v3 = _accion(
                'Proveedor por definir',
                'Asigna el proveedor responsable antes de continuar la operación.',
                'Planner',
                nivel='warning',
            )

        # Una única siguiente acción evita que el dashboard sea solo una colección de contadores.
        candidatos = [servicio.cliente_accion_v3, servicio.proveedor_accion_v3]
        prioridad = {'danger': 0, 'warning': 1, 'info': 2}
        candidatos = [c for c in candidatos if c]
        servicio.siguiente_accion_v3 = sorted(
            candidatos,
            key=lambda item: prioridad.get(item['nivel'], 9),
        )[0] if candidatos else None

    return servicios


def _marcar_rol_tareas(tareas, evento):
    roles = {
        item.usuario_id: item.get_rol_display()
        for item in ParticipanteEvento.objects.filter(evento=evento, activo=True)
    }
    for tarea in tareas:
        if not tarea.responsable_id:
            tarea.responsable_rol_v3 = 'Sin responsable'
        elif tarea.responsable_id in roles:
            tarea.responsable_rol_v3 = roles[tarea.responsable_id]
        elif hasattr(tarea.responsable, 'perfil_proveedor'):
            tarea.responsable_rol_v3 = 'Proveedor'
        else:
            tarea.responsable_rol_v3 = 'Equipo'
    return tareas


def construir_contexto_dashboard_evento_v3(
    evento,
    *,
    servicios_evento,
    tareas_evento,
    actividades_evento,
    gastos_evento,
    documentos_evento,
    invitados_confirmados_sin_mesa=0,
):
    """Contexto Event-Centric. No proyecta módulos legacy paralelos."""
    if not evento:
        return {}

    hoy = timezone.localdate()
    fecha_evento = getattr(evento, 'fecha_fiesta', None)
    if fecha_evento and hasattr(fecha_evento, 'date'):
        fecha_evento = fecha_evento.date()
    dias_evento = (fecha_evento - hoy).days if fecha_evento else None

    servicios_base_v3 = ServicioEvento.objects.filter(evento=evento)
    servicios_v3 = list(
        servicios_base_v3.filter(archivado_en__isnull=True)
        .select_related('proveedor', 'paquete_evento')
        .annotate(
            tareas_pendientes_v3=Count(
                'tareas_operativas',
                filter=~Q(tareas_operativas__estado__in=['COMPLETADA', 'CANCELADA']),
                distinct=True,
            ),
            aprobaciones_pendientes_v3=Count(
                'aprobaciones_workspace',
                filter=Q(aprobaciones_workspace__estado='PENDIENTE'),
                distinct=True,
            ),
            propuestas_pendientes_v3=Count(
                'propuestas_workspace',
                filter=Q(propuestas_workspace__estado__in=['ENVIADA', 'CAMBIOS_SOLICITADOS']),
                distinct=True,
            ),
        )
        .order_by('estado_operativo', 'fecha_servicio', 'nombre_servicio')
    )
    servicios_historial_v3 = list(
        servicios_base_v3.filter(archivado_en__isnull=False)
        .select_related('proveedor', 'paquete_evento')
        .order_by('-archivado_en', 'nombre_servicio')
    )
    servicios_gestion_v3 = servicios_v3 + servicios_historial_v3
    _enriquecer_servicios(servicios_v3, evento, hoy)

    servicios_activos = sum(1 for s in servicios_v3 if s.estado_operativo not in {'COMPLETADO', 'CANCELADO'})
    servicios_incidencia = sum(1 for s in servicios_v3 if s.estado_operativo == 'INCIDENCIA')
    aprobaciones_servicio_pendientes = AprobacionServicio.objects.filter(
        servicio_evento__evento=evento,
        estado='PENDIENTE',
    ).count()
    propuestas_cliente_pendientes = PropuestaServicioCliente.objects.filter(
        servicio_evento__evento=evento,
        estado__in=['ENVIADA', 'CAMBIOS_SOLICITADOS'],
    ).count()

    tareas_evento_v3 = list(
        tareas_evento.filter(archivado_en__isnull=True).select_related('responsable', 'servicio_evento')
        .order_by('estado', 'fecha_limite', 'prioridad', 'titulo')
    )
    tareas_historial_v3 = list(
        tareas_evento.filter(archivado_en__isnull=False)
        .select_related('responsable', 'servicio_evento')
        .order_by('-archivado_en', 'titulo')
    )
    _marcar_rol_tareas(tareas_evento_v3, evento)
    _marcar_rol_tareas(tareas_historial_v3, evento)
    tareas_gestion_v3 = tareas_evento_v3 + tareas_historial_v3
    tareas_activas = [t for t in tareas_evento_v3 if t.estado not in {'COMPLETADA', 'CANCELADA'}]
    tareas_vencidas_v3 = [t for t in tareas_activas if t.esta_vencida]
    tareas_proximas_v3 = [t for t in tareas_activas if t.fecha_limite][:8]

    actividades_base = list(
        actividades_evento.filter(archivado_en__isnull=True).exclude(estado__in=['COMPLETADA', 'CANCELADA'])
        .filter(fecha__gte=hoy)
        .select_related('servicio_evento', 'proveedor', 'responsable')
        .prefetch_related('participantes__usuario', 'participantes__proveedor')
        .order_by('fecha', 'hora_inicio')
    )
    citas_v3 = [a for a in actividades_base if a.tipo == 'CITA']
    itinerario_v3 = [a for a in actividades_base if a.tipo in {'ACTIVIDAD', 'HITO'}]
    citas_pendientes_confirmacion_v3 = sum(a.confirmaciones_pendientes for a in citas_v3)
    actividades_historial_v3 = list(
        actividades_evento.filter(Q(archivado_en__isnull=False) | Q(estado='CANCELADA'))
        .select_related('servicio_evento', 'proveedor', 'responsable')
        .order_by('-fecha', '-hora_inicio')[:50]
    )

    gastos_vencidos_v3 = [g for g in gastos_evento if g.esta_vencido]
    resumen_financiero = obtener_resumen_financiero_evento(evento)
    contrato_actual = resumen_financiero['contrato']
    total_cliente = resumen_financiero['total_contratado']
    pagos_cliente_evento_v3 = resumen_financiero['pagos_cliente']
    pagos_cliente_pendientes_v3 = [
        pago for pago in pagos_cliente_evento_v3
        if pago.estado in {'PENDIENTE', 'OBSERVADO'}
    ]

    documentos_generales = documentos_evento.filter(servicio_evento__isnull=True, archivado_en__isnull=True).order_by('-fecha_carga')
    documentos_servicio = documentos_evento.filter(servicio_evento__isnull=False, archivado_en__isnull=True).select_related('servicio_evento').order_by('servicio_evento__nombre_servicio', '-fecha_carga')
    documentos_archivados_v3 = documentos_evento.filter(archivado_en__isnull=False).select_related('servicio_evento').order_by('-archivado_en', '-fecha_carga')

    atencion = []
    if tareas_vencidas_v3:
        atencion.append({'nivel': 'danger', 'cantidad': len(tareas_vencidas_v3), 'titulo': 'Tareas vencidas', 'detalle': 'Hay trabajo pendiente que ya superó su fecha límite.', 'tab': 'tareas'})
    if aprobaciones_servicio_pendientes:
        atencion.append({'nivel': 'warning', 'cantidad': aprobaciones_servicio_pendientes, 'titulo': 'Cliente debe aprobar', 'detalle': 'Hay decisiones esperando respuesta del cliente.', 'tab': 'servicios'})
    if propuestas_cliente_pendientes:
        atencion.append({'nivel': 'warning', 'cantidad': propuestas_cliente_pendientes, 'titulo': 'Propuestas abiertas', 'detalle': 'Hay propuestas enviadas o con cambios solicitados.', 'tab': 'servicios'})
    if citas_pendientes_confirmacion_v3:
        atencion.append({'nivel': 'warning', 'cantidad': citas_pendientes_confirmacion_v3, 'titulo': 'Confirmaciones de cita', 'detalle': 'Hay participantes que aún no confirman asistencia.', 'tab': 'agenda'})
    if gastos_vencidos_v3:
        atencion.append({'nivel': 'danger', 'cantidad': len(gastos_vencidos_v3), 'titulo': 'Pagos vencidos', 'detalle': 'Existen compromisos operativos con saldo vencido.', 'tab': 'finanzas'})
    if pagos_cliente_pendientes_v3:
        atencion.append({'nivel': 'warning', 'cantidad': len(pagos_cliente_pendientes_v3), 'titulo': 'Pagos de cliente por revisar', 'detalle': 'Hay comprobantes reportados por cliente esperando validación del equipo.', 'tab': 'finanzas'})
    if invitados_confirmados_sin_mesa:
        atencion.append({'nivel': 'warning', 'cantidad': invitados_confirmados_sin_mesa, 'titulo': 'Confirmados sin mesa', 'detalle': 'Personas confirmadas todavía no están acomodadas.', 'tab': 'invitados'})
    if servicios_incidencia:
        atencion.append({'nivel': 'danger', 'cantidad': servicios_incidencia, 'titulo': 'Servicios con incidencia', 'detalle': 'Revisa el workspace de los servicios afectados.', 'tab': 'servicios'})

    return {
        'dashboard_v3': True,
        'dias_evento_v3': dias_evento,
        'servicios_v3': servicios_v3,
        'servicios_gestion_v3': servicios_gestion_v3,
        'servicios_historial_v3': servicios_historial_v3,
        'servicios_activos_v3': servicios_activos,
        'servicios_incidencia_v3': servicios_incidencia,
        'aprobaciones_servicio_pendientes_v3': aprobaciones_servicio_pendientes,
        'propuestas_cliente_pendientes_v3': propuestas_cliente_pendientes,
        'tareas_evento_v3': tareas_evento_v3,
        'tareas_gestion_v3': tareas_gestion_v3,
        'tareas_historial_v3': tareas_historial_v3,
        'tareas_vencidas_v3': tareas_vencidas_v3,
        'tareas_proximas_v3': tareas_proximas_v3,
        'citas_v3': citas_v3,
        'itinerario_v3': itinerario_v3,
        'actividades_historial_v3': actividades_historial_v3,
        'citas_pendientes_confirmacion_v3': citas_pendientes_confirmacion_v3,
        'actividades_proximas_v3': actividades_base[:10],
        'gastos_vencidos_v3': gastos_vencidos_v3,
        'gastos_operativos_total_v3': resumen_financiero['costo_comprometido'],
        'pagos_operativos_total_v3': resumen_financiero['pagos_operativos_realizados'],
        'saldo_operativo_v3': resumen_financiero['saldo_operativo'],
        'pagos_cliente_evento_v3': pagos_cliente_evento_v3,
        'pagos_cliente_pendientes_v3': pagos_cliente_pendientes_v3,
        'contrato_actual_v3': contrato_actual,
        'contrato_base_v3': total_cliente,
        'extras_cliente_v3': Decimal('0'),
        'total_cliente_v3': total_cliente,
        'resumen_financiero_v3': resumen_financiero,
        'documentos_generales_v3': documentos_generales,
        'documentos_servicio_v3': documentos_servicio,
        'documentos_archivados_v3': documentos_archivados_v3,
        'tipos_agenda_v3': ActividadItinerario.TIPOS,
        'categorias_agenda_v3': ActividadItinerario.CATEGORIAS,
        'prioridades_agenda_v3': ActividadItinerario.PRIORIDADES,
        'atencion_v3': atencion[:7],
    }
