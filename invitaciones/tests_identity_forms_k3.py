from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from core.models import PerfilAcceso
from organizaciones.models import (
    EmpresaSuscriptora,
    MembresiaEmpresa,
)


class IdentityFormsK3Tests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.empresa = EmpresaSuscriptora.objects.create(
            nombre_comercial="Casa Identity",
            slug="casa-identity",
        )
        self.admin = User.objects.create_user(
            username="admin_identity",
            password="test123",
        )
        MembresiaEmpresa.objects.create(
            empresa=self.empresa,
            usuario=self.admin,
            rol="ADMIN_EMPRESA",
        )
        self.client.force_login(self.admin)

    def test_create_client_saves_phone_identity(self):
        response = self.client.post(
            reverse("dashboard_empresa"),
            {
                "accion": "crear_cliente",
                "empresa_id": self.empresa.id,
                "rol_usuario": "CLIENTE",
                "username_usuario": "cliente_phone",
                "password_usuario": "temporal123",
                "first_name_usuario": "Cliente",
                "last_name_usuario": "Phone",
                "email_usuario": "cliente.phone@example.com",
                "telefono_usuario": "477-111-2233",
                "activo_usuario": "on",
            },
        )
        self.assertEqual(
            response.status_code,
            302,
        )
        user = get_user_model().objects.get(
            username="cliente_phone"
        )
        self.assertEqual(
            user.perfil_acceso.telefono_normalizado,
            "4771112233",
        )

    def test_company_dashboard_contains_identity_fields(self):
        response = self.client.get(
            reverse("dashboard_empresa")
        )
        self.assertContains(
            response,
            'name="telefono_usuario"',
        )
        self.assertContains(
            response,
            "Acceso al portal proveedor",
        )
