from decimal import Decimal, InvalidOperation

from django.core.exceptions import PermissionDenied
from django.db.models import Sum

from core.services.authorization import Actions, usuario_puede_evento
from core.services.permisos import roles_usuario_empresa, usuario_es_dirtec_operativo
from eventos.models import ContratoEvento, ParticipanteEvento
from proveedores.models import ServicioEvento

from .models import GastoEvento, PagoClienteEvento, PagoEvento


MONEY = Decimal('0.01')


def _money(valor):
    try:
        return Decimal(str(valor if valor is not None else '0')).quantize(MONEY)
    except (InvalidOperation, TypeError, ValueError):
        return Decimal('0.00')


def _sumar(qs, campo):
    return _money(qs.aggregate(total=Sum(campo))['total'])


def _pct(margen, total):
    total = _money(total)
    if total == 0:
        return Decimal('0.00')
    return ((margen / total) * Decimal('100')).quantize(MONEY)


def contrato_financiero_evento(evento):
    contrato = (
        ContratoEvento.objects.filter(evento=evento)
        .exclude(estado__in=['CANCELADO', 'REEMPLAZADO'])
        .order_by('-snapshot_version', '-version', '-id')
        .first()
    )
    if contrato and contrato.snapshot_version == 2:
        snapshot = contrato.snapshot_comercial or {}
        total = (snapshot.get('totales') or {}).get('total_final')
        return {
            'fuente': 'K9_CONTRATO_V2',
            'contrato': contrato,
            'total_contratado': _money(total if total is not None else contrato.monto_base),
            'advertencias': [],
        }
    if contrato:
        return {
            'fuente': 'CONTRATO_LEGACY',
            'contrato': contrato,
            'total_contratado': _money(contrato.monto_base),
            'advertencias': ['Contrato legacy: no existe snapshot K9 v2.'],
        }

    return {
        'fuente': 'SIN_CONTRATO',
        'contrato': None,
        'total_contratado': Decimal('0.00'),
        'advertencias': ['Sin contrato K9 v2 para este evento.'],
    }


def _servicio_detalle(servicio, gastos_por_servicio, pagos_por_gasto):
    gastos = gastos_por_servicio.get(servicio.id, [])
    costo_estimado = sum((_money(gasto.monto_estimado) for gasto in gastos), Decimal('0.00'))
    costo_real = sum((_money(gasto.monto_real) for gasto in gastos if _money(gasto.monto_real) > 0), Decimal('0.00'))
    costo_comprometido = sum(
        (_money(gasto.monto_real) if _money(gasto.monto_real) > 0 else _money(gasto.monto_estimado))
        for gasto in gastos
    )
    pagado = sum(
        sum((_money(pago.monto) for pago in pagos_por_gasto.get(gasto.id, [])), Decimal('0.00'))
        for gasto in gastos
    )
    costo_pendiente = (
        servicio.prestacion_tipo == 'POR_DEFINIR'
        and not servicio.proveedor_id
        and not gastos
        and _money(servicio.costo_proveedor) == 0
    )
    return {
        'servicio': servicio,
        'servicio_id': servicio.id,
        'nombre': servicio.nombre_servicio,
        'prestacion_tipo': servicio.prestacion_tipo,
        'proveedor': servicio.proveedor,
        'valor_contractual': _money(servicio.valor_contratado),
        'cargo_cliente': _money(servicio.cargo_adicional_cliente),
        'costo_estimado': costo_estimado,
        'costo_real': costo_real,
        'costo_comprometido': costo_comprometido,
        'pagado_operativo': pagado,
        'saldo_operativo': max(costo_comprometido - pagado, Decimal('0.00')),
        'costo_pendiente': costo_pendiente,
    }


def obtener_resumen_financiero_evento(evento):
    contrato_data = contrato_financiero_evento(evento)
    total_contratado = contrato_data['total_contratado']
    advertencias = list(contrato_data['advertencias'])

    pagos_cliente_qs = PagoClienteEvento.objects.filter(evento=evento, estado='RECIBIDO')
    pagos_cliente_recibidos = _sumar(pagos_cliente_qs, 'monto')
    saldo_bruto = total_contratado - pagos_cliente_recibidos
    saldo_cliente = max(saldo_bruto, Decimal('0.00'))
    sobrepago_cliente = abs(saldo_bruto) if saldo_bruto < 0 else Decimal('0.00')

    gastos_qs = (
        GastoEvento.objects.filter(evento=evento)
        .exclude(estado='CANCELADO')
        .select_related('servicio_evento', 'proveedor', 'categoria')
        .prefetch_related('pagos')
    )
    gastos = list(gastos_qs)
    costo_estimado = sum((_money(gasto.monto_estimado) for gasto in gastos), Decimal('0.00'))
    costo_real = sum((_money(gasto.monto_real) for gasto in gastos if _money(gasto.monto_real) > 0), Decimal('0.00'))
    costo_comprometido = sum(
        (_money(gasto.monto_real) if _money(gasto.monto_real) > 0 else _money(gasto.monto_estimado))
        for gasto in gastos
    )

    pagos_operativos_qs = PagoEvento.objects.filter(gasto__evento=evento, estado='ACTIVO').exclude(gasto__estado='CANCELADO')
    pagos_operativos_realizados = _sumar(pagos_operativos_qs, 'monto')
    saldo_operativo = max(costo_comprometido - pagos_operativos_realizados, Decimal('0.00'))

    margen_estimado = total_contratado - costo_estimado
    margen_real = total_contratado - costo_real
    flujo_neto_caja = pagos_cliente_recibidos - pagos_operativos_realizados

    servicios = list(
        ServicioEvento.objects.filter(evento=evento)
        .select_related('proveedor', 'servicio_catalogo_k9')
        .order_by('nombre_servicio', 'id')
    )
    gastos_por_servicio = {}
    for gasto in gastos:
        if gasto.servicio_evento_id:
            gastos_por_servicio.setdefault(gasto.servicio_evento_id, []).append(gasto)
    pagos_por_gasto = {}
    for gasto in gastos:
        pagos_por_gasto[gasto.id] = list(gasto.pagos.filter(estado='ACTIVO'))

    servicios_detalle = [_servicio_detalle(servicio, gastos_por_servicio, pagos_por_gasto) for servicio in servicios]
    pendientes = [item for item in servicios_detalle if item['costo_pendiente']]
    for item in pendientes:
        advertencias.append(f"Costo pendiente de definir: {item['nombre']}")

    return {
        'evento_id': evento.id,
        'fuente_total': contrato_data['fuente'],
        'contrato': contrato_data['contrato'],
        'total_contratado': total_contratado,
        'pagos_cliente_recibidos': pagos_cliente_recibidos,
        'saldo_cliente': saldo_cliente,
        'sobrepago_cliente': sobrepago_cliente,
        'costo_estimado': costo_estimado,
        'costo_real': costo_real,
        'costo_comprometido': costo_comprometido,
        'pagos_operativos_realizados': pagos_operativos_realizados,
        'saldo_operativo': saldo_operativo,
        'margen_estimado': margen_estimado,
        'margen_real': margen_real,
        'porcentaje_margen_estimado': _pct(margen_estimado, total_contratado),
        'porcentaje_margen_real': _pct(margen_real, total_contratado),
        'flujo_neto_caja': flujo_neto_caja,
        'advertencias': advertencias,
        'servicios': servicios_detalle,
        'pagos_cliente': list(
            PagoClienteEvento.objects.filter(evento=evento)
            .select_related('registrado_por', 'revisado_por', 'servicio_evento')
            .order_by('-fecha_pago', '-id')
        ),
        'gastos': gastos,
    }


def usuario_puede_ver_finanzas_internas(user, evento):
    if usuario_es_dirtec_operativo(user):
        return True
    roles = roles_usuario_empresa(user, evento.empresa)
    if roles.intersection({'ADMIN_EMPRESA', 'VENTAS'}):
        return usuario_puede_evento(user, evento, Actions.EVENT_VIEW)
    if 'WEDDING_PLANNER' in roles:
        return usuario_puede_evento(user, evento, Actions.EVENT_VIEW) and ParticipanteEvento.objects.filter(
            evento=evento,
            usuario=user,
            rol='PLANNER',
            activo=True,
            puede_ver_finanzas=True,
        ).exists()
    return False


def resumen_financiero_interno(evento, *, user):
    if not usuario_puede_ver_finanzas_internas(user, evento):
        raise PermissionDenied('No tienes permiso para ver finanzas internas.')
    return obtener_resumen_financiero_evento(evento)


def resumen_financiero_cliente(evento, *, user):
    if not (
        getattr(user, 'is_authenticated', False)
        and evento.clientes.filter(id=user.id).exists()
    ):
        raise PermissionDenied('No tienes permiso para ver pagos de este evento.')
    data = obtener_resumen_financiero_evento(evento)
    return {
        'evento_id': data['evento_id'],
        'fuente_total': data['fuente_total'],
        'total_contratado': data['total_contratado'],
        'pagos_cliente_recibidos': data['pagos_cliente_recibidos'],
        'saldo_cliente': data['saldo_cliente'],
        'sobrepago_cliente': data['sobrepago_cliente'],
        'pagos_cliente': [
            pago for pago in data['pagos_cliente']
            if pago.registrado_por_id == user.id or evento.clientes.filter(id=user.id).exists()
        ],
        'advertencias': [
            item for item in data['advertencias']
            if item.startswith('Sin contrato') or item.startswith('Contrato legacy')
        ],
    }
