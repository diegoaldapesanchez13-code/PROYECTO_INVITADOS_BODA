from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from core.services.navigation import build_navigation
from organizaciones.models import EmpresaSuscriptora, MembresiaEmpresa


class NavigationR1CTests(TestCase):
    def setUp(self):
        self.User = get_user_model()
        self.empresa_a = EmpresaSuscriptora.objects.create(
            nombre_comercial="Empresa A R1C",
            slug="empresa-a-r1c",
        )
        self.empresa_b = EmpresaSuscriptora.objects.create(
            nombre_comercial="Empresa B R1C",
            slug="empresa-b-r1c",
        )

    def _user(self, username):
        return self.User.objects.create_user(username=username, password="Pass-R1C-2026!")

    def test_dirtec_navigation(self):
        user = self._user("dirtec-r1c")
        user.is_superuser = True
        user.is_staff = True
        user.save(update_fields=["is_superuser", "is_staff"])

        nav = build_navigation(user)
        self.assertEqual(nav["role"], "DIRTEC")
        self.assertTrue(any(item["key"] == "empresas" for item in nav["items"]))

    def test_company_navigation_is_tenant_scoped(self):
        user = self._user("empresa-r1c")
        MembresiaEmpresa.objects.create(
            empresa=self.empresa_a,
            usuario=user,
            rol="ADMIN_EMPRESA",
        )

        nav = build_navigation(user, empresa=self.empresa_a)
        self.assertEqual(nav["role"], "EMPRESA")
        urls = " ".join(item["url"] for item in nav["items"])
        self.assertIn(self.empresa_a.slug, urls)
        self.assertNotIn(self.empresa_b.slug, urls)

    def test_planner_navigation_uses_generic_planner_alias(self):
        user = self._user("planner-r1c")
        MembresiaEmpresa.objects.create(
            empresa=self.empresa_a,
            usuario=user,
            rol="WEDDING_PLANNER",
        )
        nav = build_navigation(user, empresa=self.empresa_a)
        self.assertEqual(nav["role"], "PLANNER")
        dashboard = next(item for item in nav["items"] if item["key"] == "inicio")
        self.assertIn("/planner/dashboard/", dashboard["url"])
        self.assertNotIn("/wedding-planner/", dashboard["url"])

    def test_client_navigation_does_not_expose_company_backoffice(self):
        user = self._user("cliente-r1c")
        MembresiaEmpresa.objects.create(
            empresa=self.empresa_a,
            usuario=user,
            rol="CLIENTE",
        )
        nav = build_navigation(user, empresa=self.empresa_a)
        self.assertEqual(nav["role"], "CLIENTE")
        urls = " ".join(item["url"] for item in nav["items"])
        self.assertIn("/cliente/dashboard/", urls)
        self.assertNotIn("/empresa/", urls)

    def test_provider_navigation_does_not_expose_company_backoffice(self):
        user = self._user("proveedor-r1c")
        MembresiaEmpresa.objects.create(
            empresa=self.empresa_a,
            usuario=user,
            rol="PROVEEDOR",
        )
        nav = build_navigation(user, empresa=self.empresa_a)
        self.assertEqual(nav["role"], "PROVEEDOR")
        urls = " ".join(item["url"] for item in nav["items"])
        self.assertIn("/proveedor/dashboard/", urls)
        self.assertNotIn("/empresa/", urls)

    def test_active_item_is_marked(self):
        user = self._user("empresa-active-r1c")
        MembresiaEmpresa.objects.create(
            empresa=self.empresa_a,
            usuario=user,
            rol="ADMIN_EMPRESA",
        )
        nav = build_navigation(user, empresa=self.empresa_a, active_key="eventos")
        active = [item for item in nav["items"] if item["active"]]
        self.assertEqual(len(active), 1)
        self.assertEqual(active[0]["key"], "eventos")

    def test_preview_requires_login(self):
        response = self.client.get(reverse("app_shell_preview"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login/", response["Location"])

    def test_company_preview_renders_brand_and_navigation(self):
        user = self._user("preview-company-r1c")
        MembresiaEmpresa.objects.create(
            empresa=self.empresa_a,
            usuario=user,
            rol="ADMIN_EMPRESA",
        )
        self.client.force_login(user)
        response = self.client.get(reverse("app_shell_preview"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Empresa A R1C")
        self.assertContains(response, "Navegación por rol")
        self.assertContains(response, "Eventos")

    def test_preview_includes_mobile_navigation(self):
        user = self._user("preview-mobile-r1c")
        MembresiaEmpresa.objects.create(
            empresa=self.empresa_a,
            usuario=user,
            rol="WEDDING_PLANNER",
        )
        self.client.force_login(user)
        response = self.client.get(reverse("app_shell_preview"))
        self.assertContains(response, 'aria-label="Navegación móvil"')
        self.assertContains(response, "Mis eventos")
