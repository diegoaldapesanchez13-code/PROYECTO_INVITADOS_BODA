from datetime import time, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from colaboracion.models import AprobacionServicio, CotizacionServicio
from eventos.dashboard_v3 import construir_contexto_dashboard_evento_v3
from itinerario.models import ActividadItinerario, ParticipanteActividad
from invitaciones.models import EventoBoda
from organizaciones.models import EmpresaSuscriptora, MembresiaEmpresa
from presupuesto.models import GastoEvento
from proveedores.models import Proveedor, ServicioEvento
from tareas.models import TareaEvento
from documentos.models import DocumentoEvento


class OperationalClarityK8712Tests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.empresa = EmpresaSuscriptora.objects.create(nombre_comercial='Empresa K8712', slug='empresa-k8712')
        self.planner = User.objects.create_user(username='planner-k8712', password='test123')
        self.cliente = User.objects.create_user(username='cliente-k8712', password='test123')
        self.proveedor_user = User.objects.create_user(username='proveedor-k8712', password='test123')
        for user, rol in [
            (self.planner, 'WEDDING_PLANNER'),
            (self.cliente, 'CLIENTE'),
            (self.proveedor_user, 'PROVEEDOR'),
        ]:
            MembresiaEmpresa.objects.create(empresa=self.empresa, usuario=user, rol=rol)
        now = timezone.now()
        self.evento = EventoBoda.objects.create(
            empresa=self.empresa,
            wedding_planner=self.planner,
            nombre_evento='Boda K8712',
            novio='A', novia='B', frase_portada='Test', mensaje_general='Test',
            fecha_misa=now + timedelta(days=20), lugar_misa='Ceremonia',
            fecha_fiesta=now + timedelta(days=20), lugar_fiesta='Recepcion',
        )
        self.evento.clientes.add(self.cliente)
        self.proveedor = Proveedor.objects.create(
            empresa=self.empresa,
            usuario=self.proveedor_user,
            nombre_comercial='Proveedor K8712',
            tipo_proveedor='BANQUETE',
        )
        self.servicio = ServicioEvento.objects.create(
            evento=self.evento,
            proveedor=self.proveedor,
            nombre_servicio='Banquete K8712',
            origen='MANUAL', modalidad='ADICIONAL',
        )

    def test_cita_creada_desde_workspace_genera_participantes(self):
        self.client.force_login(self.planner)
        response = self.client.post(
            reverse('colaboracion_k86_actividad_crear', args=[self.servicio.id]),
            {
                'tipo': 'CITA',
                'titulo': 'Prueba de menú',
                'fecha': (timezone.localdate() + timedelta(days=3)).isoformat(),
                'hora_inicio': '16:30',
                'hora_fin': '18:00',
                'categoria': 'PROVEEDORES',
            },
        )
        self.assertEqual(response.status_code, 302)
        cita = ActividadItinerario.objects.get(titulo='Prueba de menú')
        self.assertEqual(cita.tipo, 'CITA')
        self.assertTrue(cita.participantes.filter(usuario=self.cliente, rol='CLIENTE').exists())
        self.assertTrue(cita.participantes.filter(usuario=self.planner, rol='PLANNER').exists())
        self.assertTrue(cita.participantes.filter(proveedor=self.proveedor, rol='PROVEEDOR').exists())
        self.assertEqual(cita.participantes.get(usuario=self.planner).estado, 'CONFIRMADO')

    def test_cliente_y_proveedor_confirman_su_propia_participacion(self):
        self.client.force_login(self.planner)
        self.client.post(
            reverse('colaboracion_k86_actividad_crear', args=[self.servicio.id]),
            {
                'tipo': 'CITA', 'titulo': 'Montaje',
                'fecha': (timezone.localdate() + timedelta(days=2)).isoformat(),
                'hora_inicio': '10:00', 'categoria': 'MONTAJE',
            },
        )
        cita = ActividadItinerario.objects.get(titulo='Montaje')
        cliente_part = cita.participantes.get(usuario=self.cliente)
        proveedor_part = cita.participantes.get(proveedor=self.proveedor)

        self.client.force_login(self.cliente)
        response = self.client.post(
            reverse('colaboracion_k8712_cita_responder', args=[self.servicio.id, cliente_part.id]),
            {'estado': 'CONFIRMADO'},
        )
        self.assertEqual(response.status_code, 302)
        cliente_part.refresh_from_db()
        self.assertEqual(cliente_part.estado, 'CONFIRMADO')

        self.client.force_login(self.proveedor_user)
        response = self.client.post(
            reverse('colaboracion_k8712_cita_responder', args=[self.servicio.id, proveedor_part.id]),
            {'estado': 'CONFIRMADO'},
        )
        self.assertEqual(response.status_code, 302)
        proveedor_part.refresh_from_db()
        self.assertEqual(proveedor_part.estado, 'CONFIRMADO')

    def test_cliente_no_puede_responder_por_proveedor(self):
        cita = ActividadItinerario.objects.create(
            evento=self.evento, servicio_evento=self.servicio, proveedor=self.proveedor,
            tipo='CITA', titulo='Visita', fecha=timezone.localdate() + timedelta(days=1),
            hora_inicio=time(9, 0),
        )
        participante = ParticipanteActividad.objects.create(
            actividad=cita, proveedor=self.proveedor, rol='PROVEEDOR', estado='PENDIENTE',
        )
        self.client.force_login(self.cliente)
        response = self.client.post(
            reverse('colaboracion_k8712_cita_responder', args=[self.servicio.id, participante.id]),
            {'estado': 'CONFIRMADO'},
        )
        self.assertEqual(response.status_code, 403)

    def test_dashboard_explica_accion_cliente_y_proveedor(self):
        AprobacionServicio.objects.create(
            servicio_evento=self.servicio,
            titulo='Aprobar centro de mesa',
            estado='PENDIENTE',
            solicitado_por=self.planner,
        )
        CotizacionServicio.objects.create(
            servicio_evento=self.servicio,
            version=1,
            costo_proveedor=Decimal('18500'),
            estado='ENVIADA',
            creado_por=self.proveedor_user,
        )
        ctx = construir_contexto_dashboard_evento_v3(
            self.evento,
            servicios_evento=ServicioEvento.objects.filter(evento=self.evento),
            tareas_evento=TareaEvento.objects.filter(evento=self.evento),
            actividades_evento=ActividadItinerario.objects.filter(evento=self.evento),
            gastos_evento=GastoEvento.objects.filter(evento=self.evento).prefetch_related('pagos'),
            documentos_evento=DocumentoEvento.objects.filter(evento=self.evento),
        )
        servicio = ctx['servicios_v3'][0]
        self.assertEqual(servicio.cliente_accion_v3['titulo'], 'Esperando aprobación')
        self.assertEqual(servicio.cliente_accion_v3['responsable'], 'Cliente')
        self.assertEqual(servicio.proveedor_accion_v3['titulo'], 'Revisar cotización del proveedor')
        self.assertEqual(servicio.proveedor_accion_v3['responsable'], 'Planner')


    def test_dashboard_evento_es_interno_y_redirige_roles_externos(self):
        self.client.force_login(self.cliente)
        response = self.client.get(reverse('dashboard'), {'evento': self.evento.id})
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('portal_cliente'), response.url)

        self.client.force_login(self.proveedor_user)
        response = self.client.get(reverse('dashboard'), {'evento': self.evento.id})
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('portal_proveedor'), response.url)

        self.client.force_login(self.planner)
        response = self.client.get(reverse('dashboard'), {'evento': self.evento.id})
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'Compatibilidad temporal')

    def test_tarea_y_cita_tienen_semantica_independiente(self):
        tarea = TareaEvento.objects.create(
            evento=self.evento,
            servicio_evento=self.servicio,
            titulo='Revisar contrato',
            fecha_limite=timezone.localdate() + timedelta(days=2),
        )
        cita = ActividadItinerario.objects.create(
            evento=self.evento,
            servicio_evento=self.servicio,
            tipo='CITA',
            titulo='Reunión',
            fecha=timezone.localdate() + timedelta(days=2),
            hora_inicio=time(12, 0),
        )
        self.assertFalse(tarea.es_cita_agenda)
        self.assertTrue(cita.requiere_confirmacion)
