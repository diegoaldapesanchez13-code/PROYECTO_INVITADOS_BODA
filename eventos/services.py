from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.db.models import Max
from django.utils import timezone

from paquetes.models import PaqueteEvento, PropuestaEvento
from paquetes.services import actualizar_totales_propuesta

from .models import ContratoEvento, ParticipanteEvento


@transaction.atomic
def sincronizar_participantes_legacy(evento):
    """Sincroniza las relaciones legacy hacia ParticipanteEvento.

    Durante K.8.2 `EventoBoda.wedding_planner` y `EventoBoda.clientes` siguen
    funcionando para no romper vistas existentes. Este servicio mantiene el
    nuevo dominio alineado y es idempotente.
    """
    creados = 0
    actualizados = 0

    planner_ids = {evento.wedding_planner_id} if evento.wedding_planner_id else set()
    ParticipanteEvento.objects.filter(evento=evento, rol='PLANNER').exclude(
        usuario_id__in=planner_ids
    ).update(activo=False)

    if evento.wedding_planner_id:
        _, created = ParticipanteEvento.objects.update_or_create(
            evento=evento,
            usuario_id=evento.wedding_planner_id,
            rol='PLANNER',
            defaults={
                'activo': True,
                'puede_ver_finanzas': True,
                'puede_aprobar': True,
                'puede_gestionar_invitados': True,
                'puede_gestionar_servicios': True,
            },
        )
        creados += int(created)
        actualizados += int(not created)

    cliente_ids = set(evento.clientes.values_list('id', flat=True))
    ParticipanteEvento.objects.filter(evento=evento, rol='CLIENTE').exclude(
        usuario_id__in=cliente_ids
    ).update(activo=False)

    for usuario_id in cliente_ids:
        _, created = ParticipanteEvento.objects.update_or_create(
            evento=evento,
            usuario_id=usuario_id,
            rol='CLIENTE',
            defaults={
                'activo': True,
                'puede_aprobar': True,
                'puede_gestionar_invitados': True,
            },
        )
        creados += int(created)
        actualizados += int(not created)

    return {'creados': creados, 'actualizados': actualizados}


CONTRATO_SNAPSHOT_VERSION_K9 = 2


def _serializar_decimal(valor):
    if isinstance(valor, Decimal):
        return str(valor)
    if valor is None:
        return '0.00'
    return str(valor)


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
        'fecha_evento': evento.fecha_fiesta.isoformat() if evento.fecha_fiesta else None,
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
        'precio_base': _serializar_decimal(sede.precio_base),
    }


def _snapshot_paquete(paquete):
    return {
        'id': paquete.id,
        'nombre': paquete.nombre,
        'descripcion': paquete.descripcion or '',
        'precio_adulto': _serializar_decimal(paquete.precio_adulto),
        'precio_nino': _serializar_decimal(paquete.precio_nino),
        'cargo_fijo': _serializar_decimal(paquete.cargo_fijo),
        'duracion_evento': paquete.duracion_evento,
        'capacidad_minima_recomendada': paquete.capacidad_minima_recomendada,
        'capacidad_maxima_recomendada': paquete.capacidad_maxima_recomendada,
    }


def _limpiar_linea_incluida(linea):
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


def _limpiar_linea_adicional(linea):
    return {
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


def _limpiar_linea_cortesia(linea):
    return {
        'origen': linea.get('origen') or '',
        'servicio_catalogo_id': linea.get('servicio_catalogo_id'),
        'nombre': linea.get('nombre') or '',
        'descripcion': linea.get('descripcion') or '',
        'valor_informativo': str(linea.get('valor_informativo') or '0.00'),
        'cargo_cliente': '0.00',
    }


def construir_snapshot_v2_desde_propuesta(propuesta, dto, *, user=None):
    subtotal_base = Decimal(str(dto['subtotal_base']))
    subtotal = Decimal(str(dto['subtotal']))
    descuento = Decimal(str(dto['descuento']))
    total = Decimal(str(dto['total']))
    adicionales_total = subtotal - subtotal_base
    if adicionales_total < 0:
        adicionales_total = Decimal('0.00')
    fecha = timezone.now()

    return {
        'version': CONTRATO_SNAPSHOT_VERSION_K9,
        'fecha_generacion': fecha.isoformat(),
        'evento': _snapshot_evento(propuesta.evento),
        'empresa': _snapshot_empresa(propuesta.empresa),
        'paquete': _snapshot_paquete(propuesta.paquete),
        'sede': _snapshot_sede(propuesta.sede),
        'cantidades': {
            'adultos': propuesta.adultos,
            'ninos': propuesta.ninos,
            'total_personas': propuesta.adultos + propuesta.ninos,
        },
        'incluidos': [_limpiar_linea_incluida(linea) for linea in dto['lineas_incluidas']],
        'adicionales': [_limpiar_linea_adicional(linea) for linea in dto['lineas_adicionales']],
        'cortesias': [_limpiar_linea_cortesia(linea) for linea in dto['lineas_cortesia']],
        'descuentos': {
            'monto': _serializar_decimal(descuento),
        },
        'totales': {
            'base': _serializar_decimal(subtotal_base),
            'adicionales': _serializar_decimal(adicionales_total),
            'descuento': _serializar_decimal(descuento),
            'total_final': _serializar_decimal(total),
        },
        'notas_comerciales': propuesta.notas_comerciales or '',
        'metadata': {
            'version_calculo': dto['version_calculo'],
            'propuesta_origen_id': propuesta.id,
            'creado_por': user.id if user else None,
            'fecha': fecha.isoformat(),
        },
    }


def _siguiente_version_contrato(evento):
    version = ContratoEvento.objects.filter(evento=evento).aggregate(max_version=Max('version'))['max_version']
    return (version or 0) + 1


@transaction.atomic
def generar_contrato_v2_desde_propuesta(propuesta_id, *, user=None):
    propuesta = (
        PropuestaEvento.objects.select_for_update()
        .select_related('empresa', 'evento', 'sede', 'paquete')
        .prefetch_related(
            'lineas__servicio_catalogo',
            'paquete__servicios',
            'paquete__servicios_catalogo_k9__servicio_catalogo',
        )
        .get(pk=propuesta_id)
    )

    existente = ContratoEvento.objects.select_for_update().filter(propuesta_origen=propuesta).first()
    if existente:
        return existente

    if propuesta.estado != 'ACEPTADO':
        raise ValidationError('Solo una propuesta aceptada puede convertirse en contrato.')

    propuesta.full_clean()
    dto = actualizar_totales_propuesta(propuesta, user=user)
    propuesta.refresh_from_db()
    snapshot = construir_snapshot_v2_desde_propuesta(propuesta, dto, user=user)

    try:
        with transaction.atomic():
            contrato = ContratoEvento.objects.create(
                evento=propuesta.evento,
                numero_contrato=f'K9-{propuesta.evento_id}-{propuesta.id}',
                version=_siguiente_version_contrato(propuesta.evento),
                estado='CONTRATADO',
                monto_base=dto['total'],
                moneda='MXN',
                fecha_emision=timezone.localdate(),
                snapshot_comercial=snapshot,
                snapshot_version=CONTRATO_SNAPSHOT_VERSION_K9,
                propuesta_origen=propuesta,
                notas=propuesta.notas_comerciales or '',
                creado_por=user,
            )
    except IntegrityError:
        contrato = ContratoEvento.objects.select_for_update().get(propuesta_origen=propuesta)

    propuesta.estado = 'CONTRATADO'
    if user is not None:
        propuesta.updated_by = user
    propuesta.save(update_fields=['estado', 'updated_by', 'updated_at'])
    return contrato


def leer_contrato_v2(contrato):
    snapshot = contrato.snapshot_comercial or {}
    return {
        'version': snapshot.get('version') or contrato.snapshot_version,
        'contrato_id': contrato.id,
        'estado': contrato.estado,
        'evento': snapshot.get('evento') or {},
        'empresa': snapshot.get('empresa') or {},
        'sede': snapshot.get('sede') or {},
        'paquete': snapshot.get('paquete') or {},
        'cantidades': snapshot.get('cantidades') or {},
        'incluidos': snapshot.get('incluidos') or [],
        'adicionales': snapshot.get('adicionales') or [],
        'cortesias': snapshot.get('cortesias') or [],
        'descuentos': snapshot.get('descuentos') or {},
        'totales': snapshot.get('totales') or {},
        'notas_comerciales': snapshot.get('notas_comerciales') or '',
        'metadata': snapshot.get('metadata') or {},
    }


def leer_contrato_v1_paquete_evento(paquete_evento):
    snapshot = paquete_evento.snapshot_paquete or {}
    return {
        'version': snapshot.get('version') or 1,
        'contrato_id': None,
        'estado': paquete_evento.estado,
        'evento': {
            'id': paquete_evento.evento_id,
            'nombre': paquete_evento.evento.titulo_evento,
        },
        'empresa': _snapshot_empresa(paquete_evento.evento.empresa),
        'sede': _snapshot_sede(paquete_evento.evento.sede),
        'paquete': {
            'id': snapshot.get('paquete_id') or paquete_evento.paquete_id,
            'nombre': snapshot.get('nombre') or paquete_evento.paquete.nombre,
            'descripcion': snapshot.get('descripcion') or '',
        },
        'cantidades': {},
        'incluidos': [
            {
                'clave_origen': f"legacy:{item.get('servicio_paquete_id')}",
                'origen': 'SERVICIO_PAQUETE_LEGACY',
                'nombre': item.get('descripcion') or item.get('tipo_servicio_display') or '',
                'categoria': item.get('tipo_servicio') or '',
                'cantidad': str(item.get('cantidad') or '0'),
                'notas': '',
                'valor_comercial': str(item.get('precio_incluido') or '0.00'),
            }
            for item in snapshot.get('servicios', [])
        ],
        'adicionales': [],
        'cortesias': [],
        'descuentos': {'monto': str(snapshot.get('descuento') or paquete_evento.descuento)},
        'totales': {
            'base': str(snapshot.get('precio_acordado') or paquete_evento.precio_acordado),
            'adicionales': '0.00',
            'descuento': str(snapshot.get('descuento') or paquete_evento.descuento),
            'total_final': str(snapshot.get('total') or paquete_evento.total),
        },
        'notas_comerciales': paquete_evento.notas or '',
        'metadata': {'version_calculo': 1, 'paquete_evento_id': paquete_evento.id},
    }


def leer_contrato_interno(contrato):
    if contrato.snapshot_version == CONTRATO_SNAPSHOT_VERSION_K9:
        return leer_contrato_v2(contrato)
    return leer_contrato_v2(contrato)


def leer_contrato_publico(contrato):
    data = leer_contrato_interno(contrato)
    return {
        'version': data['version'],
        'contrato_id': data['contrato_id'],
        'estado': data['estado'],
        'evento': data['evento'],
        'sede': data['sede'],
        'paquete': data['paquete'],
        'cantidades': data['cantidades'],
        'incluidos': data['incluidos'],
        'adicionales': data['adicionales'],
        'cortesias': data['cortesias'],
        'descuentos': data['descuentos'],
        'totales': data['totales'],
    }
