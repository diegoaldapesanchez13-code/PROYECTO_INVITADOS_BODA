from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from invitaciones.builder.event_context import (
    serializar_contexto_evento,
)
from invitaciones.builder.invitation_context import (
    serializar_contexto_invitacion,
)
from invitaciones.models import (
    EventoBoda,
    Grupoinvitacion,
    Invitado,
)


class BuilderJ12Tests(TestCase):
    def setUp(self):
        self.evento = EventoBoda.objects.create(
            nombre_evento="Evento J1.2",
            novio="Legacy novio",
            novia="Legacy novia",
            nombre_principal="Fernanda",
            nombre_secundario="Diego",
            frase_portada="Test",
            mensaje_general="Test",
            fecha_misa=timezone.now(),
            lugar_misa="Templo",
            fecha_fiesta=timezone.now() + timedelta(hours=4),
            lugar_fiesta="Jardín",
        )
        self.grupo = Grupoinvitacion.objects.create(
            evento=self.evento,
            nombre_grupo="Familia Pérez",
            tipo="FAMILIAR",
        )
        self.nino = Invitado.objects.create(
            grupo=self.grupo,
            nombre="Mateo",
            tipo_persona="NINO",
            menu_asignado="INFANTIL",
        )

    def test_event_binding_names_use_product_participants(self):
        data = serializar_contexto_evento(
            self.evento
        )
        self.assertEqual(
            data["primaryName"],
            "Fernanda",
        )
        self.assertEqual(
            data["secondaryName"],
            "Diego",
        )
        self.assertEqual(
            data["participantNames"],
            "Fernanda & Diego",
        )

    def test_invitation_context_can_include_real_badges(self):
        data = serializar_contexto_invitacion(
            self.grupo,
            include_guests=True,
        )
        guest = data["guests"][0]

        self.assertEqual(
            guest["personTypeLabel"],
            "Niño",
        )
        self.assertEqual(
            guest["menuLabel"],
            "Menú infantil",
        )

    def test_builder_bootstrap_contains_real_rsvp_preview_people(self):
        User = get_user_model()
        user = User.objects.create_superuser(
            username="j12_admin",
            password="test123",
        )
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "editor_invitacion_visual",
                args=[self.evento.id],
            )
        )

        self.assertEqual(
            response.status_code,
            200,
        )
        preview = response.context[
            "builder_bootstrap"
        ]["invitationPreview"]

        self.assertEqual(
            len(preview["guests"]),
            1,
        )
        self.assertEqual(
            preview["guests"][0]["menuLabel"],
            "Menú infantil",
        )

    def test_invitation_dashboard_has_no_second_visual_editor(self):
        User = get_user_model()
        user = User.objects.create_superuser(
            username="j12_dashboard",
            password="test123",
        )
        self.client.force_login(user)

        response = self.client.get(
            reverse("dashboard")
            + f"?evento={self.evento.id}#invitacion"
        )

        self.assertEqual(
            response.status_code,
            200,
        )
        self.assertContains(
            response,
            "Invitación digital",
        )

        for legacy_name in (
            'name="foto_portada"',
            'name="fondo_invitacion"',
            'name="paleta_colores"',
            'name="estilo_letra"',
            'name="sello_sobre"',
            'name="cancion"',
            'name="dress_code_permitido_imagen"',
        ):
            self.assertNotContains(
                response,
                legacy_name,
            )

    def test_content_dashboard_has_no_album_media_uploader(self):
        User = get_user_model()
        user = User.objects.create_superuser(
            username="j12_content",
            password="test123",
        )
        self.client.force_login(user)

        response = self.client.get(
            reverse("dashboard")
            + f"?evento={self.evento.id}#contenido"
        )

        self.assertNotContains(
            response,
            'name="archivo_album"',
        )
        self.assertContains(
            response,
            "Abrir Builder",
        )
