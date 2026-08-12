from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from invitaciones.models import EventoBoda
from organizaciones.models import EmpresaSuscriptora, MembresiaEmpresa


class CompanyDashboardK42Tests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.empresa = EmpresaSuscriptora.objects.create(
            nombre_comercial="Casa K42",
            slug="casa-k42",
        )
        self.admin = User.objects.create_user(
            username="admin_k42",
            password="test123",
        )
        MembresiaEmpresa.objects.create(
            empresa=self.empresa,
            usuario=self.admin,
            rol="ADMIN_EMPRESA",
        )
        self.evento = EventoBoda.objects.create(
            empresa=self.empresa,
            novio="A",
            novia="B",
            frase_portada="Test",
            mensaje_general="Test",
            fecha_misa=timezone.now(),
            lugar_misa="Ceremonia",
            fecha_fiesta=timezone.now(),
            lugar_fiesta="Recepcion",
        )
        self.client.force_login(self.admin)

    def test_events_are_operational_nucleus(self):
        response = self.client.get(
            reverse("dashboard_empresa")
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Portafolio")
        self.assertContains(response, "Abrir evento")
        self.assertContains(response, "Workspace Event-Centric")
        self.assertNotContains(response, ">Builder<")
        self.assertNotContains(response, ">Mesas<")
        self.assertNotContains(response, ">Calendario<")

    def test_company_dashboard_has_no_duplicate_operation_tab(self):
        response = self.client.get(
            reverse("dashboard_empresa")
        )
        self.assertNotContains(
            response,
            'href="#operacion" data-role-link',
        )
        self.assertNotContains(
            response,
            'id="operacion" data-role-panel',
        )

    def test_event_settings_remain_available_but_secondary(self):
        response = self.client.get(
            reverse("dashboard_empresa")
        )
        self.assertContains(
            response,
            "Administrar ficha del evento",
        )
        for action in (
            "editar_evento",
            "desactivar_evento",
            "eliminar_evento",
        ):
            self.assertContains(
                response,
                f'name="accion" value="{action}"',
            )
