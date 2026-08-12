from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from invitaciones.models import DisenoInvitacion, EventoBoda, Grupoinvitacion, Invitado


class BuilderJ11Tests(TestCase):
    def setUp(self):
        self.evento = EventoBoda.objects.create(
            nombre_evento="Boda J1.1",
            novio="Diego",
            novia="Fernanda",
            frase_portada="Test",
            mensaje_general="Test",
            fecha_misa=timezone.now(),
            lugar_misa="Ceremonia",
            fecha_fiesta=timezone.now(),
            lugar_fiesta="Recepción",
        )
        self.grupo = Grupoinvitacion.objects.create(
            evento=self.evento,
            nombre_grupo="Familia Pérez",
            tipo="FAMILIAR",
        )
        self.adulto = Invitado.objects.create(
            grupo=self.grupo,
            nombre="Ana",
            apellidos="Pérez",
            tipo_persona="ADULTO",
            menu_asignado="ADULTO",
            asistira=True,
        )
        self.nino = Invitado.objects.create(
            grupo=self.grupo,
            nombre="Mateo",
            tipo_persona="NINO",
            menu_asignado="SEGUN_TIPO",
            asistira=None,
        )

    def test_editor_bootstrap_has_real_invitation_preview_context(self):
        User = get_user_model()
        user = User.objects.create_superuser(username="j11", password="test123")
        self.client.force_login(user)
        response = self.client.get(reverse("editor_invitacion_visual", args=[self.evento.id]))
        self.assertEqual(response.status_code, 200)
        preview = response.context["builder_bootstrap"]["invitationPreview"]
        self.assertEqual(preview["groupName"], "Familia Pérez")
        self.assertEqual(preview["totalGuests"], 2)
        self.assertEqual(preview["confirmedGuests"], 1)
        self.assertEqual(preview["pendingGuests"], 1)

    def test_public_rsvp_exposes_visual_person_and_menu_labels(self):
        DisenoInvitacion.objects.create(
            evento=self.evento,
            documento_builder_publicado={
                "schemaVersion": 4,
                "page": {"id": "page", "name": "Invitación", "type": "PAGE", "settings": {}},
                "canvases": [],
                "nodes": [],
                "assets": [],
                "responsive": {"baseDevice": "mobile", "inheritance": {"tablet": "mobile", "desktop": "tablet"}},
                "meta": {},
            },
            estado="PUBLICADO",
        )
        response = self.client.get(reverse("builder_public_rsvp_api", args=[self.grupo.codigo]))
        self.assertEqual(response.status_code, 200)
        guests = response.json()["data"]["guests"]
        by_name = {guest["name"]: guest for guest in guests}
        self.assertEqual(by_name["Ana Pérez"]["personTypeLabel"], "Adulto")
        self.assertEqual(by_name["Ana Pérez"]["menuLabel"], "Menú adulto")
        self.assertEqual(by_name["Mateo"]["personTypeLabel"], "Niño")
        self.assertEqual(by_name["Mateo"]["menuLabel"], "Menú infantil")
        self.assertNotIn("menuEditable", by_name["Mateo"])
