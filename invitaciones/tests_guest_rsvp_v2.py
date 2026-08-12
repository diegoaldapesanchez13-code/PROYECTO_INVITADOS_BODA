import json

from django.test import TestCase
from django.urls import reverse

from invitaciones.guest_domain import asegurar_roster_grupo
from invitaciones.models import EventoBoda, Grupoinvitacion, Invitado


class GuestRsvpV2Tests(TestCase):
    def setUp(self):
        self.evento = EventoBoda.objects.create(
            novio="Diego",
            novia="Fernanda",
            frase_portada="Test",
            mensaje_general="Test",
            fecha_misa="2027-01-01T12:00:00Z",
            lugar_misa="Ceremonia",
            fecha_fiesta="2027-01-01T15:00:00Z",
            lugar_fiesta="Recepción",
        )
        self.grupo = Grupoinvitacion.objects.create(
            evento=self.evento,
            nombre_grupo="Familia Pérez",
            tipo="FAMILIAR",
        )
        self.ana = Invitado.objects.create(
            grupo=self.grupo,
            nombre="Ana Pérez",
            tipo_persona="ADULTO",
            orden=1,
        )
        self.luis = Invitado.objects.create(
            grupo=self.grupo,
            nombre="Luis Pérez",
            tipo_persona="ADULTO",
            orden=2,
        )
        self.url = reverse(
            "builder_public_rsvp_api",
            args=[self.grupo.codigo],
        )

    def post(self, guest, attending):
        return self.client.post(
            self.url,
            data=json.dumps({
                "guestId": guest.id,
                "attending": attending,
            }),
            content_type="application/json",
        )

    def test_get_returns_people_without_food_or_guest_limit_controls(self):
        response = self.client.get(self.url)

        self.assertEqual(
            response.status_code,
            200,
        )

        data = response.json()["data"]
        self.assertEqual(
            data["groupName"],
            "Familia Pérez",
        )
        self.assertEqual(
            len(data["guests"]),
            2,
        )
        self.assertEqual(
            data["guests"][0]["name"],
            "Ana Pérez",
        )

        self.assertNotIn(
            "maxGuests",
            data,
        )
        self.assertNotIn(
            "comment",
            data,
        )
        self.assertNotIn(
            "tipoPersona",
            data["guests"][0],
        )
        self.assertNotIn(
            "menu",
            data["guests"][0],
        )

    def test_each_person_confirms_independently(self):
        first = self.post(
            self.ana,
            True,
        )
        self.assertEqual(
            first.status_code,
            200,
        )

        self.ana.refresh_from_db()
        self.luis.refresh_from_db()

        self.assertIs(
            self.ana.asistira,
            True,
        )
        self.assertIsNone(
            self.luis.asistira,
        )

        second = self.post(
            self.luis,
            False,
        )
        self.assertEqual(
            second.status_code,
            200,
        )

        self.ana.refresh_from_db()
        self.luis.refresh_from_db()

        self.assertIs(
            self.ana.asistira,
            True,
        )
        self.assertIs(
            self.luis.asistira,
            False,
        )

    def test_group_legacy_summary_reads_fresh_individual_state(self):
        # The public endpoint internally prefetches the roster before it writes
        # the individual RSVP. This test protects against accidentally using
        # that stale prefetched cache for the compatibility aggregate.
        response = self.post(
            self.ana,
            True,
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.grupo.refresh_from_db()

        self.assertEqual(
            self.grupo.cantidad_confirmada,
            1,
        )
        self.assertFalse(
            self.grupo.confirmado,
        )
        self.assertIsNone(
            self.grupo.asistira,
        )

        payload = response.json()["data"]
        self.assertEqual(
            payload["confirmedGuests"],
            1,
        )
        self.assertEqual(
            payload["pendingGuests"],
            1,
        )

    def test_group_legacy_summary_is_complete_only_after_all_people_reply(self):
        self.post(
            self.ana,
            True,
        )
        self.post(
            self.luis,
            False,
        )

        self.grupo.refresh_from_db()

        self.assertEqual(
            self.grupo.cantidad_confirmada,
            1,
        )
        self.assertTrue(
            self.grupo.confirmado,
        )
        self.assertIs(
            self.grupo.asistira,
            True,
        )

    def test_guest_from_another_uuid_cannot_be_modified(self):
        other_group = Grupoinvitacion.objects.create(
            evento=self.evento,
            nombre_grupo="Otra familia",
            tipo="FAMILIAR",
        )
        outsider = Invitado.objects.create(
            grupo=other_group,
            nombre="Persona externa",
        )

        response = self.post(
            outsider,
            True,
        )

        self.assertEqual(
            response.status_code,
            404,
        )

        outsider.refresh_from_db()
        self.assertIsNone(
            outsider.asistira,
        )

    def test_personal_can_have_zero_or_authorized_extra_people(self):
        personal = Grupoinvitacion.objects.create(
            evento=self.evento,
            nombre_grupo="Carlos",
            tipo="PERSONAL",
            permitir_acompanantes_extra=True,
            cantidad_extra_permitida=1,
        )
        asegurar_roster_grupo(personal)

        people = list(
            personal.invitados.order_by(
                "orden",
                "id",
            )
        )

        self.assertEqual(
            len(people),
            2,
        )
        self.assertEqual(
            personal.invitados.filter(
                es_acompanante_extra=True
            ).count(),
            1,
        )
