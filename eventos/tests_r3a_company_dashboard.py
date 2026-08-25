from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from invitaciones.models import EventoBoda
from organizaciones.models import EmpresaSuscriptora, MembresiaEmpresa


class CompanyDashboardR3ATests(TestCase):
    def setUp(self):
        self.User = get_user_model()
        self.empresa = EmpresaSuscriptora.objects.create(nombre_comercial="Empresa R3A", slug="empresa-r3a")
        self.otra = EmpresaSuscriptora.objects.create(nombre_comercial="Otra R3A", slug="otra-r3a")
        self.admin = self.User.objects.create_user(username="admin-r3a", password="Pass-R3A-2026!")
        MembresiaEmpresa.objects.create(empresa=self.empresa, usuario=self.admin, rol="ADMIN_EMPRESA")
        self.planner = self.User.objects.create_user(username="planner-r3a", password="Pass-R3A-2026!")
        MembresiaEmpresa.objects.create(empresa=self.empresa, usuario=self.planner, rol="WEDDING_PLANNER")

    def test_company_dashboard_uses_new_app_shell(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse("empresa_dashboard", kwargs={"empresa_slug": self.empresa.slug}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Esto es lo que necesita tu atención hoy")
        self.assertContains(response, "company_dashboard_r3.css")
        self.assertContains(response, "+ Nuevo evento")

    def test_dashboard_is_tenant_scoped(self):
        EventoBoda.objects.create(empresa=self.empresa, nombre_evento="Visible")
        EventoBoda.objects.create(empresa=self.otra, nombre_evento="No visible")
        self.client.force_login(self.admin)
        response = self.client.get(reverse("empresa_dashboard", kwargs={"empresa_slug": self.empresa.slug}))
        self.assertContains(response, "Visible")
        self.assertNotContains(response, "No visible")

    def test_planner_cannot_open_company_dashboard(self):
        self.client.force_login(self.planner)
        response = self.client.get(reverse("empresa_dashboard", kwargs={"empresa_slug": self.empresa.slug}))
        self.assertEqual(response.status_code, 403)

    def test_upcoming_event_uses_generic_date(self):
        EventoBoda.objects.create(
            empresa=self.empresa,
            nombre_evento="Próximo R3A",
            estado="ACTIVO",
            fecha_inicio=timezone.now() + timezone.timedelta(days=10),
        )
        self.client.force_login(self.admin)
        response = self.client.get(reverse("empresa_dashboard", kwargs={"empresa_slug": self.empresa.slug}))
        self.assertContains(response, "Próximo R3A")

    def test_missing_data_produces_attention_item(self):
        EventoBoda.objects.create(
            empresa=self.empresa,
            nombre_evento="Incompleto R3A",
            estado="ACTIVO",
        )
        self.client.force_login(self.admin)
        response = self.client.get(reverse("empresa_dashboard", kwargs={"empresa_slug": self.empresa.slug}))
        self.assertContains(response, "Incompleto R3A")
        self.assertContains(response, "Fecha por definir")
        self.assertContains(response, "Sin planner")

    def test_event_navigation_remains_canonical(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse("empresa_dashboard", kwargs={"empresa_slug": self.empresa.slug}))
        self.assertContains(response, reverse("k9_evento_list", kwargs={"empresa_slug": self.empresa.slug}))

    def test_canonical_company_dashboard_is_read_only_entrypoint(self):
        self.client.force_login(self.admin)
        response = self.client.post(
            reverse("empresa_dashboard", kwargs={"empresa_slug": self.empresa.slug}),
            {"accion": "accion-inexistente"},
        )
        self.assertEqual(response.status_code, 405)
