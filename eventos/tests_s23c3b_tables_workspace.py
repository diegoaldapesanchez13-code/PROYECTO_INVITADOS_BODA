from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from invitaciones.models import EventoBoda, Grupoinvitacion, Invitado
from mesas.models import AsignacionMesa, Mesa
from organizaciones.models import EmpresaSuscriptora, MembresiaEmpresa


class TablesWorkspaceS23C3BTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.empresa = EmpresaSuscriptora.objects.create(
            nombre_comercial="Empresa C3B",
            slug="empresa-c3b",
        )
        self.admin = User.objects.create_user(
            username="admin-c3b",
            password="Pass-C3B-2026!",
        )
        self.ventas = User.objects.create_user(
            username="ventas-c3b",
            password="Pass-C3B-2026!",
        )
        MembresiaEmpresa.objects.create(
            empresa=self.empresa,
            usuario=self.admin,
            rol="ADMIN_EMPRESA",
        )
        MembresiaEmpresa.objects.create(
            empresa=self.empresa,
            usuario=self.ventas,
            rol="VENTAS",
        )
        self.evento = EventoBoda.objects.create(
            empresa=self.empresa,
            nombre_evento="Evento C3B",
        )
        self.grupo = Grupoinvitacion.objects.create(
            evento=self.evento,
            nombre_grupo="Familia C3B",
            tipo="FAMILIAR",
            cantidad_maxima=2,
        )
        self.invitado = Invitado.objects.create(
            grupo=self.grupo,
            nombre="Persona C3B",
            asistira=True,
        )

    def url(self):
        return reverse(
            "k9_evento_mesas",
            kwargs={
                "empresa_slug": self.empresa.slug,
                "evento_id": self.evento.id,
            },
        )

    def test_admin_opens_tables_center_and_sees_existing_floorplan_link(self):
        self.client.force_login(self.admin)
        response = self.client.get(self.url())

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Abrir plano y acomodo")
        self.assertContains(response, reverse("mesas_visual"))
        self.assertContains(response, "Confirmados sin mesa")

    def test_tables_summary_uses_existing_models(self):
        mesa = Mesa.objects.create(
            evento=self.evento,
            nombre="Mesa 1",
            capacidad=8,
        )
        AsignacionMesa.objects.create(
            mesa=mesa,
            invitado=self.invitado,
        )

        self.client.force_login(self.admin)
        response = self.client.get(self.url())

        self.assertEqual(response.context["total_mesas"], 1)
        self.assertEqual(response.context["capacidad_total"], 8)
        self.assertEqual(response.context["lugares_ocupados"], 1)
        self.assertEqual(response.context["confirmados_sin_mesa"], 0)
        self.assertContains(response, "Mesa 1")

    def test_sales_role_has_no_tables_permission(self):
        self.client.force_login(self.ventas)
        response = self.client.get(self.url())
        self.assertEqual(response.status_code, 403)

    def test_tables_tab_is_enabled_only_for_existing_permission(self):
        self.client.force_login(self.admin)
        response = self.client.get(self.url())
        tables = next(
            tab
            for tab in response.context["workspace_navigation"]["tabs"]
            if tab["key"] == "mesas"
        )
        self.assertTrue(tables["enabled"])

        self.client.force_login(self.ventas)
        response = self.client.get(
            reverse(
                "k9_evento_resumen",
                kwargs={
                    "empresa_slug": self.empresa.slug,
                    "evento_id": self.evento.id,
                },
            )
        )
        tables = next(
            tab
            for tab in response.context["workspace_navigation"]["tabs"]
            if tab["key"] == "mesas"
        )
        self.assertFalse(tables["enabled"])

    def test_legacy_table_post_can_return_to_k9_tables_center(self):
        self.client.force_login(self.admin)
        response = self.client.post(
            reverse("mesas_visual"),
            {
                "accion": "crear_mesa",
                "evento_id": self.evento.id,
                "nombre_mesa": "Mesa nueva",
                "capacidad_mesa": "10",
                "tipo_mesa": "REDONDA",
                "return_to": self.url(),
            },
        )

        self.assertRedirects(
            response,
            self.url(),
            fetch_redirect_response=False,
        )
        self.assertTrue(
            Mesa.objects.filter(
                evento=self.evento,
                nombre="Mesa nueva",
            ).exists()
        )
