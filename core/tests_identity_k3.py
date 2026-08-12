from django.contrib.auth import authenticate, get_user_model
from django.test import TestCase

from core.services.identity import (
    crear_identidad_usuario,
    perfil_acceso_de,
)


class IdentityLoginK3Tests(TestCase):
    def setUp(self):
        self.user = crear_identidad_usuario(
            username="cliente_fer",
            email="fer@example.com",
            phone="477 807 3397",
            first_name="Fernanda",
            last_name="Flores",
            password="test12345",
        )

    def test_login_by_username(self):
        self.assertEqual(
            authenticate(
                username="cliente_fer",
                password="test12345",
            ),
            self.user,
        )

    def test_login_by_email(self):
        self.assertEqual(
            authenticate(
                username="FER@example.com",
                password="test12345",
            ),
            self.user,
        )

    def test_login_by_phone(self):
        self.assertEqual(
            authenticate(
                username="4778073397",
                password="test12345",
            ),
            self.user,
        )

    def test_phone_is_normalized(self):
        profile = perfil_acceso_de(
            self.user
        )
        self.assertEqual(
            profile.telefono_normalizado,
            "4778073397",
        )
