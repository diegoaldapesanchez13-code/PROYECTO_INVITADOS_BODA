from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone
from django.utils.dateparse import parse_date
from django.views.decorators.http import require_POST

from core.services.authorization import Actions, usuario_puede_evento
from core.services.runtime_guardrails import block_replaced_legacy_post
from eventos.models import ParticipanteEvento
from proveedores.models import ServicioEvento

from .models import PagoClienteEvento


def _decimal(value):
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return Decimal("0")


def _es_cliente(user, evento):
    return evento.clientes.filter(id=user.id).exists() or ParticipanteEvento.objects.filter(
        evento=evento, usuario=user, rol="CLIENTE", activo=True
    ).exists()


@login_required
@require_POST
@transaction.atomic
def registrar_pago_cliente(request, evento_id):
    from invitaciones.models import EventoBoda

    evento = get_object_or_404(EventoBoda, pk=evento_id)
    if not _es_cliente(request.user, evento):
        raise PermissionDenied("Solo un cliente del evento puede registrar este pago.")

    monto = _decimal(request.POST.get("monto"))
    comprobante = request.FILES.get("comprobante")
    if monto <= 0:
        messages.error(request, "El monto debe ser mayor a cero.")
        return redirect(f"{reverse('portal_cliente')}?evento={evento.id}#pagos")
    if not comprobante:
        messages.error(request, "Adjunta una foto o PDF del comprobante.")
        return redirect(f"{reverse('portal_cliente')}?evento={evento.id}#pagos")

    servicio = None
    servicio_id = request.POST.get("servicio_evento_id")
    if servicio_id:
        servicio = get_object_or_404(ServicioEvento, pk=servicio_id, evento=evento)

    metodo = request.POST.get("metodo_pago") or "TRANSFERENCIA"
    if metodo not in dict(PagoClienteEvento.METODOS):
        metodo = "TRANSFERENCIA"

    pago = PagoClienteEvento(
        evento=evento,
        servicio_evento=servicio,
        registrado_por=request.user,
        concepto=(request.POST.get("concepto") or "").strip() or None,
        monto=monto,
        fecha_pago=parse_date(request.POST.get("fecha_pago") or "") or timezone.localdate(),
        metodo_pago=metodo,
        referencia=(request.POST.get("referencia") or "").strip() or None,
        comprobante=comprobante,
        comentario_cliente=(request.POST.get("comentario_cliente") or "").strip() or None,
    )
    try:
        pago.full_clean()
        pago.save()
        messages.success(request, "Pago reportado. La empresa o tu planner debe revisarlo.")
    except ValidationError as exc:
        messages.error(request, " ".join(exc.messages))
    return redirect(f"{reverse('portal_cliente')}?evento={evento.id}#pagos")


@login_required
@require_POST
@transaction.atomic
def revisar_pago_cliente(request, pago_id):
    pago = get_object_or_404(PagoClienteEvento.objects.select_related("evento"), pk=pago_id)
    if not usuario_puede_evento(request.user, pago.evento, Actions.EVENT_OPERATIONS):
        raise PermissionDenied("Solo la empresa o planner responsable puede revisar este pago.")

    empresa = pago.evento.empresa
    redirect_to = (
        reverse(
            "k9_evento_finanzas",
            kwargs={"empresa_slug": empresa.slug, "evento_id": pago.evento_id},
        )
        if empresa
        else f"{reverse('dashboard')}?evento={pago.evento_id}#finanzas"
    )
    return block_replaced_legacy_post(
        request,
        endpoint="pago_cliente_evento_revisar",
        replacement="k9_finanzas_pago_cliente_revisar",
        redirect_to=redirect_to,
        empresa=empresa,
        evento=pago.evento,
    )
