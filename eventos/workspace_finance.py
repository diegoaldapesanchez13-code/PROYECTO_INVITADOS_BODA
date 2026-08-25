from decimal import Decimal

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.db.models import Sum
from django.utils import timezone

from core.services.auditoria import registrar_auditoria
from core.services.authorization import Actions, usuario_puede_evento
from presupuesto.models import GastoEvento, PagoClienteEvento, PagoEvento
from presupuesto.services import resumen_financiero_interno


def _money(value):
    return Decimal(str(value or "0")).quantize(Decimal("0.01"))


def _snapshot_gasto(gasto):
    return {
        "evento_id": gasto.evento_id,
        "servicio_evento_id": gasto.servicio_evento_id,
        "categoria_id": gasto.categoria_id,
        "proveedor_id": gasto.proveedor_id,
        "concepto": gasto.concepto,
        "monto_estimado": str(_money(gasto.monto_estimado)),
        "monto_real": str(_money(gasto.monto_real)),
        "fecha_limite": gasto.fecha_limite.isoformat() if gasto.fecha_limite else None,
        "estado": gasto.estado,
        "cancelado_en": gasto.cancelado_en.isoformat() if gasto.cancelado_en else None,
        "archivado_en": gasto.archivado_en.isoformat() if gasto.archivado_en else None,
    }


def _snapshot_pago(pago):
    return {
        "gasto_id": pago.gasto_id,
        "monto": str(_money(pago.monto)),
        "fecha_pago": pago.fecha_pago.isoformat() if pago.fecha_pago else None,
        "metodo_pago": pago.metodo_pago,
        "referencia": pago.referencia,
        "estado": pago.estado,
        "comprobante": pago.comprobante.name if pago.comprobante else None,
        "anulado_en": pago.anulado_en.isoformat() if pago.anulado_en else None,
    }


def _snapshot_pago_cliente(pago):
    return {
        "evento_id": pago.evento_id,
        "monto": str(_money(pago.monto)),
        "estado": pago.estado,
        "revisado_por_id": pago.revisado_por_id,
        "fecha_revision": pago.fecha_revision.isoformat() if pago.fecha_revision else None,
        "comentario_equipo": pago.comentario_equipo,
    }


def exigir_operacion_financiera(user, evento):
    # Primero aplica el permiso financiero fino (incluye flag del planner).
    resumen_financiero_interno(evento, user=user)
    # Después exige capacidad operacional. VENTAS conserva lectura, no escritura.
    if not usuario_puede_evento(user, evento, Actions.EVENT_OPERATIONS):
        raise PermissionDenied("No tienes permiso para modificar las finanzas de este evento.")


def _sincronizar_estado_gasto(gasto):
    if gasto.estado == "CANCELADO":
        return gasto

    total = (
        gasto.pagos.filter(estado="ACTIVO")
        .aggregate(total=Sum("monto"))["total"]
        or Decimal("0")
    )
    objetivo = _money(gasto.monto_objetivo)

    if total <= 0:
        estado = "PENDIENTE"
    elif objetivo > 0 and total >= objetivo:
        estado = "PAGADO"
    else:
        estado = "PARCIAL"

    if gasto.estado != estado:
        gasto.estado = estado
        gasto.save(update_fields=["estado", "fecha_actualizacion"])
    return gasto


@transaction.atomic
def crear_gasto_financiero(*, evento, cleaned_data, user=None, request=None):
    exigir_operacion_financiera(user, evento)

    gasto = GastoEvento(evento=evento)
    for field, value in cleaned_data.items():
        setattr(gasto, field, value)

    if gasto.servicio_evento_id and not gasto.proveedor_id and gasto.servicio_evento.proveedor_id:
        gasto.proveedor = gasto.servicio_evento.proveedor

    gasto.full_clean()
    gasto.save()

    registrar_auditoria(
        usuario=user,
        empresa=evento.empresa,
        evento=evento,
        accion="CREAR_GASTO_EVENTO_K9",
        modelo="GastoEvento",
        objeto_id=gasto.id,
        descripcion=f"Se creó gasto: {gasto.concepto}.",
        valores_nuevos=_snapshot_gasto(gasto),
        request=request,
    )
    return gasto


@transaction.atomic
def actualizar_gasto_financiero(gasto, *, cleaned_data, user=None, request=None):
    gasto = (
        GastoEvento.objects.select_for_update()
        .select_related("evento", "evento__empresa", "servicio_evento", "proveedor")
        .get(pk=gasto.pk)
    )
    exigir_operacion_financiera(user, gasto.evento)

    if gasto.estado == "CANCELADO":
        raise ValidationError("No se puede editar un gasto cancelado.")

    before = _snapshot_gasto(gasto)
    for field, value in cleaned_data.items():
        setattr(gasto, field, value)

    if gasto.servicio_evento_id and not gasto.proveedor_id and gasto.servicio_evento.proveedor_id:
        gasto.proveedor = gasto.servicio_evento.proveedor

    gasto.full_clean()
    gasto.save()
    _sincronizar_estado_gasto(gasto)

    registrar_auditoria(
        usuario=user,
        empresa=gasto.evento.empresa,
        evento=gasto.evento,
        accion="ACTUALIZAR_GASTO_EVENTO_K9",
        modelo="GastoEvento",
        objeto_id=gasto.id,
        descripcion=f"Se actualizó gasto: {gasto.concepto}.",
        valores_anteriores=before,
        valores_nuevos=_snapshot_gasto(gasto),
        request=request,
    )
    return gasto


@transaction.atomic
def registrar_pago_operativo(gasto, *, cleaned_data, user=None, request=None):
    gasto = (
        GastoEvento.objects.select_for_update()
        .select_related("evento", "evento__empresa")
        .get(pk=gasto.pk)
    )
    exigir_operacion_financiera(user, gasto.evento)

    if gasto.estado == "CANCELADO":
        raise ValidationError("No puedes registrar pagos sobre un gasto cancelado.")
    if gasto.archivado_en:
        raise ValidationError("Restaura el gasto antes de registrar un pago.")

    monto = _money(cleaned_data.get("monto"))
    if monto <= 0:
        raise ValidationError("El monto debe ser mayor a cero.")
    if monto > _money(gasto.saldo_pendiente):
        raise ValidationError("El pago excede el saldo pendiente del gasto.")

    pago = PagoEvento(gasto=gasto)
    for field, value in cleaned_data.items():
        setattr(pago, field, value)
    pago.full_clean()
    pago.save()
    _sincronizar_estado_gasto(gasto)

    registrar_auditoria(
        usuario=user,
        empresa=gasto.evento.empresa,
        evento=gasto.evento,
        accion="REGISTRAR_PAGO_OPERATIVO_K9",
        modelo="PagoEvento",
        objeto_id=pago.id,
        descripcion=f"Se registró pago operativo de {pago.monto} para {gasto.concepto}.",
        valores_nuevos=_snapshot_pago(pago),
        request=request,
    )
    return pago


@transaction.atomic
def anular_pago_operativo(pago, *, motivo, user=None, request=None):
    pago = (
        PagoEvento.objects.select_for_update()
        .select_related("gasto", "gasto__evento", "gasto__evento__empresa")
        .get(pk=pago.pk)
    )
    exigir_operacion_financiera(user, pago.gasto.evento)

    if pago.estado == "ANULADO":
        return pago

    motivo = (motivo or "").strip()
    if not motivo:
        raise ValidationError("Debes indicar el motivo de la anulación.")

    before = _snapshot_pago(pago)
    pago.estado = "ANULADO"
    pago.anulado_en = timezone.now()
    pago.anulado_por = user if getattr(user, "is_authenticated", False) else None
    pago.motivo_anulacion = motivo
    pago.save(
        update_fields=[
            "estado",
            "anulado_en",
            "anulado_por",
            "motivo_anulacion",
        ]
    )
    _sincronizar_estado_gasto(pago.gasto)

    registrar_auditoria(
        usuario=user,
        empresa=pago.gasto.evento.empresa,
        evento=pago.gasto.evento,
        accion="ANULAR_PAGO_OPERATIVO_K9",
        modelo="PagoEvento",
        objeto_id=pago.id,
        descripcion=f"Se anuló pago operativo #{pago.id}.",
        valores_anteriores=before,
        valores_nuevos=_snapshot_pago(pago),
        request=request,
    )
    return pago


@transaction.atomic
def cancelar_gasto_financiero(gasto, *, motivo, user=None, request=None):
    gasto = (
        GastoEvento.objects.select_for_update()
        .select_related("evento", "evento__empresa")
        .get(pk=gasto.pk)
    )
    exigir_operacion_financiera(user, gasto.evento)

    if gasto.estado == "CANCELADO":
        return gasto

    if gasto.pagos.filter(estado="ACTIVO").exists():
        raise ValidationError(
            "Este gasto tiene pagos activos. Anúlalos primero para no borrar movimientos reales del flujo de caja."
        )

    motivo = (motivo or "").strip()
    if not motivo:
        raise ValidationError("Debes indicar el motivo de cancelación.")

    before = _snapshot_gasto(gasto)
    gasto.estado = "CANCELADO"
    gasto.cancelado_en = timezone.now()
    gasto.cancelado_por = user if getattr(user, "is_authenticated", False) else None
    gasto.motivo_cancelacion = motivo
    gasto.save(
        update_fields=[
            "estado",
            "cancelado_en",
            "cancelado_por",
            "motivo_cancelacion",
            "fecha_actualizacion",
        ]
    )

    registrar_auditoria(
        usuario=user,
        empresa=gasto.evento.empresa,
        evento=gasto.evento,
        accion="CANCELAR_GASTO_EVENTO_K9",
        modelo="GastoEvento",
        objeto_id=gasto.id,
        descripcion=f"Se canceló gasto: {gasto.concepto}.",
        valores_anteriores=before,
        valores_nuevos=_snapshot_gasto(gasto),
        request=request,
    )
    return gasto


@transaction.atomic
def archivar_gasto_financiero(gasto, *, motivo, user=None, request=None):
    gasto = (
        GastoEvento.objects.select_for_update()
        .select_related("evento", "evento__empresa")
        .get(pk=gasto.pk)
    )
    exigir_operacion_financiera(user, gasto.evento)

    if gasto.archivado_en:
        return gasto

    motivo = (motivo or "").strip()
    if not motivo:
        raise ValidationError("Debes indicar el motivo de archivo.")

    before = _snapshot_gasto(gasto)
    gasto.archivado_en = timezone.now()
    gasto.archivado_por = user if getattr(user, "is_authenticated", False) else None
    # GastoEvento no tiene motivo_archivo; se conserva el motivo en auditoría y notas.
    nota = f"[Archivado] {motivo}"
    gasto.notas = f"{gasto.notas}\n{nota}".strip() if gasto.notas else nota
    gasto.save(update_fields=["archivado_en", "archivado_por", "notas", "fecha_actualizacion"])

    registrar_auditoria(
        usuario=user,
        empresa=gasto.evento.empresa,
        evento=gasto.evento,
        accion="ARCHIVAR_GASTO_EVENTO_K9",
        modelo="GastoEvento",
        objeto_id=gasto.id,
        descripcion=f"Se archivó gasto: {gasto.concepto}. Motivo: {motivo}",
        valores_anteriores=before,
        valores_nuevos=_snapshot_gasto(gasto),
        request=request,
    )
    return gasto


@transaction.atomic
def restaurar_gasto_financiero(gasto, *, user=None, request=None):
    gasto = (
        GastoEvento.objects.select_for_update()
        .select_related("evento", "evento__empresa")
        .get(pk=gasto.pk)
    )
    exigir_operacion_financiera(user, gasto.evento)

    if not gasto.archivado_en:
        return gasto

    before = _snapshot_gasto(gasto)
    gasto.archivado_en = None
    gasto.archivado_por = None
    gasto.save(update_fields=["archivado_en", "archivado_por", "fecha_actualizacion"])

    registrar_auditoria(
        usuario=user,
        empresa=gasto.evento.empresa,
        evento=gasto.evento,
        accion="RESTAURAR_GASTO_EVENTO_K9",
        modelo="GastoEvento",
        objeto_id=gasto.id,
        descripcion=f"Se restauró gasto: {gasto.concepto}.",
        valores_anteriores=before,
        valores_nuevos=_snapshot_gasto(gasto),
        request=request,
    )
    return gasto


@transaction.atomic
def revisar_pago_cliente_financiero(pago, *, estado, comentario="", user=None, request=None):
    pago = (
        PagoClienteEvento.objects.select_for_update()
        .select_related("evento", "evento__empresa")
        .get(pk=pago.pk)
    )
    exigir_operacion_financiera(user, pago.evento)

    if estado not in {"RECIBIDO", "OBSERVADO"}:
        raise ValidationError("Estado de revisión inválido.")

    comentario = (comentario or "").strip()
    if estado == "OBSERVADO" and not comentario:
        raise ValidationError("Debes indicar la observación.")

    before = _snapshot_pago_cliente(pago)
    pago.estado = estado
    pago.comentario_equipo = comentario or None
    pago.revisado_por = user if getattr(user, "is_authenticated", False) else None
    pago.fecha_revision = timezone.now()
    pago.save(
        update_fields=[
            "estado",
            "comentario_equipo",
            "revisado_por",
            "fecha_revision",
            "fecha_actualizacion",
        ]
    )

    registrar_auditoria(
        usuario=user,
        empresa=pago.evento.empresa,
        evento=pago.evento,
        accion="REVISAR_PAGO_CLIENTE_K9",
        modelo="PagoClienteEvento",
        objeto_id=pago.id,
        descripcion=f"Pago de cliente #{pago.id} revisado como {estado}.",
        valores_anteriores=before,
        valores_nuevos=_snapshot_pago_cliente(pago),
        request=request,
    )
    return pago
