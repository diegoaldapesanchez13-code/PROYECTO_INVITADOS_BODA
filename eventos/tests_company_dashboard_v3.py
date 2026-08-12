from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from invitaciones.models import EventoBoda
from organizaciones.models import EmpresaSuscriptora, MembresiaEmpresa
from proveedores.models import ServicioEvento
from tareas.models import TareaEvento


class CompanyDashboardV3Tests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.empresa = EmpresaSuscriptora.objects.create(nombre_comercial="Empresa V3", slug="empresa-v3")
        self.admin = User.objects.create_user(username="admin_company_v3", password="test123")
        MembresiaEmpresa.objects.create(empresa=self.empresa, usuario=self.admin, rol="ADMIN_EMPRESA")
        self.evento = EventoBoda.objects.create(
            empresa=self.empresa, novio="A", novia="B", frase_portada="Test", mensaje_general="Test",
            fecha_misa=timezone.now(), lugar_misa="Ceremonia", fecha_fiesta=timezone.now(), lugar_fiesta="Recepcion",
        )
        self.servicio = ServicioEvento.objects.create(evento=self.evento, nombre_servicio="Decoracion")
        TareaEvento.objects.create(evento=self.evento, titulo="Pendiente empresa", fecha_limite=timezone.localdate())
        self.client.force_login(self.admin)

    def test_company_v3_is_business_management_not_event_operation(self):
        response = self.client.get(reverse("dashboard_empresa"))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["empresa_v3"])
        self.assertContains(response, "Gestión de empresa")
        self.assertContains(response, "Abrir evento")
        self.assertNotContains(response, ">Builder<")
        self.assertNotContains(response, ">Mesas<")
        self.assertNotContains(response, ">Calendario<")

    def test_company_v3_has_expected_management_modules(self):
        response = self.client.get(reverse("dashboard_empresa"))
        for target in ("resumen", "eventos", "clientes", "equipo", "proveedores", "catalogos", "configuracion"):
            self.assertContains(response, f'href="#{target}" data-role-link')

    def test_event_card_exposes_health_and_single_workspace_entry(self):
        response = self.client.get(reverse("dashboard_empresa"))
        cards = response.context["empresa_eventos_cards_v3"]
        self.assertEqual(len(cards), 1)
        self.assertEqual(cards[0]["servicios"], 1)
        self.assertEqual(cards[0]["tareas_pendientes"], 1)
        self.assertContains(response, "Workspace Event-Centric")

    def test_company_v3_remains_tenant_isolated(self):
        otra = EmpresaSuscriptora.objects.create(nombre_comercial="Otra", slug="otra-company-v3")
        EventoBoda.objects.create(
            empresa=otra, novio="X", novia="Y", frase_portada="T", mensaje_general="T",
            fecha_misa=timezone.now(), lugar_misa="X", fecha_fiesta=timezone.now(), lugar_fiesta="Y",
        )
        response = self.client.get(reverse("dashboard_empresa"))
        self.assertEqual(len(response.context["empresa_eventos_cards_v3"]), 1)
