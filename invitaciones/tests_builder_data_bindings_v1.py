from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from invitaciones.builder.event_context import (
    serializar_contexto_evento,
)
from invitaciones.models import (
    DisenoInvitacion,
    EventoBoda,
    Grupoinvitacion,
)


class BuilderDataBindingsV1Tests(TestCase):
    def setUp(self):
        self.evento = EventoBoda.objects.create(
            nombre_evento="Boda D & F",
            novio="Diego",
            novia="Fernanda",
            frase_portada="Test",
            mensaje_general="Test",
            fecha_misa=timezone.now(),
            lugar_misa="Templo Expiatorio",
            fecha_fiesta=timezone.now(),
            lugar_fiesta="Casa Cisneros",
        )

    def test_event_context_contains_reusable_template_fields(self):
        data = serializar_contexto_evento(
            self.evento
        )

        self.assertEqual(
            data["groomName"],
            "Diego",
        )
        self.assertEqual(
            data["brideName"],
            "Fernanda",
        )
        self.assertEqual(
            data["coupleNames"],
            "Diego & Fernanda",
        )
        self.assertEqual(
            data["ceremonyPlace"],
            "Templo Expiatorio",
        )
        self.assertEqual(
            data["receptionPlace"],
            "Casa Cisneros",
        )
        self.assertTrue(
            data["ceremonyDateText"],
        )
        self.assertTrue(
            data["receptionTimeText"],
        )

    def test_public_invitation_context_contains_group_binding_fields(self):
        grupo = Grupoinvitacion.objects.create(
            evento=self.evento,
            nombre_grupo="Familia Pérez",
            tipo="FAMILIAR",
        )

        DisenoInvitacion.objects.create(
            evento=self.evento,
            documento_builder_publicado={
                "schemaVersion": 4,
                "page": {
                    "id": "page",
                    "name": "Invitación",
                    "type": "PAGE",
                    "settings": {},
                },
                "canvases": [],
                "nodes": [],
                "assets": [],
                "responsive": {
                    "baseDevice": "mobile",
                    "inheritance": {
                        "tablet": "mobile",
                        "desktop": "tablet",
                    },
                },
                "meta": {},
            },
            estado="PUBLICADO",
        )

        response = self.client.get(
            reverse(
                "ver_invitacion",
                args=[grupo.codigo],
            )
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        invitation = response.context[
            "builder_public_bootstrap"
        ]["invitation"]

        self.assertEqual(
            invitation["groupName"],
            "Familia Pérez",
        )
        self.assertEqual(
            invitation["groupTypeLabel"],
            "Familiar",
        )
        self.assertEqual(
            invitation["totalGuests"],
            0,
        )
