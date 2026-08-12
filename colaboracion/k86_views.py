from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone
from django.utils.dateparse import parse_date, parse_time
from django.views.decorators.http import require_POST

from documentos.models import DocumentoEvento
from itinerario.models import ActividadItinerario, ParticipanteActividad
from itinerario.services import asegurar_participantes_cita, registrar_confirmacion_propia
from presupuesto.models import CategoriaGasto, GastoEvento, PagoEvento
from proveedores.models import ServicioEvento
from tareas.models import TareaEvento

from .services import es_operador_servicio_workspace


def _servicio(pk):
    return get_object_or_404(
        ServicioEvento.objects.select_related('evento', 'evento__empresa', 'proveedor'),
        pk=pk,
    )


def _url(servicio):
    return f"{reverse('colaboracion_workspace_servicio', args=[servicio.id])}?canal=CLIENTE_PLANNER#operacion-servicio"


def _require_operador(user, servicio):
    if not es_operador_servicio_workspace(user, servicio):
        raise PermissionDenied('Solo el equipo operativo puede administrar la operación vinculada.')


def _decimal(value, default=Decimal('0')):
    try:
        return Decimal(str(value or default))
    except (InvalidOperation, TypeError, ValueError):
        return default


def _validation_message(exc):
    if hasattr(exc, 'message_dict'):
        return ' · '.join(f"{campo}: {', '.join(map(str, errores))}" for campo, errores in exc.message_dict.items())
    return ' · '.join(map(str, getattr(exc, 'messages', [str(exc)])))


@login_required
@require_POST
@transaction.atomic
def crear_tarea(request, servicio_id):
    servicio = _servicio(servicio_id)
    _require_operador(request.user, servicio)
    titulo = (request.POST.get('titulo') or '').strip()
    if not titulo:
        messages.error(request, 'La tarea necesita un título.')
        return redirect(_url(servicio))
    tarea = TareaEvento(
        evento=servicio.evento,
        servicio_evento=servicio,
        titulo=titulo,
        descripcion=(request.POST.get('descripcion') or '').strip() or None,
        responsable=request.user,
        fecha_inicio=parse_date(request.POST.get('fecha_inicio') or '') or None,
        fecha_limite=parse_date(request.POST.get('fecha_limite') or '') or None,
        prioridad=request.POST.get('prioridad') if request.POST.get('prioridad') in dict(TareaEvento.PRIORIDADES) else 'MEDIA',
        categoria=request.POST.get('categoria') if request.POST.get('categoria') in dict(TareaEvento.CATEGORIAS) else 'PROVEEDORES',
        notas=(request.POST.get('notas') or '').strip() or None,
    )
    try:
        tarea.full_clean()
        tarea.save()
        messages.success(request, 'Tarea vinculada al servicio.')
    except ValidationError as exc:
        messages.error(request, _validation_message(exc))
    return redirect(_url(servicio))


@login_required
@require_POST
@transaction.atomic
def crear_actividad(request, servicio_id):
    servicio = _servicio(servicio_id)
    _require_operador(request.user, servicio)
    titulo = (request.POST.get('titulo') or '').strip()
    fecha = parse_date(request.POST.get('fecha') or '')
    hora_inicio = parse_time(request.POST.get('hora_inicio') or '')
    if not titulo or not fecha or not hora_inicio:
        messages.error(request, 'La cita necesita título, fecha y hora de inicio.')
        return redirect(_url(servicio))
    tipo = request.POST.get('tipo') if request.POST.get('tipo') in dict(ActividadItinerario.TIPOS) else 'CITA'
    actividad = ActividadItinerario(
        evento=servicio.evento,
        tipo=tipo,
        servicio_evento=servicio,
        titulo=titulo,
        descripcion=(request.POST.get('descripcion') or '').strip() or None,
        categoria=request.POST.get('categoria') if request.POST.get('categoria') in dict(ActividadItinerario.CATEGORIAS) else 'PROVEEDORES',
        fecha=fecha,
        hora_inicio=hora_inicio,
        hora_fin=parse_time(request.POST.get('hora_fin') or '') or None,
        ubicacion=(request.POST.get('ubicacion') or '').strip() or None,
        responsable=request.user,
        proveedor=servicio.proveedor,
        prioridad=request.POST.get('prioridad') if request.POST.get('prioridad') in dict(ActividadItinerario.PRIORIDADES) else 'MEDIA',
        estado='PENDIENTE',
        notas=(request.POST.get('notas') or '').strip() or None,
    )
    try:
        actividad.full_clean()
        actividad.save()
        if actividad.tipo == 'CITA':
            asegurar_participantes_cita(actividad, creador=request.user)
        messages.success(request, f'{actividad.get_tipo_display()} vinculada al servicio.')
    except ValidationError as exc:
        messages.error(request, _validation_message(exc))
    return redirect(_url(servicio))


@login_required
@require_POST
@transaction.atomic
def crear_documento(request, servicio_id):
    servicio = _servicio(servicio_id)
    _require_operador(request.user, servicio)
    archivo = request.FILES.get('archivo')
    titulo = (request.POST.get('titulo') or '').strip()
    if not titulo or not archivo:
        messages.error(request, 'El documento necesita título y archivo.')
        return redirect(_url(servicio))
    tipo = request.POST.get('tipo_documento')
    documento = DocumentoEvento(
        evento=servicio.evento,
        servicio_evento=servicio,
        tipo_documento=tipo if tipo in dict(DocumentoEvento.TIPOS) else 'OTRO',
        titulo=titulo,
        archivo=archivo,
        proveedor=servicio.proveedor,
        descripcion=(request.POST.get('descripcion') or '').strip() or None,
        cargado_por=request.user,
        visible_cliente=request.POST.get('visible_cliente') == 'on',
        visible_proveedor=request.POST.get('visible_proveedor') == 'on',
    )
    try:
        documento.full_clean()
        documento.save()
        messages.success(request, 'Documento guardado y vinculado al servicio.')
    except ValidationError as exc:
        messages.error(request, _validation_message(exc))
    return redirect(_url(servicio))


@login_required
@require_POST
@transaction.atomic
def crear_gasto(request, servicio_id):
    servicio = _servicio(servicio_id)
    _require_operador(request.user, servicio)
    categoria = CategoriaGasto.objects.filter(pk=request.POST.get('categoria_id'), activo=True).first()
    concepto = (request.POST.get('concepto') or '').strip()
    if not categoria or not concepto:
        messages.error(request, 'El gasto necesita categoría y concepto.')
        return redirect(_url(servicio))
    gasto = GastoEvento(
        evento=servicio.evento,
        servicio_evento=servicio,
        categoria=categoria,
        proveedor=servicio.proveedor,
        concepto=concepto,
        monto_estimado=_decimal(request.POST.get('monto_estimado')),
        monto_real=_decimal(request.POST.get('monto_real')),
        fecha_limite=parse_date(request.POST.get('fecha_limite') or '') or None,
        estado='PENDIENTE',
        notas=(request.POST.get('notas') or '').strip() or None,
    )
    try:
        gasto.full_clean()
        gasto.save()
        messages.success(request, 'Gasto vinculado al servicio.')
    except ValidationError as exc:
        messages.error(request, _validation_message(exc))
    return redirect(_url(servicio))


@login_required
@require_POST
@transaction.atomic
def crear_pago(request, servicio_id):
    servicio = _servicio(servicio_id)
    _require_operador(request.user, servicio)
    gasto = get_object_or_404(GastoEvento, pk=request.POST.get('gasto_id'), servicio_evento=servicio, evento=servicio.evento)
    monto = _decimal(request.POST.get('monto'))
    if monto <= 0:
        messages.error(request, 'El pago debe ser mayor a cero.')
        return redirect(_url(servicio))
    metodo = request.POST.get('metodo_pago')
    pago = PagoEvento(
        gasto=gasto,
        monto=monto,
        fecha_pago=parse_date(request.POST.get('fecha_pago') or '') or timezone.localdate(),
        metodo_pago=metodo if metodo in dict(PagoEvento.METODOS) else 'TRANSFERENCIA',
        referencia=(request.POST.get('referencia') or '').strip() or None,
        comprobante=request.FILES.get('comprobante'),
        notas=(request.POST.get('notas') or '').strip() or None,
    )
    try:
        pago.full_clean()
        pago.save()
        messages.success(request, 'Pago registrado dentro del gasto del servicio.')
    except ValidationError as exc:
        messages.error(request, _validation_message(exc))
    return redirect(_url(servicio))


@login_required
@require_POST
@transaction.atomic
def responder_confirmacion_cita(request, servicio_id, participante_id):
    servicio = _servicio(servicio_id)
    participante = get_object_or_404(
        ParticipanteActividad.objects.select_related('actividad', 'usuario', 'proveedor', 'proveedor__usuario'),
        pk=participante_id,
        actividad__servicio_evento=servicio,
        actividad__evento=servicio.evento,
        actividad__tipo='CITA',
    )
    estado = request.POST.get('estado') or ''
    comentario = request.POST.get('comentario') or ''
    registrar_confirmacion_propia(participante, request.user, estado, comentario)
    messages.success(request, 'Tu respuesta de la cita quedó registrada.')
    if es_operador_servicio_workspace(request.user, servicio):
        return redirect(_url(servicio))
    from .services import es_cliente_servicio_workspace, es_proveedor_servicio_workspace
    if es_cliente_servicio_workspace(request.user, servicio):
        return redirect(f"{reverse('portal_cliente')}?evento={servicio.evento_id}#agenda")
    if es_proveedor_servicio_workspace(request.user, servicio):
        return redirect(f"{reverse('portal_proveedor')}?evento={servicio.evento_id}")
    return redirect(_url(servicio))


@login_required
@require_POST
@transaction.atomic
def responder_confirmacion_cita_evento(request, participante_id):
    """Responder una CITA general del evento que no pertenece a ServicioEvento."""
    participante = get_object_or_404(
        ParticipanteActividad.objects.select_related(
            'actividad',
            'actividad__evento',
            'usuario',
            'proveedor',
            'proveedor__usuario',
        ),
        pk=participante_id,
        actividad__tipo='CITA',
        actividad__servicio_evento__isnull=True,
    )
    registrar_confirmacion_propia(
        participante,
        request.user,
        request.POST.get('estado') or '',
        request.POST.get('comentario') or '',
    )
    messages.success(request, 'Tu respuesta de la cita quedó registrada.')

    evento = participante.actividad.evento
    if evento.clientes.filter(id=request.user.id).exists():
        return redirect(f"{reverse('portal_cliente')}?evento={evento.id}#agenda")

    from eventos.models import ParticipanteEvento
    if ParticipanteEvento.objects.filter(
        evento=evento,
        usuario=request.user,
        rol='CLIENTE',
        activo=True,
    ).exists():
        return redirect(f"{reverse('portal_cliente')}?evento={evento.id}#agenda")

    return redirect(f"{reverse('dashboard')}?evento={evento.id}#agenda")


MODELOS_VINCULABLES = {
    'TAREA': TareaEvento,
    'ACTIVIDAD': ActividadItinerario,
    'DOCUMENTO': DocumentoEvento,
    'GASTO': GastoEvento,
}


@login_required
@require_POST
@transaction.atomic
def vincular_existente(request, servicio_id):
    servicio = _servicio(servicio_id)
    _require_operador(request.user, servicio)
    tipo = request.POST.get('tipo')
    modelo = MODELOS_VINCULABLES.get(tipo)
    if not modelo:
        messages.error(request, 'Tipo de registro no reconocido.')
        return redirect(_url(servicio))
    objeto = get_object_or_404(modelo, pk=request.POST.get('registro_id'), evento=servicio.evento)
    if objeto.servicio_evento_id and objeto.servicio_evento_id != servicio.id:
        messages.error(request, 'Ese registro ya está vinculado a otro servicio.')
        return redirect(_url(servicio))
    objeto.servicio_evento = servicio
    if hasattr(objeto, 'proveedor_id') and not objeto.proveedor_id and servicio.proveedor_id:
        objeto.proveedor = servicio.proveedor
    try:
        objeto.full_clean()
        objeto.save(update_fields=['servicio_evento'] + (['proveedor'] if hasattr(objeto, 'proveedor_id') and objeto.proveedor_id == servicio.proveedor_id else []))
        messages.success(request, 'Registro existente vinculado al servicio.')
    except ValidationError as exc:
        messages.error(request, _validation_message(exc))
    return redirect(_url(servicio))


@login_required
@require_POST
@transaction.atomic
def desvincular(request, servicio_id):
    servicio = _servicio(servicio_id)
    _require_operador(request.user, servicio)
    tipo = request.POST.get('tipo')
    modelo = MODELOS_VINCULABLES.get(tipo)
    if not modelo:
        messages.error(request, 'Tipo de registro no reconocido.')
        return redirect(_url(servicio))
    objeto = get_object_or_404(modelo, pk=request.POST.get('registro_id'), evento=servicio.evento, servicio_evento=servicio)
    objeto.servicio_evento = None
    objeto.save(update_fields=['servicio_evento'])
    messages.success(request, 'Registro desvinculado. El registro no fue eliminado.')
    return redirect(_url(servicio))
