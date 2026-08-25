"""Shared helpers used by legacy dashboard boundaries during K9 consolidation."""

from decimal import Decimal, InvalidOperation
from .models import (
    AssetInvitacion,
    ComponenteInvitacion,
    DetalleProduccionEvento,
    DisenoInvitacion,
    EnlaceRegalo,
    EventoBoda,
    FotoEvento,
    Grupoinvitacion,
    Invitado,
    ItinerarioEvento,
    MenuBoda,
    PersonaCeremonia,
    PlantillaInvitacion,
    SeccionInvitacion,
    VersionDisenoInvitacion,
    es_video_archivo,
    google_maps_src,
)
from .guest_analytics import (
    resumen_invitados_evento,
    resumen_invitados_eventos,
)
from presupuesto.models import CategoriaGasto, GastoEvento, PagoEvento
from proveedores.models import PersonalEvento, Proveedor, ServicioEvento
from tareas.models import TareaEvento

def resumen_operativo_eventos(eventos):
    eventos_ids = list(eventos.values_list('id', flat=True))
    grupos = Grupoinvitacion.objects.filter(evento_id__in=eventos_ids)
    invitados_metricas = resumen_invitados_eventos(eventos)
    servicios = ServicioEvento.objects.filter(evento_id__in=eventos_ids)
    tareas = TareaEvento.objects.filter(evento_id__in=eventos_ids)
    gastos = GastoEvento.objects.filter(evento_id__in=eventos_ids)
    return {
        'invitaciones': grupos.count(),
        'confirmados': invitados_metricas['confirmados'],
        'pendientes_rsvp': invitados_metricas['pendientes'],
        'servicios_pendientes': servicios.exclude(
            estado__in=['CONTRATADO', 'ANTICIPO_PAGADO', 'LIQUIDADO', 'SERVICIO_COMPLETADO']
        ).count(),
        'tareas_pendientes': tareas.exclude(estado__in=['COMPLETADA', 'CANCELADA']).count(),
        'tareas_vencidas': sum(1 for tarea in tareas if tarea.esta_vencida),
        'pagos_vencidos': sum(1 for gasto in gastos if gasto.esta_vencido),
    }

def convertir_entero(valor, default=0):
    try:
        return max(int(valor), 0)
    except (TypeError, ValueError):
        return default

def bool_post(request, campo):
    return request.POST.get(campo) == 'on'

def limpiar_texto(request, campo):
    valor = request.POST.get(campo)
    return valor.strip() if valor else None

def convertir_decimal(valor, default=0):
    try:
        return Decimal(valor or default)
    except (InvalidOperation, TypeError, ValueError):
        return Decimal(default)
