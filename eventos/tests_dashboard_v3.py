from datetime import time, timedelta
from decimal import Decimal

from django.test import TestCase
from django.utils import timezone

from invitaciones.models import EventoBoda
from proveedores.models import ServicioEvento
from tareas.models import TareaEvento
from itinerario.models import ActividadItinerario
from presupuesto.models import CategoriaGasto, GastoEvento, PagoEvento
from documentos.models import DocumentoEvento
from eventos.models import ContratoEvento
from eventos.dashboard_v3 import construir_contexto_dashboard_evento_v3


class EventDashboardV3ContextTests(TestCase):
    def setUp(self):
        now = timezone.now()
        self.evento = EventoBoda.objects.create(
            novio='Diego', novia='Fernanda', frase_portada='F&D', mensaje_general='Evento',
            fecha_misa=now + timedelta(days=10), lugar_misa='Ceremonia',
            fecha_fiesta=now + timedelta(days=10), lugar_fiesta='Recepcion',
        )
        self.servicio = ServicioEvento.objects.create(
            evento=self.evento, nombre_servicio='Banquete', modalidad='INCLUIDO',
            valor_contratado=Decimal('80000'), cargo_adicional_cliente=Decimal('0'),
        )
        self.tarea = TareaEvento.objects.create(
            evento=self.evento, servicio_evento=self.servicio, titulo='Confirmar menu',
            fecha_limite=timezone.localdate() - timedelta(days=1),
        )
        self.actividad = ActividadItinerario.objects.create(
            evento=self.evento, servicio_evento=self.servicio, titulo='Prueba menu',
            fecha=timezone.localdate() + timedelta(days=2), hora_inicio=time(16, 30),
        )
        categoria = CategoriaGasto.objects.create(nombre='Banquete K871')
        self.gasto = GastoEvento.objects.create(
            evento=self.evento, servicio_evento=self.servicio, categoria=categoria,
            concepto='Anticipo', monto_real=Decimal('10000'),
        )
        PagoEvento.objects.create(gasto=self.gasto, monto=Decimal('4000'))
        ContratoEvento.objects.create(evento=self.evento, version=1, estado='FIRMADO', monto_base=Decimal('300000'))

    def test_contexto_separa_finanzas_y_operacion(self):
        ctx = construir_contexto_dashboard_evento_v3(
            self.evento,
            servicios_evento=ServicioEvento.objects.filter(evento=self.evento),
            tareas_evento=TareaEvento.objects.filter(evento=self.evento),
            actividades_evento=ActividadItinerario.objects.filter(evento=self.evento),
            gastos_evento=GastoEvento.objects.filter(evento=self.evento).prefetch_related('pagos'),
            documentos_evento=DocumentoEvento.objects.filter(evento=self.evento),
        )
        self.assertEqual(ctx['contrato_base_v3'], Decimal('300000'))
        self.assertEqual(ctx['extras_cliente_v3'], Decimal('0'))
        self.assertEqual(ctx['gastos_operativos_total_v3'], Decimal('10000'))
        self.assertEqual(ctx['pagos_operativos_total_v3'], Decimal('4000'))
        self.assertEqual(ctx['saldo_operativo_v3'], Decimal('6000'))
        self.assertEqual(len(ctx['tareas_vencidas_v3']), 1)
        self.assertEqual(ctx['servicios_activos_v3'], 1)
