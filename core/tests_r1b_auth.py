from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class AuthExperienceR1BTests(TestCase):
    def setUp(self):
        self.User = get_user_model()
        self.password = "Prueba-Segura-2026!"
        self.user = self.User.objects.create_user(
            username="usuario_r1b",
            email="usuario-r1b@example.com",
            password=self.password,
        )

    def test_login_page_uses_new_event_studio_experience(self):
        response = self.client.get(reverse("login"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "DIRTEC Event Studio")
        self.assertContains(response, "Todo tu evento")
        self.assertContains(response, "core/app/auth.css")
        self.assertContains(response, "core/app/auth.js")
        self.assertNotContains(response, "wedding planners")

    def test_login_invalid_credentials_stay_on_login(self):
        response = self.client.post(
            reverse("login"),
            {"username": self.user.username, "password": "incorrecta"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No pudimos iniciar sesión")

    def test_login_valid_credentials_redirect_to_internal_role_router(self):
        response = self.client.post(
            reverse("login"),
            {"username": self.user.username, "password": self.password},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], "/redirigir/")

    def test_external_next_is_not_honored(self):
        response = self.client.post(
            reverse("login") + "?next=https://example.com/evil",
            {
                "username": self.user.username,
                "password": self.password,
                "next": "https://example.com/evil",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], "/redirigir/")

    def test_password_reset_form_is_neutral_and_branded(self):
        response = self.client.get(reverse("password_reset"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "DIRTEC Event Studio")
        self.assertContains(response, "Restablece tu contraseña")
        self.assertContains(response, "Si existe")

    def test_password_reset_sends_email_for_existing_account(self):
        response = self.client.post(
            reverse("password_reset"),
            {"email": self.user.email},
        )
        self.assertRedirects(response, reverse("password_reset_done"))
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("DIRTEC Event Studio", mail.outbox[0].subject)
        self.assertIn("/password-reset/", mail.outbox[0].body)

    def test_password_reset_does_not_reveal_unknown_email(self):
        response = self.client.post(
            reverse("password_reset"),
            {"email": "desconocido@example.com"},
        )
        self.assertRedirects(response, reverse("password_reset_done"))
        self.assertEqual(len(mail.outbox), 0)

    def test_password_reset_done_is_neutral(self):
        response = self.client.get(reverse("password_reset_done"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Si existe una cuenta")
        self.assertNotContains(response, self.user.email)

    def test_invalid_reset_link_has_recovery_action(self):
        response = self.client.get(
            reverse(
                "password_reset_confirm",
                kwargs={"uidb64": "invalid", "token": "invalid-token"},
            )
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Este enlace ya no es válido")
        self.assertContains(response, "Solicitar un nuevo enlace")

    def test_password_reset_complete_page_links_to_login(self):
        response = self.client.get(reverse("password_reset_complete"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Contraseña actualizada")
        self.assertContains(response, reverse("login"))

    def test_logout_returns_to_login(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse("logout"))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], reverse("login"))
