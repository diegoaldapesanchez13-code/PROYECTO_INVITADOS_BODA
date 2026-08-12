from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from organizaciones.models import (
    EmpresaSuscriptora,
    MembresiaEmpresa,
)


class RoleRedirectK3Tests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.empresa = EmpresaSuscriptora.objects.create(
            nombre_comercial="Casa K3",
            slug="casa-k3",
        )
        self.client_user = User.objects.create_user(
            username="fernanda_cliente",
            password="test123",
        )
        MembresiaEmpresa.objects.create(
            empresa=self.empresa,
            usuario=self.client_user,
            rol="CLIENTE",
        )

    def test_client_role_goes_to_client_portal_even_without_event(self):
        self.client.force_login(
            self.client_user
        )
        response = self.client.get(
            reverse("redirigir_por_rol")
        )
        self.assertEqual(
            response.status_code,
            302,
        )
        self.assertEqual(
            response["Location"],
            "/cliente/dashboard/",
        )

    def test_client_portal_home_does_not_point_to_root(self):
        self.client.force_login(
            self.client_user
        )
        response = self.client.get(
            reverse("portal_cliente")
        )
        self.assertEqual(
            response.status_code,
            200,
        )
        self.assertNotContains(
            response,
            'href="/">Inicio</a>',
        )
        self.assertContains(
            response,
            "Mi evento",
        )
        self.assertContains(
            response,
            "Cerrar sesión",
        )
