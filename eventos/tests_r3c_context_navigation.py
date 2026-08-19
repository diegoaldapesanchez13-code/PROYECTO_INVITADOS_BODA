from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from invitaciones.models import EventoBoda
from organizaciones.models import EmpresaSuscriptora, MembresiaEmpresa


class ReturnContextR3CTests(TestCase):
    def setUp(self):
        self.User = get_user_model()
        self.empresa = EmpresaSuscriptora.objects.create(
            nombre_comercial="Empresa R3C",
            slug="empresa-r3c",
        )
        self.otra = EmpresaSuscriptora.objects.create(
            nombre_comercial="Otra R3C",
            slug="otra-r3c",
        )
        self.admin = self.User.objects.create_user(
            username="admin-r3c",
            password="Pass-R3C-2026!",
        )
        MembresiaEmpresa.objects.create(
            empresa=self.empresa,
            usuario=self.admin,
            rol="ADMIN_EMPRESA",
        )
        self.planner = self.User.objects.create_user(
            username="planner-r3c",
            password="Pass-R3C-2026!",
        )
        MembresiaEmpresa.objects.create(
            empresa=self.empresa,
            usuario=self.planner,
            rol="WEDDING_PLANNER",
        )

    def _evento(self, planner=None):
        return EventoBoda.objects.create(
            empresa=self.empresa,
            nombre_evento="Evento R3C",
            wedding_planner=planner,
        )

    def test_company_dashboard_links_event_with_company_return_context(self):
        evento = self._evento()
        self.client.force_login(self.admin)
        response = self.client.get(
            reverse("empresa_dashboard", kwargs={"empresa_slug": self.empresa.slug})
        )
        dashboard = reverse("empresa_dashboard", kwargs={"empresa_slug": self.empresa.slug})
        target = reverse(
            "k9_evento_resumen",
            kwargs={"empresa_slug": self.empresa.slug, "evento_id": evento.id},
        )
        self.assertContains(response, f"{target}?return_to={dashboard}")

    def test_planner_dashboard_links_event_with_planner_return_context(self):
        evento = self._evento(planner=self.planner)
        self.client.force_login(self.planner)
        response = self.client.get(
            reverse("planner_dashboard_empresa_alias", kwargs={"empresa_slug": self.empresa.slug})
        )
        dashboard = reverse(
            "planner_dashboard_empresa_alias",
            kwargs={"empresa_slug": self.empresa.slug},
        )
        target = reverse(
            "k9_evento_resumen",
            kwargs={"empresa_slug": self.empresa.slug, "evento_id": evento.id},
        )
        self.assertContains(response, f"{target}?return_to={dashboard}")

    def test_workspace_preserves_company_return_across_tabs(self):
        evento = self._evento()
        dashboard = reverse("empresa_dashboard", kwargs={"empresa_slug": self.empresa.slug})
        self.client.force_login(self.admin)
        response = self.client.get(
            reverse(
                "k9_evento_resumen",
                kwargs={"empresa_slug": self.empresa.slug, "evento_id": evento.id},
            ),
            {"return_to": dashboard},
        )
        self.assertContains(response, 'href="' + dashboard + '"')
        datos = reverse(
            "k9_evento_datos",
            kwargs={"empresa_slug": self.empresa.slug, "evento_id": evento.id},
        )
        self.assertContains(response, datos + "?return_to=")

    def test_external_return_context_is_rejected(self):
        evento = self._evento()
        self.client.force_login(self.admin)
        response = self.client.get(
            reverse(
                "k9_evento_resumen",
                kwargs={"empresa_slug": self.empresa.slug, "evento_id": evento.id},
            ),
            {"return_to": "https://evil.example/phish"},
        )
        dashboard = reverse("empresa_dashboard", kwargs={"empresa_slug": self.empresa.slug})
        self.assertEqual(response.context["return_to"], dashboard)
        self.assertNotContains(response, "evil.example")

    def test_cross_tenant_return_context_is_rejected(self):
        evento = self._evento()
        self.client.force_login(self.admin)
        malicious = reverse("empresa_dashboard", kwargs={"empresa_slug": self.otra.slug})
        response = self.client.get(
            reverse(
                "k9_evento_resumen",
                kwargs={"empresa_slug": self.empresa.slug, "evento_id": evento.id},
            ),
            {"return_to": malicious},
        )
        expected = reverse("empresa_dashboard", kwargs={"empresa_slug": self.empresa.slug})
        self.assertEqual(response.context["return_to"], expected)

    def test_save_data_preserves_same_module_and_return_context(self):
        evento = self._evento()
        dashboard = reverse("empresa_dashboard", kwargs={"empresa_slug": self.empresa.slug})
        self.client.force_login(self.admin)
        response = self.client.post(
            reverse(
                "k9_evento_datos",
                kwargs={"empresa_slug": self.empresa.slug, "evento_id": evento.id},
            ),
            {
                "return_to": dashboard,
                "nombre_evento": "Evento actualizado R3C",
                "tipo_evento": "OTRO",
                "fecha_inicio": "",
                "fecha_fin": "",
                "cliente": "",
                "planner": "",
                "sede": "",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn(
            reverse(
                "k9_evento_datos",
                kwargs={"empresa_slug": self.empresa.slug, "evento_id": evento.id},
            ),
            response["Location"],
        )
        self.assertIn("return_to=", response["Location"])

    def test_delete_error_returns_to_source_dashboard(self):
        evento = self._evento()
        dashboard = reverse("empresa_dashboard", kwargs={"empresa_slug": self.empresa.slug})
        self.client.force_login(self.admin)
        response = self.client.post(
            reverse(
                "k9_evento_eliminar_error",
                kwargs={"empresa_slug": self.empresa.slug, "evento_id": evento.id},
            ),
            {"confirmacion": "ELIMINAR", "return_to": dashboard},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], dashboard)

    def test_event_list_defaults_back_to_role_home(self):
        self.client.force_login(self.planner)
        response = self.client.get(
            reverse("k9_evento_list", kwargs={"empresa_slug": self.empresa.slug})
        )
        expected = reverse(
            "planner_dashboard_empresa_alias",
            kwargs={"empresa_slug": self.empresa.slug},
        )
        self.assertEqual(response.context["return_to"], expected)
