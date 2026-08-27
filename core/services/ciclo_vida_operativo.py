"""Reglas de ciclo de vida operativo K9.8.

Este modulo separa cancelar/archivar/anular de la eliminacion fisica. Las vistas
se conectaran en K9.8B; K9.8A define solamente el dominio y su auditoria.
"""

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
from proveedores.service_lifecycle import aplicar_estado_operativo, servicio_cerrado

from core.services.auditoria import registrar_auditoria


def _actor(actor):
    return actor if getattr(actor, 'is_authenticated', False) else None


def _empresa_evento(obj):
    evento = getattr(obj, 'evento', None)
    if evento is None and hasattr(obj, 'gasto'):
        evento = getattr(obj.gasto, 'evento', None)
    return getattr(evento, 'empresa', None), evento


def _registrar(obj, *, actor, request, accion, anteriores, nuevos, descripcion):
    empresa, evento = _empresa_evento(obj)
    registrar_auditoria(
        usuario=_actor(actor),
        empresa=empresa,
        evento=evento,
        accion=accion,
        modelo=obj._meta.label,
        objeto_id=obj.pk,
        descripcion=descripcion,
        valores_anteriores=anteriores,
        valores_nuevos=nuevos,
        request=request,
    )


def _texto(valor):
    return (valor or '').strip() or None


@transaction.atomic
def cancelar_servicio_evento(servicio, *, actor=None, motivo=None, request=None):
    from proveedores.models import ServicioEvento

    servicio = ServicioEvento.objects.select_for_update().get(pk=servicio.pk)
    if servicio.estado_operativo == 'CANCELADO' and servicio.estado_comercial == 'CANCELADO':
        return servicio
    anteriores = {
        'estado': servicio.estado,
        'estado_comercial': servicio.estado_comercial,
        'estado_operativo': servicio.estado_operativo,
    }
    aplicar_estado_operativo(servicio, 'CANCELADO')
    servicio.cancelado_en = timezone.now()
    servicio.cancelado_por = _actor(actor)
    servicio.motivo_cancelacion = _texto(motivo)
    servicio.save(update_fields=[
        'estado', 'estado_comercial', 'estado_operativo', 'cancelado_en',
        'cancelado_por', 'motivo_cancelacion', 'fecha_actualizacion',
    ])
    _registrar(
        servicio,
        actor=actor,
        request=request,
        accion='servicio_evento.cancelar',
        anteriores=anteriores,
        nuevos={'estado': 'CANCELADO', 'estado_comercial': 'CANCELADO', 'estado_operativo': 'CANCELADO'},
        descripcion=f'Servicio cancelado: {servicio.nombre_servicio}',
    )
    return servicio


@transaction.atomic
def archivar_servicio_evento(servicio, *, actor=None, request=None):
    from proveedores.models import ServicioEvento

    servicio = ServicioEvento.objects.select_for_update().get(pk=servicio.pk)
    if servicio.archivado_en:
        return servicio
    if not servicio_cerrado(servicio):
        # Compatibility for untouched pre-D4 rows whose old terminal state was
        # written only into the legacy field.
        if servicio.estado not in {'CANCELADO', 'SERVICIO_COMPLETADO'}:
            raise ValidationError('Solo se puede archivar un servicio cancelado o completado.')
    servicio.archivado_en = timezone.now()
    servicio.archivado_por = _actor(actor)
    servicio.save(update_fields=['archivado_en', 'archivado_por', 'fecha_actualizacion'])
    _registrar(
        servicio,
        actor=actor,
        request=request,
        accion='servicio_evento.archivar',
        anteriores={'archivado': False},
        nuevos={'archivado': True},
        descripcion=f'Servicio archivado: {servicio.nombre_servicio}',
    )
    return servicio


@transaction.atomic
def desarchivar_servicio_evento(servicio, *, actor=None, request=None):
    from proveedores.models import ServicioEvento

    servicio = ServicioEvento.objects.select_for_update().get(pk=servicio.pk)
    if not servicio.archivado_en:
        return servicio
    servicio.archivado_en = None
    servicio.archivado_por = None
    servicio.save(update_fields=['archivado_en', 'archivado_por', 'fecha_actualizacion'])
    _registrar(servicio, actor=actor, request=request, accion='servicio_evento.desarchivar',
               anteriores={'archivado': True}, nuevos={'archivado': False},
               descripcion=f'Servicio restaurado del archivo: {servicio.nombre_servicio}')
    return servicio


@transaction.atomic
def cancelar_tarea_evento(tarea, *, actor=None, motivo=None, request=None):
    from tareas.models import TareaEvento

    tarea = TareaEvento.objects.select_for_update().get(pk=tarea.pk)
    if tarea.estado == 'CANCELADA':
        return tarea
    anterior = tarea.estado
    tarea.estado = 'CANCELADA'
    tarea.cancelado_en = timezone.now()
    tarea.cancelado_por = _actor(actor)
    tarea.motivo_cancelacion = _texto(motivo)
    tarea.save(update_fields=['estado', 'cancelado_en', 'cancelado_por', 'motivo_cancelacion', 'fecha_actualizacion'])
    _registrar(tarea, actor=actor, request=request, accion='tarea_evento.cancelar',
               anteriores={'estado': anterior}, nuevos={'estado': 'CANCELADA'},
               descripcion=f'Tarea cancelada: {tarea.titulo}')
    return tarea


@transaction.atomic
def archivar_tarea_evento(tarea, *, actor=None, request=None):
    from tareas.models import TareaEvento

    tarea = TareaEvento.objects.select_for_update().get(pk=tarea.pk)
    if tarea.archivado_en:
        return tarea
    if tarea.estado not in {'COMPLETADA', 'CANCELADA'}:
        raise ValidationError('Solo se puede archivar una tarea completada o cancelada.')
    tarea.archivado_en = timezone.now()
    tarea.archivado_por = _actor(actor)
    tarea.save(update_fields=['archivado_en', 'archivado_por', 'fecha_actualizacion'])
    _registrar(tarea, actor=actor, request=request, accion='tarea_evento.archivar',
               anteriores={'archivado': False}, nuevos={'archivado': True},
               descripcion=f'Tarea archivada: {tarea.titulo}')
    return tarea


@transaction.atomic
def desarchivar_tarea_evento(tarea, *, actor=None, request=None):
    from tareas.models import TareaEvento

    tarea = TareaEvento.objects.select_for_update().get(pk=tarea.pk)
    if not tarea.archivado_en:
        return tarea
    tarea.archivado_en = None
    tarea.archivado_por = None
    tarea.save(update_fields=['archivado_en', 'archivado_por', 'fecha_actualizacion'])
    _registrar(tarea, actor=actor, request=request, accion='tarea_evento.desarchivar',
               anteriores={'archivado': True}, nuevos={'archivado': False},
               descripcion=f'Tarea restaurada del archivo: {tarea.titulo}')
    return tarea


@transaction.atomic
def cancelar_actividad_itinerario(actividad, *, actor=None, motivo=None, request=None):
    from itinerario.models import ActividadItinerario

    actividad = ActividadItinerario.objects.select_for_update().get(pk=actividad.pk)
    if actividad.estado == 'CANCELADA':
        return actividad
    anterior = actividad.estado
    actividad.estado = 'CANCELADA'
    actividad.cancelado_en = timezone.now()
    actividad.cancelado_por = _actor(actor)
    actividad.motivo_cancelacion = _texto(motivo)
    actividad.save(update_fields=['estado', 'cancelado_en', 'cancelado_por', 'motivo_cancelacion'])
    _registrar(actividad, actor=actor, request=request, accion='actividad_itinerario.cancelar',
               anteriores={'estado': anterior}, nuevos={'estado': 'CANCELADA'},
               descripcion=f'Actividad cancelada: {actividad.titulo}')
    return actividad


@transaction.atomic
def archivar_actividad_itinerario(actividad, *, actor=None, request=None):
    from itinerario.models import ActividadItinerario

    actividad = ActividadItinerario.objects.select_for_update().get(pk=actividad.pk)
    if actividad.archivado_en:
        return actividad
    if actividad.estado not in {'COMPLETADA', 'CANCELADA'}:
        raise ValidationError('Solo se puede archivar una actividad completada o cancelada.')
    actividad.archivado_en = timezone.now()
    actividad.archivado_por = _actor(actor)
    actividad.save(update_fields=['archivado_en', 'archivado_por'])
    _registrar(actividad, actor=actor, request=request, accion='actividad_itinerario.archivar',
               anteriores={'archivado': False}, nuevos={'archivado': True},
               descripcion=f'Actividad archivada: {actividad.titulo}')
    return actividad


@transaction.atomic
def desarchivar_actividad_itinerario(actividad, *, actor=None, request=None):
    from itinerario.models import ActividadItinerario

    actividad = ActividadItinerario.objects.select_for_update().get(pk=actividad.pk)
    if not actividad.archivado_en:
        return actividad
    actividad.archivado_en = None
    actividad.archivado_por = None
    actividad.save(update_fields=['archivado_en', 'archivado_por'])
    _registrar(actividad, actor=actor, request=request, accion='actividad_itinerario.desarchivar',
               anteriores={'archivado': True}, nuevos={'archivado': False},
               descripcion=f'Actividad restaurada del archivo: {actividad.titulo}')
    return actividad


@transaction.atomic
def archivar_documento_evento(documento, *, actor=None, motivo=None, request=None):
    from documentos.models import DocumentoEvento

    documento = DocumentoEvento.objects.select_for_update().get(pk=documento.pk)
    if documento.archivado_en:
        return documento
    documento.archivado_en = timezone.now()
    documento.archivado_por = _actor(actor)
    documento.motivo_archivo = _texto(motivo)
    documento.save(update_fields=['archivado_en', 'archivado_por', 'motivo_archivo'])
    _registrar(documento, actor=actor, request=request, accion='documento_evento.archivar',
               anteriores={'archivado': False}, nuevos={'archivado': True},
               descripcion=f'Documento archivado: {documento.titulo}')
    return documento


@transaction.atomic
def desarchivar_documento_evento(documento, *, actor=None, request=None):
    from documentos.models import DocumentoEvento

    documento = DocumentoEvento.objects.select_for_update().get(pk=documento.pk)
    if not documento.archivado_en:
        return documento
    documento.archivado_en = None
    documento.archivado_por = None
    documento.motivo_archivo = None
    documento.save(update_fields=['archivado_en', 'archivado_por', 'motivo_archivo'])
    _registrar(documento, actor=actor, request=request, accion='documento_evento.desarchivar',
               anteriores={'archivado': True}, nuevos={'archivado': False},
               descripcion=f'Documento restaurado del archivo: {documento.titulo}')
    return documento


@transaction.atomic
def cancelar_gasto_evento(gasto, *, actor=None, motivo=None, request=None):
    from presupuesto.models import GastoEvento

    gasto = GastoEvento.objects.select_for_update().get(pk=gasto.pk)
    if gasto.estado == 'CANCELADO':
        return gasto
    if gasto.pagos.filter(estado='ACTIVO').exists():
        raise ValidationError('No se puede cancelar un gasto con pagos activos. Anula primero sus pagos.')
    anterior = gasto.estado
    gasto.estado = 'CANCELADO'
    gasto.cancelado_en = timezone.now()
    gasto.cancelado_por = _actor(actor)
    gasto.motivo_cancelacion = _texto(motivo)
    gasto.save(update_fields=['estado', 'cancelado_en', 'cancelado_por', 'motivo_cancelacion', 'fecha_actualizacion'])
    _registrar(gasto, actor=actor, request=request, accion='gasto_evento.cancelar',
               anteriores={'estado': anterior}, nuevos={'estado': 'CANCELADO'},
               descripcion=f'Gasto cancelado: {gasto.concepto}')
    return gasto


@transaction.atomic
def archivar_gasto_evento(gasto, *, actor=None, request=None):
    from presupuesto.models import GastoEvento

    gasto = GastoEvento.objects.select_for_update().get(pk=gasto.pk)
    if gasto.archivado_en:
        return gasto
    if gasto.estado not in {'PAGADO', 'CANCELADO'}:
        raise ValidationError('Solo se puede archivar un gasto pagado o cancelado.')
    gasto.archivado_en = timezone.now()
    gasto.archivado_por = _actor(actor)
    gasto.save(update_fields=['archivado_en', 'archivado_por', 'fecha_actualizacion'])
    _registrar(gasto, actor=actor, request=request, accion='gasto_evento.archivar',
               anteriores={'archivado': False}, nuevos={'archivado': True},
               descripcion=f'Gasto archivado: {gasto.concepto}')
    return gasto


@transaction.atomic
def desarchivar_gasto_evento(gasto, *, actor=None, request=None):
    from presupuesto.models import GastoEvento

    gasto = GastoEvento.objects.select_for_update().get(pk=gasto.pk)
    if not gasto.archivado_en:
        return gasto
    gasto.archivado_en = None
    gasto.archivado_por = None
    gasto.save(update_fields=['archivado_en', 'archivado_por', 'fecha_actualizacion'])
    _registrar(gasto, actor=actor, request=request, accion='gasto_evento.desarchivar',
               anteriores={'archivado': True}, nuevos={'archivado': False},
               descripcion=f'Gasto restaurado del archivo: {gasto.concepto}')
    return gasto


@transaction.atomic
def anular_pago_evento(pago, *, actor=None, motivo=None, request=None):
    from presupuesto.models import PagoEvento

    pago = PagoEvento.objects.select_for_update().select_related('gasto__evento').get(pk=pago.pk)
    if pago.estado == 'ANULADO':
        return pago
    pago.estado = 'ANULADO'
    pago.anulado_en = timezone.now()
    pago.anulado_por = _actor(actor)
    pago.motivo_anulacion = _texto(motivo)
    pago.save(update_fields=['estado', 'anulado_en', 'anulado_por', 'motivo_anulacion'])
    _registrar(pago, actor=actor, request=request, accion='pago_evento.anular',
               anteriores={'estado': 'ACTIVO'}, nuevos={'estado': 'ANULADO'},
               descripcion=f'Pago operativo anulado: {pago.monto}')
    return pago
