from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from invitaciones.models import DisenoInvitacion, EventoBoda, Grupoinvitacion, Invitado
from organizaciones.models import EmpresaSuscriptora, MembresiaEmpresa


class InvitationWorkspaceS23C3ATests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.empresa = EmpresaSuscriptora.objects.create(
            nombre_comercial="Empresa C3A",
            slug="empresa-c3a",
        )
        self.admin = User.objects.create_user(
            username="admin-c3a",
            password="Pass-C3A-2026!",
        )
        MembresiaEmpresa.objects.create(
            empresa=self.empresa,
            usuario=self.admin,
            rol="ADMIN_EMPRESA",
        )
        self.evento = EventoBoda.objects.create(
            empresa=self.empresa,
            nombre_evento="Evento C3A",
        )
        self.grupo = Grupoinvitacion.objects.create(
            evento=self.evento,
            nombre_grupo="Familia C3A",
            tipo="FAMILIAR",
            cantidad_maxima=2,
        )
        Invitado.objects.create(
            grupo=self.grupo,
            nombre="Persona C3A",
            orden=1,
        )

    def url(self):
        return reverse(
            "k9_evento_invitacion",
            kwargs={
                "empresa_slug": self.empresa.slug,
                "evento_id": self.evento.id,
            },
        )

    def test_company_admin_can_open_invitation_center(self):
        self.client.force_login(self.admin)
        response = self.client.get(self.url())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "DIRTEC Builder")
        self.assertContains(response, "Gestionar RSVP e invitados")
        self.assertContains(response, "Abrir Builder")

    def test_invitation_tab_is_enabled(self):
        self.client.force_login(self.admin)
        response = self.client.get(self.url())
        tabs = response.context["workspace_navigation"]["tabs"]
        invitation = next(tab for tab in tabs if tab["key"] == "invitacion")
        self.assertTrue(invitation["enabled"])
        self.assertEqual(invitation["url"], self.url())

    def test_published_group_gets_public_link(self):
        DisenoInvitacion.objects.create(
            evento=self.evento,
            documento_builder_borrador={"schemaVersion": 3, "page": {}, "sections": [], "nodes": []},
            documento_builder_publicado={"schemaVersion": 3, "page": {}, "sections": [], "nodes": []},
            estado="PUBLICADO",
        )
        self.client.force_login(self.admin)
        response = self.client.get(self.url())
        public_url = reverse("ver_invitacion", args=[self.grupo.codigo])
        self.assertContains(response, public_url)
        self.assertContains(response, "Ver invitación publicada")
