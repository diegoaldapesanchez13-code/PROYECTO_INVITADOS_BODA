from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction

from core.services.authorization import Actions, usuario_puede_evento, usuario_tiene_permiso
from core.services.permisos import roles_usuario_empresa
from proveedores.models import ServicioEvento

from .models import PaqueteBoda, PropuestaEvento


PROPUESTA_VERSION_CALCULO = 1
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

    Esta funcion usa una unica fuente de verdad: PaqueteServicio.
    """
    lineas = []
    for item in paquete.servicios_catalogo_k9.select_related('servicio_catalogo').all():
        servicio = item.servicio_catalogo
        lineas.append(
            _linea_dict(
                origen='PAQUETE_SERVICIO_K9',
                clave_origen=item.clave_origen,
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
    return _linea_dict(
        linea_id=linea.id,
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


def calcular_propuesta(propuesta):
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
