from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from core.services.authorization import Actions, usuario_puede_evento, usuario_tiene_permiso
from core.services.permisos import roles_usuario_empresa
from proveedores.models import ServicioEvento

from .models import PaqueteBoda, PropuestaEvento


PROPUESTA_VERSION_CALCULO = 1
PROPUESTA_SNAPSHOT_ACEPTACION_VERSION = 1
PROPUESTA_ESTADOS_NEGOCIABLES = {"BORRADOR", "PROPUESTA", "EN_REVISION"}
PROPUESTA_ESTADOS_CONGELADOS = {"ACEPTADO", "CONTRATADO"}
MONEY = Decimal('0.01')


def _decimal_a_texto(valor):
    return str(valor if valor is not None else Decimal('0'))


def _money(valor):
    return Decimal(str(valor if valor is not None else '0')).quantize(MONEY)


def _cantidad(valor):
    return Decimal(str(valor if valor is not None else '0'))


def _linea_dict(**kwargs):
    data = {}
    for key, value in kwargs.items():
        if isinstance(value, Decimal):
            data[key] = str(value)
        else:
            data[key] = value
    return data


def _fecha_evento_iso(evento):
    fecha_evento = evento.fecha_inicio or evento.fecha_fiesta
    return fecha_evento.isoformat() if fecha_evento else None


def _snapshot_empresa(empresa):
    return {
        'id': empresa.id if empresa else None,
        'nombre': empresa.nombre_comercial if empresa else '',
        'razon_social': getattr(empresa, 'razon_social', '') or '',
    }


def _snapshot_evento(evento):
    return {
        'id': evento.id,
        'nombre': evento.titulo_evento,
        'tipo': evento.tipo_evento,
        'fecha_evento': _fecha_evento_iso(evento),
    }


def _snapshot_sede(sede):
    if not sede:
        return {'id': None, 'nombre': '', 'tipo': '', 'direccion': '', 'capacidad_minima': 0, 'capacidad_maxima': 0}
    return {
        'id': sede.id,
        'nombre': sede.nombre,
        'tipo': sede.tipo,
        'direccion': sede.direccion or '',
        'descripcion': sede.descripcion or '',
        'capacidad_minima': sede.capacidad_minima,
        'capacidad_maxima': sede.capacidad_maxima,
        'precio_base': _decimal_a_texto(_money(sede.precio_base)),
    }


def _snapshot_paquete(paquete):
    return {
        'id': paquete.id,
        'nombre': paquete.nombre,
        'descripcion': paquete.descripcion or '',
        'precio_adulto': _decimal_a_texto(paquete.precio_adulto),
        'precio_nino': _decimal_a_texto(paquete.precio_nino),
        'cargo_fijo': _decimal_a_texto(paquete.cargo_fijo),
        'duracion_evento': paquete.duracion_evento,
        'capacidad_minima_recomendada': paquete.capacidad_minima_recomendada,
        'capacidad_maxima_recomendada': paquete.capacidad_maxima_recomendada,
    }


def _linea_incluida_aceptacion(linea):
    return {
        'clave_origen': linea.get('clave_origen') or '',
        'origen': linea.get('origen') or '',
        'servicio_catalogo_id': linea.get('servicio_catalogo_id'),
        'servicio_paquete_id': linea.get('servicio_paquete_id'),
        'nombre': linea.get('nombre') or '',
        'categoria': linea.get('categoria') or '',
        'cantidad': str(linea.get('cantidad') or '0'),
        'notas': linea.get('notas') or '',
        'valor_comercial': str(linea.get('precio_incluido') or '0.00'),
        'incluido': bool(linea.get('incluido', True)),
        'obligatorio': bool(linea.get('obligatorio', True)),
    }


def _linea_adicional_aceptacion(linea):
    return {
        'linea_id': linea.get('linea_id'),
        'origen': linea.get('origen') or '',
        'servicio_catalogo_id': linea.get('servicio_catalogo_id'),
        'nombre': linea.get('nombre') or '',
        'descripcion': linea.get('descripcion') or '',
        'modo_precio': linea.get('modo_precio') or '',
        'tarifa': str(linea.get('tarifa') or '0.00'),
        'cantidad': str(linea.get('cantidad') or '0'),
        'cantidad_aplicada': str(linea.get('cantidad_aplicada') or '0'),
        'subtotal': str(linea.get('subtotal') or '0.00'),
    }


def _linea_cortesia_aceptacion(linea):
    return {
        'linea_id': linea.get('linea_id'),
        'origen': linea.get('origen') or '',
        'servicio_catalogo_id': linea.get('servicio_catalogo_id'),
        'nombre': linea.get('nombre') or '',
        'descripcion': linea.get('descripcion') or '',
        'valor_informativo': str(linea.get('valor_informativo') or '0.00'),
        'cargo_cliente': '0.00',
    }


def construir_snapshot_aceptacion(propuesta, dto, *, user=None, fecha=None):
    fecha = fecha or timezone.now()
    subtotal_base = _money(dto['subtotal_base'])
    subtotal = _money(dto['subtotal'])
    descuento = _money(dto['descuento'])
    total = _money(dto['total'])
    adicionales_total = subtotal - subtotal_base
    if adicionales_total < 0:
        adicionales_total = Decimal('0.00')

    return {
        'version': PROPUESTA_SNAPSHOT_ACEPTACION_VERSION,
        'fecha_aceptacion': fecha.isoformat(),
        'aceptado_por': user.id if user else None,
        'evento': _snapshot_evento(propuesta.evento),
        'empresa': _snapshot_empresa(propuesta.empresa),
        'paquete': _snapshot_paquete(propuesta.paquete),
        'sede': _snapshot_sede(propuesta.sede),
        'cantidades': {
            'adultos': int(propuesta.adultos or 0),
            'ninos': int(propuesta.ninos or 0),
            'total_personas': int(propuesta.adultos or 0) + int(propuesta.ninos or 0),
        },
        'incluidos': [_linea_incluida_aceptacion(linea) for linea in dto['lineas_incluidas']],
        'adicionales': [_linea_adicional_aceptacion(linea) for linea in dto['lineas_adicionales']],
        'cortesias': [_linea_cortesia_aceptacion(linea) for linea in dto['lineas_cortesia']],
        'descuentos': {
            'monto': _decimal_a_texto(descuento),
        },
        'totales': {
            'base': _decimal_a_texto(subtotal_base),
            'adicionales': _decimal_a_texto(adicionales_total),
            'descuento': _decimal_a_texto(descuento),
            'total_final': _decimal_a_texto(total),
        },
        'notas_comerciales': propuesta.notas_comerciales or '',
        'metadata': {
            'version_calculo': dto['version_calculo'],
            'propuesta_origen_id': propuesta.id,
            'fuente': 'PROPUESTA_ACEPTADA_D1',
        },
    }


def propuesta_tiene_snapshot_aceptacion(propuesta):
    return bool(
        propuesta
        and propuesta.snapshot_aceptacion
        and propuesta.snapshot_aceptacion_version == PROPUESTA_SNAPSHOT_ACEPTACION_VERSION
        and propuesta.snapshot_aceptacion.get('version') == PROPUESTA_SNAPSHOT_ACEPTACION_VERSION
    )


def dto_desde_snapshot_aceptacion(snapshot):
    totales = snapshot.get('totales') or {}
    descuentos = snapshot.get('descuentos') or {}
    cantidades = snapshot.get('cantidades') or {}
    return {
        'evento_id': (snapshot.get('evento') or {}).get('id'),
        'empresa_id': (snapshot.get('empresa') or {}).get('id'),
        'sede': snapshot.get('sede') or {},
        'adultos': int(cantidades.get('adultos') or 0),
        'ninos': int(cantidades.get('ninos') or 0),
        'paquete': snapshot.get('paquete') or {},
        'subtotal_base': _money(totales.get('base')),
        'lineas_incluidas': snapshot.get('incluidos') or [],
        'lineas_adicionales': snapshot.get('adicionales') or [],
        'lineas_cortesia': snapshot.get('cortesias') or [],
        'descuento': _money(descuentos.get('monto') or totales.get('descuento')),
        'subtotal': _money(_money(totales.get('base')) + _money(totales.get('adicionales'))),
        'total': _money(totales.get('total_final')),
        'advertencias': [],
        'version_calculo': (snapshot.get('metadata') or {}).get('version_calculo') or PROPUESTA_VERSION_CALCULO,
    }


def puede_ver_paquetes(user, empresa):
    roles = roles_usuario_empresa(user, empresa)
    return bool(
        usuario_tiene_permiso(user, Actions.COMPANY_VIEW, empresa=empresa)
        or 'WEDDING_PLANNER' in roles
    )


def puede_gestionar_paquetes(user, empresa):
    return usuario_tiene_permiso(user, Actions.COMPANY_MANAGE_CATALOGS, empresa=empresa)


def puede_editar_propuesta(user, propuesta_or_evento):
    evento = getattr(propuesta_or_evento, 'evento', propuesta_or_evento)
    return usuario_puede_evento(user, evento, Actions.EVENT_EDIT)


def paquetes_empresa_qs(empresa):
    return PaqueteBoda.objects.filter(empresa=empresa).prefetch_related(
        'servicios_catalogo_k9__servicio_catalogo',
        'media_comercial',
    )


def propuestas_empresa_qs(empresa):
    return PropuestaEvento.objects.filter(empresa=empresa).select_related(
        'empresa',
        'evento',
        'sede',
        'paquete',
    ).prefetch_related(
        'lineas__servicio_catalogo',
        'paquete__servicios_catalogo_k9__servicio_catalogo',
    )


def lineas_incluidas_paquete(paquete):
    """Devuelve exclusivamente las lineas K9 configuradas en PaqueteServicio.

    D3 añade una identidad operacional estable para reconciliar revisiones
    contractuales sin duplicar ServicioEvento.
    """
    lineas = []
    for item in paquete.servicios_catalogo_k9.select_related('servicio_catalogo').all():
        servicio = item.servicio_catalogo
        lineage = f"INCLUIDO:package:{item.clave_origen or item.id}"
        lineas.append(
            _linea_dict(
                origen='PAQUETE_SERVICIO_K9',
                clave_origen=item.clave_origen,
                operational_lineage_key=lineage,
                servicio_catalogo_id=servicio.id,
                nombre=servicio.nombre,
                categoria=servicio.categoria,
                descripcion=servicio.descripcion or '',
                cantidad=_cantidad(item.cantidad),
                orden=item.orden,
                notas=item.notas or '',
                incluido=item.incluido,
                obligatorio=item.obligatorio,
            )
        )
    return lineas


def _calcular_base(propuesta, advertencias):
    paquete = propuesta.paquete
    adultos = int(propuesta.adultos or 0)
    ninos = int(propuesta.ninos or 0)
    cargo_fijo = _money(paquete.cargo_fijo)
    usa_tarifa_k9 = any(
        valor is not None and _money(valor) != Decimal('0.00')
        for valor in [paquete.precio_adulto, paquete.precio_nino, paquete.cargo_fijo]
    )

    if not usa_tarifa_k9:
        if paquete.precio_base:
            advertencias.append('Paquete legacy: se usa precio_base como subtotal base.')
        return _money(paquete.precio_base)

    subtotal = cargo_fijo
    if paquete.precio_adulto is None:
        if adultos:
            advertencias.append('Tarifa de adultos no configurada; adultos no suman al subtotal base.')
    else:
        subtotal += _money(paquete.precio_adulto) * adultos

    if paquete.precio_nino is None:
        if ninos:
            advertencias.append('Tarifa de ninos no configurada; ninos no suman al subtotal base.')
    else:
        subtotal += _money(paquete.precio_nino) * ninos

    return _money(subtotal)


def _advertencias_capacidad(propuesta, advertencias):
    total_personas = int(propuesta.adultos or 0) + int(propuesta.ninos or 0)
    paquete = propuesta.paquete
    if paquete.capacidad_minima_recomendada and total_personas < paquete.capacidad_minima_recomendada:
        advertencias.append(
            f'Capacidad por debajo de lo recomendado ({paquete.capacidad_minima_recomendada} personas).'
        )
    if paquete.capacidad_maxima_recomendada and total_personas > paquete.capacidad_maxima_recomendada:
        advertencias.append(
            f'Capacidad por encima de lo recomendado ({paquete.capacidad_maxima_recomendada} personas).'
        )


def calcular_subtotal_linea(linea, propuesta):
    if linea.tipo == 'CORTESIA':
        return Decimal('0.00')

    tarifa = _money(linea.tarifa)
    cantidad = _cantidad(linea.cantidad)
    modo = linea.modo_precio
    if modo == 'FIJO':
        return tarifa
    if modo == 'POR_ADULTO':
        return _money(tarifa * int(propuesta.adultos or 0))
    if modo == 'POR_NINO':
        return _money(tarifa * int(propuesta.ninos or 0))
    if modo == 'POR_PERSONA':
        return _money(tarifa * (int(propuesta.adultos or 0) + int(propuesta.ninos or 0)))
    if modo in {'POR_UNIDAD', 'MANUAL'}:
        return _money(tarifa * cantidad)
    raise ValidationError('Modo de precio no soportado.')


def _snapshot_linea(linea, subtotal, cantidad_aplicada):
    servicio = linea.servicio_catalogo
    lineage = (linea.snapshot_linea or {}).get('operational_lineage_key')
    if not lineage:
        lineage = f"{linea.tipo}:proposal-line:{linea.id}"
    return _linea_dict(
        linea_id=linea.id,
        operational_lineage_key=lineage,
        tipo=linea.tipo,
        servicio_catalogo_id=servicio.id if servicio else None,
        origen='CATALOGO' if servicio else 'MANUAL',
        nombre=linea.nombre,
        descripcion=linea.descripcion or '',
        modo_precio=linea.modo_precio,
        tarifa=_money(linea.tarifa),
        cantidad=linea.cantidad,
        cantidad_aplicada=cantidad_aplicada,
        subtotal=subtotal,
        valor_informativo=_money(linea.valor_informativo),
    )


def _cantidad_aplicada_linea(linea, propuesta):
    if linea.modo_precio == 'POR_ADULTO':
        return Decimal(int(propuesta.adultos or 0))
    if linea.modo_precio == 'POR_NINO':
        return Decimal(int(propuesta.ninos or 0))
    if linea.modo_precio == 'POR_PERSONA':
        return Decimal(int(propuesta.adultos or 0) + int(propuesta.ninos or 0))
    if linea.modo_precio in {'POR_UNIDAD', 'MANUAL'}:
        return _cantidad(linea.cantidad)
    return Decimal('1')


def calcular_propuesta(propuesta, *, usar_snapshot_aceptacion=True):
    if (
        usar_snapshot_aceptacion
        and propuesta.estado in PROPUESTA_ESTADOS_CONGELADOS
        and propuesta_tiene_snapshot_aceptacion(propuesta)
    ):
        return dto_desde_snapshot_aceptacion(propuesta.snapshot_aceptacion)

    advertencias = []
    _advertencias_capacidad(propuesta, advertencias)

    subtotal_base = _calcular_base(propuesta, advertencias)
    lineas_adicionales = []
    lineas_cortesia = []
    subtotal_adicionales = Decimal('0.00')

    for linea in propuesta.lineas.filter(activo=True).select_related('servicio_catalogo').order_by('orden', 'id'):
        subtotal_linea = calcular_subtotal_linea(linea, propuesta)
        cantidad_aplicada = _cantidad_aplicada_linea(linea, propuesta)
        snapshot = _snapshot_linea(linea, subtotal_linea, cantidad_aplicada)
        if linea.tipo == 'CORTESIA':
            lineas_cortesia.append(snapshot)
        else:
            lineas_adicionales.append(snapshot)
            subtotal_adicionales += subtotal_linea

    subtotal = _money(subtotal_base + subtotal_adicionales)
    descuento = _money(propuesta.descuento)
    total = _money(subtotal - descuento)
    if total < 0:
        total = Decimal('0.00')
        advertencias.append('El descuento excede el subtotal; el total se ajusto a cero.')
    if propuesta.estado in PROPUESTA_ESTADOS_CONGELADOS:
        advertencias.append('Propuesta aceptada sin snapshot D1: requiere normalizacion antes de contratar.')

    return {
        'evento_id': propuesta.evento_id,
        'empresa_id': propuesta.empresa_id,
        'sede': {
            'id': propuesta.sede_id,
            'nombre': propuesta.sede.nombre if propuesta.sede_id else '',
        },
        'adultos': int(propuesta.adultos or 0),
        'ninos': int(propuesta.ninos or 0),
        'paquete': {
            'id': propuesta.paquete_id,
            'nombre': propuesta.paquete.nombre,
            'descripcion': propuesta.paquete.descripcion or '',
        },
        'subtotal_base': subtotal_base,
        'lineas_incluidas': lineas_incluidas_paquete(propuesta.paquete),
        'lineas_adicionales': lineas_adicionales,
        'lineas_cortesia': lineas_cortesia,
        'descuento': descuento,
        'subtotal': subtotal,
        'total': total,
        'advertencias': advertencias,
        'version_calculo': PROPUESTA_VERSION_CALCULO,
    }


@transaction.atomic
def actualizar_totales_propuesta(propuesta, *, user=None):
    propuesta = (
        PropuestaEvento.objects.select_for_update()
        .select_related('empresa', 'evento', 'sede', 'paquete')
        .prefetch_related(
            'lineas__servicio_catalogo',
            'paquete__servicios_catalogo_k9__servicio_catalogo',
        )
        .get(pk=propuesta.pk)
    )
    if propuesta.estado in PROPUESTA_ESTADOS_CONGELADOS:
        if propuesta_tiene_snapshot_aceptacion(propuesta):
            return dto_desde_snapshot_aceptacion(propuesta.snapshot_aceptacion)
        raise ValidationError('Una propuesta aceptada o contratada no se puede recalcular sin reabrir negociacion.')
    dto = calcular_propuesta(propuesta)
    snapshots_lineas = {
        item['linea_id']: item
        for item in dto['lineas_adicionales'] + dto['lineas_cortesia']
        if item.get('linea_id')
    }
    for linea in propuesta.lineas.filter(pk__in=snapshots_lineas):
        snapshot = snapshots_lineas[linea.pk]
        linea.subtotal = _money(snapshot['subtotal'])
        linea.snapshot_linea = snapshot
        linea.save(update_fields=['subtotal', 'snapshot_linea', 'updated_at'])

    propuesta.subtotal_base = dto['subtotal_base']
    propuesta.subtotal = dto['subtotal']
    propuesta.total = dto['total']
    propuesta.version_calculo = dto['version_calculo']
    propuesta.desglose_calculado = {
        key: value
        for key, value in dto.items()
        if key not in {'subtotal_base', 'subtotal', 'total', 'descuento'}
    }
    propuesta.desglose_calculado.update(
        subtotal_base=str(dto['subtotal_base']),
        subtotal=str(dto['subtotal']),
        total=str(dto['total']),
        descuento=str(dto['descuento']),
    )
    if user is not None:
        propuesta.updated_by = user
    propuesta.full_clean()
    propuesta.save(
        update_fields=[
            'subtotal_base',
            'subtotal',
            'total',
            'version_calculo',
            'desglose_calculado',
            'updated_by',
            'updated_at',
        ]
    )
    return dto
