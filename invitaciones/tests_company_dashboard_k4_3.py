from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from organizaciones.models import (
    EmpresaSuscriptora,
    MembresiaEmpresa,
)
from proveedores.models import Proveedor


class CompanyDashboardK43Tests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.empresa = EmpresaSuscriptora.objects.create(
            nombre_comercial="Casa K43",
            slug="casa-k43",
        )
        self.admin = User.objects.create_user(
            username="admin_k43",
            password="test123",
        )
        MembresiaEmpresa.objects.create(
            empresa=self.empresa,
            usuario=self.admin,
            rol="ADMIN_EMPRESA",
        )
        self.planner = User.objects.create_user(
            username="planner_k43",
            password="test123",
        )
        MembresiaEmpresa.objects.create(
            empresa=self.empresa,
            usuario=self.planner,
            rol="WEDDING_PLANNER",
        )
        self.cliente = User.objects.create_user(
            username="cliente_k43",
            password="test123",
        )
        MembresiaEmpresa.objects.create(
            empresa=self.empresa,
            usuario=self.cliente,
            rol="CLIENTE",
        )
        self.proveedor_user = User.objects.create_user(
            username="proveedor_k43",
            password="test123",
        )
        self.proveedor = Proveedor.objects.create(
            empresa=self.empresa,
            usuario=self.proveedor_user,
            nombre_comercial="Proveedor K43",
            tipo_proveedor="DJ",
            activo=True,
        )
        MembresiaEmpresa.objects.create(
            empresa=self.empresa,
            usuario=self.proveedor_user,
            rol="PROVEEDOR",
        )
        self.client.force_login(self.admin)

    def test_clients_team_and_providers_have_separate_modules(self):
        response = self.client.get(
            reverse("dashboard_empresa")
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            'href="#clientes" data-role-link',
        )
        self.assertContains(
            response,
            'href="#equipo" data-role-link',
        )
        self.assertContains(
            response,
            'href="#proveedores" data-role-link',
        )

    def test_team_context_contains_only_internal_roles(self):
        response = self.client.get(
            reverse("dashboard_empresa")
        )
        team = list(
            response.context["membresias_equipo"]
        )
        roles = {item.rol for item in team}

        self.assertIn(
            "ADMIN_EMPRESA",
            roles,
        )
        self.assertIn(
            "WEDDING_PLANNER",
            roles,
        )
        self.assertNotIn(
            "CLIENTE",
            roles,
        )
        self.assertNotIn(
            "PROVEEDOR",
            roles,
        )

        role_values = {
            value
            for value, _
            in response.context["roles_equipo"]
        }
        self.assertEqual(
            role_values,
            {
                "ADMIN_EMPRESA",
                "VENTAS",
                "WEDDING_PLANNER",
            },
        )

    def test_provider_is_not_a_catalog_subpanel_anymore(self):
        response = self.client.get(
            reverse("dashboard_empresa")
        )
        content = response.content.decode()

        self.assertContains(
            response,
            'id="proveedores" data-role-panel',
        )
        self.assertNotIn(
            'data-subpanel-button="proveedores"',
            content[
                content.index('id="catalogos"'):
            ],
        )

    def test_identity_fields_remain_for_all_account_types(self):
        response = self.client.get(
            reverse("dashboard_empresa")
        )
        self.assertContains(
            response,
            'name="username_usuario"',
        )
        self.assertContains(
            response,
            'name="email_usuario"',
        )
        self.assertContains(
            response,
            'name="telefono_usuario"',
        )
        self.assertContains(
            response,
            'name="password_usuario"',
        )
        self.assertContains(
            response,
            "Acceso al portal proveedor",
        )
