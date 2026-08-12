from datetime import time, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from colaboracion.models import AprobacionServicio, CotizacionServicio
from eventos.planner_dashboard_v3 import construir_contexto_dashboard_planner_v3
from itinerario.models import ActividadItinerario, ParticipanteActividad
from invitaciones.models import EventoBoda
from organizaciones.models import EmpresaSuscriptora, MembresiaEmpresa
from proveedores.models import Proveedor, ServicioEvento
from tareas.models import TareaEvento


class PlannerDashboardV3K872Tests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.empresa = EmpresaSuscriptora.objects.create(
            nombre_comercial="Empresa Planner V3",
            slug="empresa-planner-v3",
        )
        self.planner = User.objects.create_user(
            username="planner-v3",
            password="test123",
            first_name="Sofia",
        )
        self.cliente = User.objects.create_user(
            username="cliente-v3",
            password="test123",
        )
        self.proveedor_user = User.objects.create_user(
            username="proveedor-v3",
            password="test123",
        )
        for user, rol in (
            (self.planner, "WEDDING_PLANNER"),
            (self.cliente, "CLIENTE"),
            (self.proveedor_user, "PROVEEDOR"),
        ):
            MembresiaEmpresa.objects.create(
                empresa=self.empresa,
                usuario=user,
                rol=rol,
            )

        ahora = timezone.now()
        self.evento = EventoBoda.objects.create(
            empresa=self.empresa,
            wedding_planner=self.planner,
            nombre_evento="Boda Planner V3",
            novio="A",
            novia="B",
            frase_portada="Test",
            mensaje_general="Test",
            fecha_misa=ahora + timedelta(days=30),
            lugar_misa="Ceremonia",
            fecha_fiesta=ahora + timedelta(days=30),
            lugar_fiesta="Recepción",
        )
        self.evento.clientes.add(self.cliente)
        self.proveedor = Proveedor.objects.create(
            empresa=self.empresa,
            usuario=self.proveedor_user,
            nombre_comercial="Banquetes V3",
            tipo_proveedor="BANQUETE",
        )
        self.servicio = ServicioEvento.objects.create(
            evento=self.evento,
            proveedor=self.proveedor,
            nombre_servicio="Banquete",
            origen="MANUAL",
            modalidad="ADICIONAL",
        )

    def _crear_pendientes(self):
        AprobacionServicio.objects.create(
            servicio_evento=self.servicio,
            titulo="Aprobar menú",
            estado="PENDIENTE",
            solicitado_por=self.planner,
        )
        CotizacionServicio.objects.create(
            servicio_evento=self.servicio,
            version=1,
            costo_proveedor=Decimal("18500"),
            estado="ENVIADA",
            creado_por=self.proveedor_user,
        )
        TareaEvento.objects.create(
            evento=self.evento,
            servicio_evento=self.servicio,
            responsable=self.planner,
            titulo="Revisar contrato",
            fecha_limite=timezone.localdate() - timedelta(days=1),
            prioridad="URGENTE",
        )
        cita = ActividadItinerario.objects.create(
            evento=self.evento,
            servicio_evento=self.servicio,
            proveedor=self.proveedor,
            tipo="CITA",
            titulo="Prueba de menú",
            fecha=timezone.localdate() + timedelta(days=2),
            hora_inicio=time(16, 30),
        )
        ParticipanteActividad.objects.create(
            actividad=cita,
            usuario=self.cliente,
            rol="CLIENTE",
            estado="PENDIENTE",
        )
        ParticipanteActividad.objects.create(
            actividad=cita,
            proveedor=self.proveedor,
            rol="PROVEEDOR",
            estado="PENDIENTE",
        )

    def test_contexto_separa_cliente_proveedor_e_interno(self):
        self._crear_pendientes()
        ctx = construir_contexto_dashboard_planner_v3(
            eventos=[self.evento],
            planner=self.planner,
            empresa=self.empresa,
        )
        self.assertEqual(
            ctx["planner_acciones_cliente_v3"][0]["titulo"],
            "Esperando aprobación",
        )
        self.assertEqual(
            ctx["planner_acciones_proveedor_v3"][0]["titulo"],
            "Revisar cotización del proveedor",
        )
        self.assertTrue(
            any(
                item["tipo"] == "TAREA" and item["titulo"] == "Revisar contrato"
                for item in ctx["planner_acciones_internas_v3"]
            )
        )
        self.assertEqual(ctx["planner_confirmaciones_cliente_v3"], 1)
        self.assertEqual(ctx["planner_confirmaciones_proveedor_v3"], 1)

    def test_dashboard_planner_no_expone_crud_legacy_de_servicio(self):
        self.client.force_login(self.planner)
        response = self.client.get(reverse("dashboard_planner"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Bandeja de trabajo")
        self.assertContains(response, "Mis eventos")
        self.assertContains(response, "Agenda")
        self.assertNotContains(response, 'name="accion" value="asignar_proveedor_evento"')
        self.assertNotContains(response, 'name="accion" value="actualizar_servicio_evento"')
        self.assertNotContains(response, "ExpedienteServicio")

    def test_planner_ve_solo_eventos_asignados_del_tenant(self):
        otra_empresa = EmpresaSuscriptora.objects.create(
            nombre_comercial="Otra empresa",
            slug="otra-empresa-planner-v3",
        )
        otro_planner = get_user_model().objects.create_user(
            username="otro-planner-v3",
            password="test123",
        )
        MembresiaEmpresa.objects.create(
            empresa=otra_empresa,
            usuario=otro_planner,
            rol="WEDDING_PLANNER",
        )
        otro_evento = EventoBoda.objects.create(
            empresa=otra_empresa,
            wedding_planner=otro_planner,
            nombre_evento="Evento ajeno",
            novio="X",
            novia="Y",
            frase_portada="X",
            mensaje_general="X",
            fecha_misa=timezone.now() + timedelta(days=10),
            lugar_misa="X",
            fecha_fiesta=timezone.now() + timedelta(days=10),
            lugar_fiesta="X",
        )
        self.client.force_login(self.planner)
        response = self.client.get(reverse("dashboard_planner"))
        self.assertContains(response, self.evento.nombre_evento)
        self.assertNotContains(response, otro_evento.nombre_evento)

    def test_cita_pendiente_aparece_en_agenda_planner(self):
        cita = ActividadItinerario.objects.create(
            evento=self.evento,
            servicio_evento=self.servicio,
            proveedor=self.proveedor,
            tipo="CITA",
            titulo="Prueba de montaje V3",
            fecha=timezone.localdate() + timedelta(days=3),
            hora_inicio=time(11, 0),
        )
        ParticipanteActividad.objects.create(
            actividad=cita,
            usuario=self.cliente,
            rol="CLIENTE",
            estado="PENDIENTE",
        )
        self.client.force_login(self.planner)
        response = self.client.get(reverse("dashboard_planner"))
        self.assertContains(response, "Prueba de montaje V3")
        self.assertEqual(response.context["planner_confirmaciones_pendientes_v3"], 1)
