from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.db.models import Max
from django.utils import timezone

from catalogo.models import ServicioCatalogo
from paquetes.models import PropuestaEvento
from paquetes.services import (
    PROPUESTA_SNAPSHOT_ACEPTACION_VERSION,
    propuesta_tiene_snapshot_aceptacion,
)
from proveedores.models import ServicioEvento
from proveedores.service_lifecycle import (
    aplicar_estado_comercial,
    aplicar_estado_operativo,
    sincronizar_estado_legacy,
)

from .models import ContratoEvento, ParticipanteEvento
from .selectors import CONTRATO_ESTADOS_VIGENTES


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
        participante, created = ParticipanteEvento.objects.get_or_create(
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
        if not created and not participante.activo:
            # La relacion legacy solo reactiva la pertenencia. Los permisos
            # pueden haber sido personalizados por la empresa y no deben
            # volver a sus valores iniciales durante una sincronizacion.
            participante.activo = True
            participante.save(update_fields=['activo', 'fecha_actualizacion'])
        creados += int(created)
        actualizados += int(not created)

    cliente_ids = set(evento.clientes.values_list('id', flat=True))
    ParticipanteEvento.objects.filter(evento=evento, rol='CLIENTE').exclude(
        usuario_id__in=cliente_ids
    ).update(activo=False)

    for usuario_id in cliente_ids:
        participante, created = ParticipanteEvento.objects.get_or_create(
            evento=evento,
            usuario_id=usuario_id,
            rol='CLIENTE',
            defaults={
                'activo': True,
                'puede_aprobar': True,
                'puede_gestionar_invitados': True,
            },
        )
        if not created and not participante.activo:
            participante.activo = True
            participante.save(update_fields=['activo', 'fecha_actualizacion'])
        creados += int(created)
        actualizados += int(not created)

    return {'creados': creados, 'actualizados': actualizados}


CONTRATO_SNAPSHOT_VERSION_K9 = 2
MATERIALIZACION_VERSION_K9 = 2
MONEY = Decimal('0.01')


def _serializar_decimal(valor):
    if isinstance(valor, Decimal):
        return str(valor)
    if valor is None:
        return '0.00'
    return str(valor)


def _money(valor):
    return Decimal(str(valor if valor is not None else '0')).quantize(MONEY)


def _snapshot_empresa(empresa):
    return {
        'id': empresa.id if empresa else None,
        'nombre': empresa.nombre_comercial if empresa else '',
        'razon_social': getattr(empresa, 'razon_social', '') or '',
    }


def _snapshot_evento(evento):
    fecha_evento = evento.fecha_inicio or evento.fecha_fiesta
    return {
        'id': evento.id,
        'nombre': evento.titulo_evento,
        'tipo': evento.tipo_evento,
        'fecha_evento': fecha_evento.isoformat() if fecha_evento else None,
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
        'operational_lineage_key': linea.get('operational_lineage_key') or '',
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
        'operational_lineage_key': linea.get('operational_lineage_key') or '',
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
        'operational_lineage_key': linea.get('operational_lineage_key') or '',
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


def construir_snapshot_v2_desde_aceptacion(propuesta, *, user=None):
    if not propuesta_tiene_snapshot_aceptacion(propuesta):
        raise ValidationError(
            'La propuesta aceptada no tiene snapshot de aceptacion D1. Reabre y acepta nuevamente.'
        )

    aceptacion = propuesta.snapshot_aceptacion
    fecha = timezone.now()
    metadata = dict(aceptacion.get('metadata') or {})
    metadata.update(
        {
            'snapshot_aceptacion_version': PROPUESTA_SNAPSHOT_ACEPTACION_VERSION,
            'fecha_aceptacion': aceptacion.get('fecha_aceptacion'),
            'aceptado_por': aceptacion.get('aceptado_por'),
            'contrato_creado_por': user.id if user else None,
            'fecha': fecha.isoformat(),
        }
    )

    return {
        'version': CONTRATO_SNAPSHOT_VERSION_K9,
        'fecha_generacion': fecha.isoformat(),
        'evento': aceptacion.get('evento') or {},
        'empresa': aceptacion.get('empresa') or {},
        'paquete': aceptacion.get('paquete') or {},
        'sede': aceptacion.get('sede') or {},
        'cantidades': aceptacion.get('cantidades') or {},
        'incluidos': aceptacion.get('incluidos') or [],
        'adicionales': aceptacion.get('adicionales') or [],
        'cortesias': aceptacion.get('cortesias') or [],
        'descuentos': aceptacion.get('descuentos') or {},
        'totales': aceptacion.get('totales') or {},
        'notas_comerciales': aceptacion.get('notas_comerciales') or '',
        'metadata': metadata,
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
            'paquete__servicios_catalogo_k9__servicio_catalogo',
        )
        .get(pk=propuesta_id)
    )

    existente = ContratoEvento.objects.select_for_update().filter(propuesta_origen=propuesta).first()
    if existente:
        return existente

    if propuesta.estado != 'ACEPTADO':
        raise ValidationError('Solo una propuesta aceptada puede convertirse en contrato.')
    if not propuesta_tiene_snapshot_aceptacion(propuesta):
        raise ValidationError(
            'La propuesta aceptada no tiene snapshot de aceptacion D1. Reabre y acepta nuevamente.'
        )

    propuesta.full_clean()
    snapshot = construir_snapshot_v2_desde_aceptacion(propuesta, user=user)
    total_contratado = _money((snapshot.get('totales') or {}).get('total_final'))

    try:
        with transaction.atomic():
            contrato = ContratoEvento.objects.create(
                evento=propuesta.evento,
                numero_contrato=f'K9-{propuesta.evento_id}-{propuesta.id}',
                version=_siguiente_version_contrato(propuesta.evento),
                estado='CONTRATADO',
                monto_base=total_contratado,
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

    # D2: the freshly generated K9 contract becomes the single current
    # contract. Older active contracts are history, never deleted.
    (
        ContratoEvento.objects.select_for_update()
        .filter(
            evento=propuesta.evento,
            estado__in=CONTRATO_ESTADOS_VIGENTES,
        )
        .exclude(pk=contrato.pk)
        .update(estado='REEMPLAZADO')
    )

    propuesta.estado = 'CONTRATADO'
    if user is not None:
        propuesta.updated_by = user
    propuesta.save(update_fields=['estado', 'updated_by', 'updated_at'])
    return contrato


def _linea_key(tipo, item, posicion):
    lineage = (item.get('operational_lineage_key') or '').strip()
    if lineage:
        return lineage
    base = (
        item.get('linea_key')
        or item.get('clave_origen')
        or item.get('linea_id')
        or f'{posicion:04d}'
    )
    return f'{tipo}:{base}'


def _lineas_snapshot_v2(snapshot):
    for tipo, seccion in (
        ('INCLUIDO', 'incluidos'),
        ('ADICIONAL', 'adicionales'),
        ('CORTESIA', 'cortesias'),
    ):
        for posicion, item in enumerate(snapshot.get(seccion) or [], start=1):
            yield tipo, _linea_key(tipo, item, posicion), item


def _catalogo_k9_para_linea(item, empresa_id):
    servicio_catalogo_id = item.get('servicio_catalogo_id')
    if not servicio_catalogo_id:
        return None
    return ServicioCatalogo.objects.filter(
        pk=servicio_catalogo_id,
        empresa_id=empresa_id,
    ).first()


def _cantidad_operativa(tipo, item):
    valor = item.get('cantidad_aplicada') if tipo == 'ADICIONAL' else item.get('cantidad')
    try:
        cantidad = int(Decimal(str(valor if valor is not None else '1')))
    except Exception:
        cantidad = 1
    return max(cantidad, 1)


def _valor_contratado_linea(tipo, item):
    if tipo == 'ADICIONAL':
        return _money(item.get('subtotal'))
    if tipo == 'CORTESIA':
        return _money(item.get('valor_informativo'))
    return _money(item.get('valor_comercial'))


def _cargo_cliente_linea(tipo, item):
    if tipo == 'ADICIONAL':
        return _money(item.get('subtotal'))
    return Decimal('0.00')


def _snapshot_linea_materializada(contrato, tipo, linea_key, item):
    data = {
        'contrato_id': contrato.id,
        'snapshot_version': contrato.snapshot_version,
        'linea_key': linea_key,
        'tipo': tipo,
        'nombre': item.get('nombre') or '',
        'descripcion': item.get('descripcion') or '',
        'cantidad': str(item.get('cantidad') or ''),
        'modo_precio': item.get('modo_precio') or '',
        'tarifa': str(item.get('tarifa') or '0.00'),
        'subtotal': str(item.get('subtotal') or '0.00'),
    }
    if tipo == 'ADICIONAL':
        data['cantidad_aplicada'] = str(item.get('cantidad_aplicada') or '0')
    if tipo == 'CORTESIA':
        data['valor_informativo'] = str(item.get('valor_informativo') or '0.00')
        data['cargo_cliente'] = '0.00'
    return data


def _defaults_servicio_materializado(contrato, tipo, linea_key, item):
    nombre = (item.get('nombre') or '').strip()
    if not nombre:
        raise ValidationError('No se puede materializar una linea contractual sin nombre.')

    modalidad = tipo
    origen_snapshot = item.get('origen') or ''
    if tipo == 'INCLUIDO':
        origen = 'PAQUETE'
    elif origen_snapshot == 'CATALOGO':
        origen = 'CATALOGO'
    else:
        origen = 'MANUAL'

    valor_contratado = _valor_contratado_linea(tipo, item)
    cargo_cliente = _cargo_cliente_linea(tipo, item)
    catalogo_k9 = _catalogo_k9_para_linea(item, contrato.evento.empresa_id)
    descripcion = item.get('descripcion') or item.get('notas') or ''

    return {
        'evento': contrato.evento,
        'servicio_catalogo_k9': catalogo_k9,
        'origen': origen,
        'modalidad': modalidad,
        'categoria': item.get('categoria') or '',
        'nombre_servicio': nombre,
        'descripcion': descripcion,
        'valor_contratado': valor_contratado,
        'cargo_adicional_cliente': cargo_cliente,
        'paquete_nombre_snapshot': (contrato.snapshot_comercial.get('paquete') or {}).get('nombre') or '',
        'paquete_servicio_snapshot': item if tipo == 'INCLUIDO' else {},
        'cantidad_paquete': _cantidad_operativa(tipo, item),
        'snapshot_linea': _snapshot_linea_materializada(contrato, tipo, linea_key, item),
        'materializacion_version': MATERIALIZACION_VERSION_K9,
    }



def _lineage_history(servicio):
    snapshot = dict(servicio.snapshot_linea or {})
    history = list(snapshot.get('historial_contractual') or [])
    if servicio.contrato_origen_id:
        current = {
            'contrato_id': servicio.contrato_origen_id,
            'linea_key': servicio.linea_origen_key,
            'snapshot': {
                key: value
                for key, value in snapshot.items()
                if key != 'historial_contractual'
            },
        }
        if not history or history[-1].get('contrato_id') != current['contrato_id']:
            history.append(current)
    return history


def _candidate_previous_service(contrato, tipo, linea_key, item):
    qs = (
        ServicioEvento.objects.select_for_update()
        .filter(evento=contrato.evento)
        .exclude(contrato_origen=contrato)
        .exclude(estado_comercial='CANCELADO')
    )

    exact = qs.filter(linea_origen_key=linea_key).order_by('-contrato_origen__version', '-id').first()
    if exact:
        return exact

    # Compatibility for pre-D3 snapshots that did not persist the lineage key.
    catalogo_id = item.get('servicio_catalogo_id')
    semantic = qs.filter(modalidad=tipo)
    if catalogo_id:
        semantic = semantic.filter(servicio_catalogo_k9_id=catalogo_id)
    else:
        semantic = semantic.filter(nombre_servicio__iexact=(item.get('nombre') or '').strip())

    candidates = list(semantic.order_by('-contrato_origen__version', '-id')[:2])
    if len(candidates) == 1:
        return candidates[0]
    if len(candidates) > 1:
        raise ValidationError(
            f'No se puede reconciliar automaticamente la linea "{item.get("nombre") or linea_key}": '
            'hay mas de un servicio operativo compatible.'
        )
    return None


def _related_exists(servicio, related_name):
    relation = getattr(servicio, related_name, None)
    if relation is None:
        return False
    try:
        return relation.exists()
    except Exception:
        return False


def _servicio_tiene_huella_operativa(servicio):
    if servicio.estado_operativo == 'CANCELADO':
        return False
    if servicio.proveedor_id:
        return True
    if servicio.costo_proveedor and servicio.costo_proveedor != Decimal('0.00'):
        return True
    if servicio.estado_operativo not in {'PENDIENTE', 'EN_DEFINICION'}:
        return True
    if servicio.estado_proveedor != 'PENDIENTE':
        return True

    related_names = (
        'expediente_colaboracion',
        'temas_workspace',
        'conversaciones_workspace',
        'referencias_workspace',
        'decisiones_workspace',
        'cotizaciones_workspace',
        'propuestas_workspace',
        'ajustes_contractuales',
        'aprobaciones_workspace',
        'documentos_operativos',
        'tareas_operativas',
        'actividades_agenda',
        'gastos_operativos',
        'pagos_cliente_evento',
    )
    for related_name in related_names:
        relation = getattr(servicio, related_name, None)
        if relation is None:
            continue
        try:
            if hasattr(relation, 'exists') and relation.exists():
                return True
            if getattr(relation, 'pk', None):
                return True
        except Exception:
            continue
    return False


def _reconciliar_servicio_existente(servicio, contrato, tipo, linea_key, item):
    history = _lineage_history(servicio)
    servicio = _actualizar_servicio_materializado(
        servicio, contrato, tipo, linea_key, item, history=history
    )
    return servicio


def _retirar_servicio_por_revision(servicio, contrato, *, user=None):
    if servicio.estado_operativo == 'CANCELADO':
        return 'ya_cancelado'
    if _servicio_tiene_huella_operativa(servicio):
        raise ValidationError(
            f'El servicio "{servicio.nombre_servicio}" fue retirado del contrato v{contrato.version}, '
            'pero ya tiene operacion vinculada. Cancela/resuelve ese servicio explicitamente y vuelve a materializar.'
        )

    aplicar_estado_operativo(servicio, 'CANCELADO')
    servicio.cancelado_en = timezone.now()
    servicio.cancelado_por = user
    servicio.motivo_cancelacion = (
        f'Retirado automaticamente por revision contractual v{contrato.version}.'
    )
    servicio.save(
        update_fields=[
            'estado',
            'estado_comercial',
            'estado_operativo',
            'cancelado_en',
            'cancelado_por',
            'motivo_cancelacion',
            'fecha_actualizacion',
        ]
    )
    return 'cancelado'

def _crear_servicio_materializado(contrato, tipo, linea_key, item):
    defaults = _defaults_servicio_materializado(contrato, tipo, linea_key, item)
    servicio = ServicioEvento(
        contrato_origen=contrato,
        linea_origen_key=linea_key,
        proveedor=None,
        costo_proveedor=Decimal('0.00'),
        prestacion_tipo='POR_DEFINIR',
        estado='CONTRATADO',
        estado_comercial='CONTRATADO',
        estado_operativo='PENDIENTE',
        **defaults,
    )
    sincronizar_estado_legacy(servicio)
    servicio.full_clean()
    servicio.save()
    return servicio


def _actualizar_servicio_materializado(servicio, contrato, tipo, linea_key, item, history=None):
    defaults = _defaults_servicio_materializado(contrato, tipo, linea_key, item)
    if history:
        defaults['snapshot_linea']['historial_contractual'] = history
    campos_contractuales = [
        'evento',
        'servicio_catalogo_k9',
        'origen',
        'modalidad',
        'categoria',
        'nombre_servicio',
        'descripcion',
        'valor_contratado',
        'cargo_adicional_cliente',
        'paquete_nombre_snapshot',
        'paquete_servicio_snapshot',
        'cantidad_paquete',
        'snapshot_linea',
        'materializacion_version',
    ]
    for campo in campos_contractuales:
        setattr(servicio, campo, defaults[campo])
    servicio.contrato_origen = contrato
    servicio.linea_origen_key = linea_key
    aplicar_estado_comercial(servicio, 'CONTRATADO')
    if servicio.estado_operativo == 'CANCELADO' and not servicio.cancelado_en:
        # Compatibility only for a malformed historical row with no real
        # cancellation metadata.
        servicio.estado_operativo = 'PENDIENTE'
        sincronizar_estado_legacy(servicio)
    servicio.full_clean()
    servicio.save(
        update_fields=campos_contractuales
        + [
            'contrato_origen',
            'linea_origen_key',
            'estado_comercial',
            'estado_operativo',
            'fecha_actualizacion',
        ]
    )
    return servicio


@transaction.atomic
def materializar_servicios_contrato_v2(contrato_id, *, user=None):
    contrato = (
        ContratoEvento.objects.select_for_update()
        .select_related('evento', 'evento__empresa')
        .get(pk=contrato_id)
    )
    snapshot = contrato.snapshot_comercial or {}

    if contrato.estado == 'CANCELADO':
        raise ValidationError('No se puede materializar un contrato cancelado.')
    if contrato.estado != 'CONTRATADO':
        raise ValidationError('Solo un contrato contratado puede materializar servicios.')
    if contrato.snapshot_version != CONTRATO_SNAPSHOT_VERSION_K9 or snapshot.get('version') != CONTRATO_SNAPSHOT_VERSION_K9:
        raise ValidationError('Solo se puede materializar snapshot comercial v2.')

    # Only the current K9 contract may own the current operation.
    from .selectors import contrato_es_materializable
    if not contrato_es_materializable(contrato):
        raise ValidationError('Solo el contrato K9 vigente puede materializar o reconciliar operacion.')

    creados = 0
    actualizados = 0
    reutilizados = 0
    retirados = 0
    ids = []
    lineas = list(_lineas_snapshot_v2(snapshot))
    keys = [linea_key for _, linea_key, _ in lineas]
    if len(keys) != len(set(keys)):
        raise ValidationError('El snapshot contiene claves de linea duplicadas.')

    previous_services = list(
        ServicioEvento.objects.select_for_update()
        .filter(evento=contrato.evento, contrato_origen__version__lt=contrato.version)
        .exclude(estado_comercial='CANCELADO')
        .order_by('-contrato_origen__version', 'id')
    )
    matched_previous_ids = set()

    for tipo, linea_key, item in lineas:
        servicio = ServicioEvento.objects.select_for_update().filter(
            contrato_origen=contrato,
            linea_origen_key=linea_key,
        ).first()

        if servicio:
            servicio = _actualizar_servicio_materializado(servicio, contrato, tipo, linea_key, item)
            actualizados += 1
        else:
            servicio = _candidate_previous_service(contrato, tipo, linea_key, item)
            if servicio:
                matched_previous_ids.add(servicio.id)
                servicio = _reconciliar_servicio_existente(servicio, contrato, tipo, linea_key, item)
                reutilizados += 1
            else:
                servicio = _crear_servicio_materializado(contrato, tipo, linea_key, item)
                creados += 1

        ids.append(servicio.id)

    # Anything from the immediately previous operational contract that did
    # not continue in the new snapshot is a removed line. Pristine services
    # are cancelled; real operation must be resolved explicitly by the user.
    previous_contract = (
        ContratoEvento.objects.filter(evento=contrato.evento, version__lt=contrato.version)
        .order_by('-version', '-id')
        .first()
    )
    if previous_contract:
        removed = (
            ServicioEvento.objects.select_for_update()
            .filter(evento=contrato.evento, contrato_origen=previous_contract)
            .exclude(pk__in=matched_previous_ids)
            .exclude(pk__in=ids)
        )
        for servicio in removed:
            result = _retirar_servicio_por_revision(servicio, contrato, user=user)
            if result == 'cancelado':
                retirados += 1

    contrato.materializado_en = timezone.now()
    contrato.materializacion_version = MATERIALIZACION_VERSION_K9
    contrato.save(update_fields=['materializado_en', 'materializacion_version', 'fecha_actualizacion'])

    return {
        'creados': creados,
        'actualizados': actualizados,
        'reutilizados': reutilizados,
        'retirados': retirados,
        'servicio_evento_ids': ids,
        'materializacion_version': MATERIALIZACION_VERSION_K9,
    }


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
