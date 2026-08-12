from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from invitaciones.models import EventoBoda
from organizaciones.models import EmpresaSuscriptora, MembresiaEmpresa


class TenantRouteK1Tests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.a = EmpresaSuscriptora.objects.create(
            nombre_comercial="Casa A",
            slug="casa-a",
        )
        self.b = EmpresaSuscriptora.objects.create(
            nombre_comercial="Casa B",
            slug="casa-b",
        )
        self.admin = User.objects.create_user(
            username="admin_a",
            password="test123",
        )
        MembresiaEmpresa.objects.create(
            empresa=self.a,
            usuario=self.admin,
            rol="ADMIN_EMPRESA",
        )
        self.planner = User.objects.create_user(
            username="planner_a",
            password="test123",
        )
        MembresiaEmpresa.objects.create(
            empresa=self.a,
            usuario=self.planner,
            rol="WEDDING_PLANNER",
        )
        self.evento = EventoBoda.objects.create(
            empresa=self.a,
            wedding_planner=self.planner,
            novio="A",
            novia="B",
            frase_portada="Test",
            mensaje_general="Test",
            fecha_misa=timezone.now(),
            lugar_misa="Ceremonia",
            fecha_fiesta=timezone.now(),
            lugar_fiesta="Recepción",
        )

    def test_company_query_cannot_switch_tenant(self):
        self.client.force_login(self.admin)
        response = self.client.get(
            reverse("dashboard_empresa")
            + f"?empresa={self.b.id}"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["empresa"], self.a)

    def test_cross_tenant_company_slug_is_404(self):
        self.client.force_login(self.admin)
        response = self.client.get(
            reverse("empresa_dashboard", args=[self.b.slug])
        )
        self.assertEqual(response.status_code, 404)

    def test_event_dashboard_hides_company_selector(self):
        self.client.force_login(self.admin)
        response = self.client.get(
            reverse("dashboard")
            + f"?evento={self.evento.id}"
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(
            response,
            '<select id="empresa"',
        )

    def test_planner_query_cannot_switch_tenant(self):
        self.client.force_login(self.planner)
        response = self.client.get(
            reverse("dashboard_planner")
            + f"?empresa={self.b.id}"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context["empresa_actual"],
            self.a,
        )

    def test_cross_tenant_planner_slug_is_404(self):
        self.client.force_login(self.planner)
        response = self.client.get(
            reverse(
                "planner_dashboard_empresa",
                args=[self.b.slug],
            )
        )
        self.assertEqual(response.status_code, 404)
