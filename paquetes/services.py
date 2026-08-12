from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from proveedores.models import ServicioEvento

from .models import PaqueteEvento


MATERIALIZACION_VERSION = 1


def _decimal_a_texto(valor):
    return str(valor if valor is not None else Decimal('0'))


def construir_snapshot_paquete(paquete_evento):
    """Devuelve una representacion contractual serializable del paquete.

    No persiste cambios. El snapshot contiene solo datos necesarios para
    reconstruir el acuerdo aun si el catalogo maestro cambia posteriormente.
    """
    paquete = paquete_evento.paquete
    servicios = []
    for servicio in paquete.servicios.all().order_by('id'):
        servicios.append(
            {
                'servicio_paquete_id': servicio.pk,
                'tipo_servicio': servicio.tipo_servicio,
                'tipo_servicio_display': servicio.get_tipo_servicio_display(),
                'descripcion': servicio.descripcion,
                'cantidad': servicio.cantidad,
                'precio_incluido': _decimal_a_texto(servicio.precio_incluido),
            }
        )

    precio_acordado = paquete_evento.precio_acordado or paquete.precio_base
    return {
        'version': MATERIALIZACION_VERSION,
        'paquete_id': paquete.pk,
        'empresa_id': paquete.empresa_id,
        'nombre': paquete.nombre,
        'descripcion': paquete.descripcion or '',
        'precio_base': _decimal_a_texto(paquete.precio_base),
        'numero_personas_incluidas': paquete.numero_personas_incluidas,
        'precio_acordado': _decimal_a_texto(precio_acordado),
        'descuento': _decimal_a_texto(paquete_evento.descuento),
        'total': _decimal_a_texto(paquete_evento.total),
        'servicios': servicios,
    }


def validar_paquete_evento(paquete_evento):
    evento_empresa_id = getattr(paquete_evento.evento, 'empresa_id', None)
    paquete_empresa_id = getattr(paquete_evento.paquete, 'empresa_id', None)
    if evento_empresa_id and paquete_empresa_id and evento_empresa_id != paquete_empresa_id:
        raise ValidationError('El paquete y el evento pertenecen a empresas diferentes.')


@transaction.atomic
def capturar_snapshot_paquete(paquete_evento, *, reemplazar=False):
    """Congela el paquete maestro en PaqueteEvento.

    Es idempotente: si ya existe snapshot no lo modifica salvo que
    ``reemplazar=True``. Reemplazar esta pensado solo para estados previos a
    contratacion; una vez CONTRATADO no se permite reescribir el acuerdo.
    """
    paquete_evento = (
        PaqueteEvento.objects.select_for_update()
        .select_related('evento', 'paquete')
        .prefetch_related('paquete__servicios')
        .get(pk=paquete_evento.pk)
    )
    validar_paquete_evento(paquete_evento)

    if paquete_evento.snapshot_paquete and not reemplazar:
        return paquete_evento.snapshot_paquete
    if reemplazar and paquete_evento.estado == 'CONTRATADO' and paquete_evento.snapshot_paquete:
        raise ValidationError('No se puede reemplazar el snapshot de un paquete contratado.')

    snapshot = construir_snapshot_paquete(paquete_evento)
    paquete_evento.snapshot_paquete = snapshot
    paquete_evento.snapshot_generado_en = timezone.now()
    paquete_evento.materializacion_version = MATERIALIZACION_VERSION
    paquete_evento.save(
        update_fields=[
            'snapshot_paquete',
            'snapshot_generado_en',
            'materializacion_version',
        ]
    )
    return snapshot


def _estado_comercial_desde_paquete(paquete_evento):
    return {
        'PROPUESTO': 'PROPUESTO',
        'EN_REVISION': 'PROPUESTO',
        'APROBADO': 'APROBADO',
        'CONTRATADO': 'CONTRATADO',
        'CANCELADO': 'CANCELADO',
    }.get(paquete_evento.estado, 'BORRADOR')


@transaction.atomic
def materializar_servicios_paquete(paquete_evento, *, reemplazar_snapshot=False):
    """Crea/actualiza ServicioEvento independientes desde el snapshot.

    La operacion es idempotente. Cada ServicioPaquete maestro origina como
    maximo un ServicioEvento por PaqueteEvento; ejecutar nuevamente no duplica
    servicios. Los servicios resultantes conservan snapshots aun si el paquete
    maestro cambia.
    """
    paquete_evento = (
        PaqueteEvento.objects.select_for_update()
        .select_related('evento', 'paquete')
        .prefetch_related('paquete__servicios')
        .get(pk=paquete_evento.pk)
    )
    validar_paquete_evento(paquete_evento)

    if paquete_evento.estado == 'CANCELADO':
        raise ValidationError('No se puede materializar un paquete cancelado.')

    snapshot = capturar_snapshot_paquete(
        paquete_evento,
        reemplazar=reemplazar_snapshot,
    )

    servicios_maestros = {
        servicio.pk: servicio
        for servicio in paquete_evento.paquete.servicios.all()
    }
    creados = 0
    actualizados = 0
    ids = []
    estado_comercial = _estado_comercial_desde_paquete(paquete_evento)

    for item in snapshot.get('servicios', []):
        servicio_paquete_id = item.get('servicio_paquete_id')
        servicio_maestro = servicios_maestros.get(servicio_paquete_id)
        precio = Decimal(str(item.get('precio_incluido') or '0'))
        cantidad = max(int(item.get('cantidad') or 1), 1)
        defaults = {
            'evento': paquete_evento.evento,
            'origen': 'PAQUETE',
            'modalidad': 'INCLUIDO',
            'categoria': item.get('tipo_servicio') or '',
            'nombre_servicio': item.get('descripcion') or item.get('tipo_servicio_display') or 'Servicio incluido',
            'descripcion': item.get('descripcion') or '',

            # precio_incluido es el valor comercial atribuido al componente
            # dentro del paquete; NO es evidencia del costo real del proveedor.
            'valor_contratado': precio,
            'cargo_adicional_cliente': Decimal('0'),

            # Campos legacy: no inventamos costo de proveedor. precio_cliente se
            # conserva como espejo transitorio del valor comercial para no romper
            # pantallas antiguas hasta que migren a valor_contratado.
            'costo_total': Decimal('0'),
            'costo_proveedor': Decimal('0'),
            'precio_cliente': precio,
            'ajuste_cliente': Decimal('0'),
            'estado_comercial': estado_comercial,
            'estado_operativo': 'PENDIENTE',
            'paquete_nombre_snapshot': snapshot.get('nombre') or paquete_evento.paquete.nombre,
            'paquete_servicio_snapshot': item,
            'cantidad_paquete': cantidad,
        }

        if servicio_maestro is not None:
            servicio_evento, created = ServicioEvento.objects.update_or_create(
                paquete_evento=paquete_evento,
                servicio_paquete_origen=servicio_maestro,
                defaults=defaults,
            )
        else:
            # Si el item maestro fue eliminado despues de capturar el snapshot,
            # se conserva el acuerdo creando una instancia sin FK de origen.
            servicio_evento = ServicioEvento.objects.filter(
                paquete_evento=paquete_evento,
                servicio_paquete_origen__isnull=True,
                paquete_servicio_snapshot__servicio_paquete_id=servicio_paquete_id,
            ).first()
            if servicio_evento:
                for campo, valor in defaults.items():
                    setattr(servicio_evento, campo, valor)
                servicio_evento.save()
                created = False
            else:
                servicio_evento = ServicioEvento.objects.create(
                    paquete_evento=paquete_evento,
                    servicio_paquete_origen=None,
                    **defaults,
                )
                created = True

        ids.append(servicio_evento.pk)
        creados += int(created)
        actualizados += int(not created)

    paquete_evento.materializado_en = timezone.now()
    paquete_evento.materializacion_version = MATERIALIZACION_VERSION
    paquete_evento.save(update_fields=['materializado_en', 'materializacion_version'])

    return {
        'creados': creados,
        'actualizados': actualizados,
        'servicio_evento_ids': ids,
        'snapshot': snapshot,
    }
