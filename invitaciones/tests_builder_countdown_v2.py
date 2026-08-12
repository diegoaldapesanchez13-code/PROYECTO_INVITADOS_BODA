from datetime import datetime, timezone as datetime_timezone

from django.contrib.auth import get_user_model
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


def utc_iso(value):
    return (
        value
        .astimezone(datetime_timezone.utc)
        .isoformat()
    )


class BuilderCountdownContextTests(TestCase):
    def setUp(self):
        current_timezone = (
            timezone.get_current_timezone()
        )

        self.ceremony = datetime(
            2030,
            5,
            10,
            12,
            0,
            tzinfo=current_timezone,
        )
        self.reception = datetime(
            2030,
            5,
            10,
            18,
            0,
            tzinfo=current_timezone,
        )
        self.evento = EventoBoda.objects.create(
            novio="Diego",
            novia="Fernanda",
            frase_portada="Test",
            mensaje_general="Test",
            fecha_misa=self.ceremony,
            lugar_misa="Ceremonia",
            fecha_fiesta=self.reception,
            lugar_fiesta="Recepción",
        )

    def test_event_context_is_canonical_utc_and_uses_earliest_event_start(self):
        data = serializar_contexto_evento(
            self.evento,
        )

        self.assertEqual(
            data["eventDate"],
            utc_iso(self.ceremony),
        )
        self.assertEqual(
            data["ceremonyDate"],
            utc_iso(self.ceremony),
        )
        self.assertEqual(
            data["receptionDate"],
            utc_iso(self.reception),
        )

    def test_editor_bootstrap_contains_event_context(self):
        User = get_user_model()
        user = User.objects.create_superuser(
            username="countdown_admin",
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

        bootstrap = response.context[
            "builder_bootstrap"
        ]

        self.assertEqual(
            bootstrap["event"]["ceremonyDate"],
            utc_iso(self.ceremony),
        )
        self.assertEqual(
            bootstrap["event"]["receptionDate"],
            utc_iso(self.reception),
        )

    def test_public_bootstrap_contains_same_event_context(self):
        grupo = Grupoinvitacion.objects.create(
            evento=self.evento,
            nombre_grupo="Familia Countdown",
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

        event = response.context[
            "builder_public_bootstrap"
        ]["event"]

        self.assertEqual(
            event["eventDate"],
            utc_iso(self.ceremony),
        )
        self.assertEqual(
            event["ceremonyDate"],
            utc_iso(self.ceremony),
        )
        self.assertEqual(
            event["receptionDate"],
            utc_iso(self.reception),
        )
