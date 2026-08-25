from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from core.services.authorization import Actions, usuario_puede_evento
from presupuesto.models import GastoEvento, PagoClienteEvento, PagoEvento
from presupuesto.services import resumen_financiero_interno

from .workspace_finance import (
    actualizar_gasto_financiero,
    anular_pago_operativo,
    archivar_gasto_financiero,
    cancelar_gasto_financiero,
    crear_gasto_financiero,
    exigir_operacion_financiera,
    registrar_pago_operativo,
    restaurar_gasto_financiero,
    revisar_pago_cliente_financiero,
)
from .workspace_finance_forms import (
    GastoEventoWorkspaceForm,
    MotivoGastoForm,
    MotivoPagoForm,
    PagoOperativoWorkspaceForm,
    RevisarPagoClienteWorkspaceForm,
)
from .workspace_views import (
    _app_context,
    _contexto_empresa,
    _evento_visible,
    _return_context,
    _workspace_context,
)


def _finance_redirect(empresa, evento, request):
    url = reverse(
        "k9_evento_finanzas",
        kwargs={"empresa_slug": empresa.slug, "evento_id": evento.id},
    )
    return_to = (request.POST.get("return_to") or "").strip()
    if return_to:
        from urllib.parse import urlencode
        url = f"{url}?{urlencode({'return_to': return_to})}"
    return redirect(url)


def _validation_message(exc):
    if hasattr(exc, "message_dict"):
        parts = []
        for values in exc.message_dict.values():
            parts.extend(values)
        return " · ".join(str(item) for item in parts)
    if hasattr(exc, "messages"):
        return " · ".join(str(item) for item in exc.messages)
    return str(exc)


def _base_event(request, empresa_slug, evento_id):
    tenant, _roles = _contexto_empresa(request, empresa_slug)
    empresa = tenant.empresa
    evento = _evento_visible(request.user, empresa, evento_id)
    # Valida permiso financiero interno, incluido flag fino de planner.
    resumen_financiero_interno(evento, user=request.user)
    return empresa, evento


@login_required(login_url="/login/")
def evento_finanzas(request, empresa_slug, evento_id):
    tenant, _roles = _contexto_empresa(request, empresa_slug)
    empresa = tenant.empresa
    evento = _evento_visible(request.user, empresa, evento_id)
    return_to = _return_context(request, empresa)

    try:
        resumen = resumen_financiero_interno(evento, user=request.user)
    except PermissionDenied:
        raise PermissionDenied(
            "No tienes permiso para consultar las finanzas internas de este evento."
        )

    puede_operar = usuario_puede_evento(
        request.user,
        evento,
        Actions.EVENT_OPERATIONS,
    )

    gastos_qs = (
        GastoEvento.objects.filter(evento=evento)
        .select_related("categoria", "proveedor", "servicio_evento")
        .prefetch_related("pagos")
        .order_by("archivado_en", "fecha_limite", "concepto", "id")
    )
    gastos_todos = list(gastos_qs)
    gastos_archivados = [gasto for gasto in gastos_todos if gasto.archivado_en]
    gastos = [gasto for gasto in gastos_todos if not gasto.archivado_en]

    pagos_cliente = list(
        PagoClienteEvento.objects.filter(evento=evento)
        .select_related("registrado_por", "revisado_por", "servicio_evento")
        .order_by("-fecha_pago", "-id")
    )
    servicios = list(resumen.get("servicios") or [])

    estado_gasto = (request.GET.get("estado_gasto") or "").strip().upper()
    if estado_gasto:
        valid_states = {"PENDIENTE", "PARCIAL", "PAGADO", "VENCIDO", "CANCELADO"}
        if estado_gasto in valid_states:
            gastos = [
                gasto
                for gasto in gastos
                if ("VENCIDO" if gasto.esta_vencido else gasto.estado) == estado_gasto
            ]
        else:
            estado_gasto = ""

    estado_cliente = (request.GET.get("estado_cliente") or "").strip().upper()
    if estado_cliente:
        valid_client_states = {"PENDIENTE", "RECIBIDO", "OBSERVADO", "CANCELADO"}
        if estado_cliente in valid_client_states:
            pagos_cliente = [
                pago for pago in pagos_cliente if pago.estado == estado_cliente
            ]
        else:
            estado_cliente = ""

    costos_pendientes = [item for item in servicios if item.get("costo_pendiente")]
    gastos_vencidos = [
        gasto
        for gasto in GastoEvento.objects.filter(evento=evento, archivado_en__isnull=True)
        .exclude(estado="CANCELADO")
        if gasto.esta_vencido
    ]
    pagos_cliente_pendientes = [
        pago
        for pago in PagoClienteEvento.objects.filter(evento=evento)
        if pago.estado == "PENDIENTE"
    ]

    context = _app_context(
        request,
        empresa,
        title=evento.titulo_evento,
        section="Event Workspace",
    )
    context.update(
        {
            "evento": evento,
            "workspace_active": "finanzas",
            "workspace_navigation": _workspace_context(
                request,
                empresa=empresa,
                evento=evento,
                active_key="finanzas",
            ),
            "return_to": return_to,
            "puede_editar": puede_operar,
            "puede_operar_finanzas": puede_operar,
            "resumen": resumen,
            "gastos": gastos,
            "gastos_archivados": gastos_archivados,
            "pagos_cliente": pagos_cliente,
            "servicios_financieros": servicios,
            "estado_gasto": estado_gasto,
            "estado_cliente": estado_cliente,
            "costos_pendientes": costos_pendientes,
            "gastos_vencidos": gastos_vencidos,
            "pagos_cliente_pendientes": pagos_cliente_pendientes,
            "gasto_form": GastoEventoWorkspaceForm(evento=evento),
            "pago_form": PagoOperativoWorkspaceForm(),
            "motivo_gasto_form": MotivoGastoForm(),
            "motivo_pago_form": MotivoPagoForm(),
            "revision_pago_cliente_form": RevisarPagoClienteWorkspaceForm(),
        }
    )
    return render(request, "eventos/workspace/finanzas.html", context)


@login_required(login_url="/login/")
@require_POST
def gasto_crear(request, empresa_slug, evento_id):
    empresa, evento = _base_event(request, empresa_slug, evento_id)
    exigir_operacion_financiera(request.user, evento)

    form = GastoEventoWorkspaceForm(request.POST, evento=evento)
    if not form.is_valid():
        messages.error(request, " · ".join(form.non_field_errors() or []) or "Revisa los datos del gasto.")
        for field in form:
            for error in field.errors:
                messages.error(request, f"{field.label}: {error}")
        return _finance_redirect(empresa, evento, request)

    try:
        gasto = crear_gasto_financiero(
            evento=evento,
            cleaned_data=form.cleaned_data,
            user=request.user,
            request=request,
        )
        messages.success(request, f"Gasto creado: {gasto.concepto}.")
    except ValidationError as exc:
        messages.error(request, _validation_message(exc))
    return _finance_redirect(empresa, evento, request)


@login_required(login_url="/login/")
@require_POST
def gasto_editar(request, empresa_slug, evento_id, gasto_id):
    empresa, evento = _base_event(request, empresa_slug, evento_id)
    exigir_operacion_financiera(request.user, evento)
    gasto = get_object_or_404(GastoEvento, pk=gasto_id, evento=evento)

    form = GastoEventoWorkspaceForm(
        request.POST,
        instance=gasto,
        evento=evento,
    )
    if not form.is_valid():
        for field in form:
            for error in field.errors:
                messages.error(request, f"{field.label}: {error}")
        for error in form.non_field_errors():
            messages.error(request, error)
        return _finance_redirect(empresa, evento, request)

    try:
        actualizar_gasto_financiero(
            gasto,
            cleaned_data=form.cleaned_data,
            user=request.user,
            request=request,
        )
        messages.success(request, "Gasto actualizado.")
    except ValidationError as exc:
        messages.error(request, _validation_message(exc))
    return _finance_redirect(empresa, evento, request)


@login_required(login_url="/login/")
@require_POST
def pago_registrar(request, empresa_slug, evento_id, gasto_id):
    empresa, evento = _base_event(request, empresa_slug, evento_id)
    exigir_operacion_financiera(request.user, evento)
    gasto = get_object_or_404(GastoEvento, pk=gasto_id, evento=evento)

    form = PagoOperativoWorkspaceForm(
        request.POST,
        request.FILES,
        gasto=gasto,
    )
    if not form.is_valid():
        for field in form:
            for error in field.errors:
                messages.error(request, f"{field.label}: {error}")
        for error in form.non_field_errors():
            messages.error(request, error)
        return _finance_redirect(empresa, evento, request)

    try:
        registrar_pago_operativo(
            gasto,
            cleaned_data=form.cleaned_data,
            user=request.user,
            request=request,
        )
        messages.success(request, "Pago operativo registrado.")
    except ValidationError as exc:
        messages.error(request, _validation_message(exc))
    return _finance_redirect(empresa, evento, request)


@login_required(login_url="/login/")
@require_POST
def pago_anular(request, empresa_slug, evento_id, pago_id):
    empresa, evento = _base_event(request, empresa_slug, evento_id)
    exigir_operacion_financiera(request.user, evento)
    pago = get_object_or_404(PagoEvento, pk=pago_id, gasto__evento=evento)

    form = MotivoPagoForm(request.POST)
    if not form.is_valid():
        messages.error(request, "Indica el motivo de la anulación.")
        return _finance_redirect(empresa, evento, request)

    try:
        anular_pago_operativo(
            pago,
            motivo=form.cleaned_data["motivo"],
            user=request.user,
            request=request,
        )
        messages.success(request, "Pago operativo anulado. El saldo del gasto fue recalculado.")
    except ValidationError as exc:
        messages.error(request, _validation_message(exc))
    return _finance_redirect(empresa, evento, request)


@login_required(login_url="/login/")
@require_POST
def gasto_cancelar(request, empresa_slug, evento_id, gasto_id):
    empresa, evento = _base_event(request, empresa_slug, evento_id)
    exigir_operacion_financiera(request.user, evento)
    gasto = get_object_or_404(GastoEvento, pk=gasto_id, evento=evento)

    form = MotivoGastoForm(request.POST)
    if not form.is_valid():
        messages.error(request, "Indica el motivo de cancelación.")
        return _finance_redirect(empresa, evento, request)

    try:
        cancelar_gasto_financiero(
            gasto,
            motivo=form.cleaned_data["motivo"],
            user=request.user,
            request=request,
        )
        messages.success(request, "Gasto cancelado.")
    except ValidationError as exc:
        messages.error(request, _validation_message(exc))
    return _finance_redirect(empresa, evento, request)


@login_required(login_url="/login/")
@require_POST
def gasto_archivar(request, empresa_slug, evento_id, gasto_id):
    empresa, evento = _base_event(request, empresa_slug, evento_id)
    exigir_operacion_financiera(request.user, evento)
    gasto = get_object_or_404(GastoEvento, pk=gasto_id, evento=evento)

    form = MotivoGastoForm(request.POST)
    if not form.is_valid():
        messages.error(request, "Indica el motivo de archivo.")
        return _finance_redirect(empresa, evento, request)

    try:
        archivar_gasto_financiero(
            gasto,
            motivo=form.cleaned_data["motivo"],
            user=request.user,
            request=request,
        )
        messages.success(request, "Gasto archivado. Su historial financiero se conserva.")
    except ValidationError as exc:
        messages.error(request, _validation_message(exc))
    return _finance_redirect(empresa, evento, request)


@login_required(login_url="/login/")
@require_POST
def gasto_restaurar(request, empresa_slug, evento_id, gasto_id):
    empresa, evento = _base_event(request, empresa_slug, evento_id)
    exigir_operacion_financiera(request.user, evento)
    gasto = get_object_or_404(GastoEvento, pk=gasto_id, evento=evento)

    try:
        restaurar_gasto_financiero(
            gasto,
            user=request.user,
            request=request,
        )
        messages.success(request, "Gasto restaurado.")
    except ValidationError as exc:
        messages.error(request, _validation_message(exc))
    return _finance_redirect(empresa, evento, request)


@login_required(login_url="/login/")
@require_POST
def pago_cliente_revisar(request, empresa_slug, evento_id, pago_id):
    empresa, evento = _base_event(request, empresa_slug, evento_id)
    exigir_operacion_financiera(request.user, evento)
    pago = get_object_or_404(PagoClienteEvento, pk=pago_id, evento=evento)

    form = RevisarPagoClienteWorkspaceForm(request.POST)
    if not form.is_valid():
        for field in form:
            for error in field.errors:
                messages.error(request, f"{field.label}: {error}")
        return _finance_redirect(empresa, evento, request)

    try:
        revisar_pago_cliente_financiero(
            pago,
            estado=form.cleaned_data["estado"],
            comentario=form.cleaned_data["comentario_equipo"],
            user=request.user,
            request=request,
        )
        messages.success(request, "Pago del cliente revisado.")
    except ValidationError as exc:
        messages.error(request, _validation_message(exc))
    return _finance_redirect(empresa, evento, request)
