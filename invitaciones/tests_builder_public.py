import json

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from invitaciones.builder.services import BUILDER_BUILD_VERSION
from invitaciones.models import (
    DisenoInvitacion,
    EventoBoda,
    Grupoinvitacion,
    Invitado,
)


class BuilderPublicRendererTests(TestCase):
    def setUp(self):
        now = timezone.now()
        self.evento = EventoBoda.objects.create(
            nombre_evento="PHASE E Public Renderer",
            novio="Diego",
            novia="Fernanda",
            frase_portada="Portada de prueba",
            mensaje_general="Mensaje de prueba",
            fecha_misa=now,
            lugar_misa="Ceremonia de prueba",
            fecha_fiesta=now,
            lugar_fiesta="Recepción de prueba",
        )
        self.grupo = Grupoinvitacion.objects.create(
            evento=self.evento,
            nombre_grupo="Familia Test",
            tipo="PERSONAL",
            cantidad_maxima=2,
            cantidad_extra_permitida=1,
            permitir_acompanantes_extra=True,
        )
        self.titular = Invitado.objects.create(
            grupo=self.grupo,
            nombre="Familia Test",
            tipo_persona="ADULTO",
            orden=0,
            es_acompanante_extra=False,
        )
        self.acompanante = Invitado.objects.create(
            grupo=self.grupo,
            nombre="Acompañante 1",
            tipo_persona="ADULTO",
            orden=1,
            es_acompanante_extra=True,
        )

        self.document = {
            "schemaVersion": 3,
            "page": {"name": "Public"},
            "sections": [
                {
                    "id": "section-1",
                    "type": "SECTION",
                    "name": "Portada",
                    "parentId": None,
                    "order": 0,
                    "visible": True,
                    "locked": False,
                    "x": 50,
                    "y": 50,
                    "width": 100,
                    "height": 800,
                    "minHeight": 800,
                    "rotation": 0,
                    "scale": 1,
                    "opacity": 1,
                    "zIndex": 1,
                    "coordinateSpace": "CANVAS",
                    "layoutMode": "FLOW",
                    "style": {},
                    "content": {},
                    "responsive": {},
                }
            ],
            "nodes": [],
        }
        self.diseno = DisenoInvitacion.objects.create(
            evento=self.evento,
            documento_builder_borrador=self.document,
            documento_builder_publicado=self.document,
            estado="PUBLICADO",
        )

    def test_public_route_uses_v3_template(self):
        response = self.client.get(
            reverse("ver_invitacion", args=[self.grupo.codigo])
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response,
            "invitaciones/builder/public_invitation.html",
        )
        self.assertContains(
            response,
            "dirtec-builder-public-bootstrap",
        )

    def test_public_bootstrap_schema_version_is_v4(self):
        response = self.client.get(
            reverse("ver_invitacion", args=[self.grupo.codigo])
        )
        bootstrap = response.context["builder_public_bootstrap"]

        self.assertEqual(
            bootstrap["schemaVersion"],
            4,
        )
        self.assertEqual(
            bootstrap["buildVersion"],
            BUILDER_BUILD_VERSION,
        )
        self.assertEqual(
            bootstrap["document"]["schemaVersion"],
            3,
        )
        self.assertContains(
            response,
            f"?v={BUILDER_BUILD_VERSION}",
        )

        invitation = bootstrap["invitation"]
        self.assertEqual(
            invitation["groupName"],
            "Familia Test",
        )
        self.assertEqual(
            len(invitation["guests"]),
            2,
        )
        self.assertNotIn(
            "maxGuests",
            invitation,
        )
        self.assertNotIn(
            "comment",
            invitation,
        )

    def test_public_route_does_not_expose_draft_to_guest(self):
        self.diseno.documento_builder_borrador = {
            **self.document,
            "page": {"name": "SECRET-DRAFT"},
        }
        self.diseno.save(
            update_fields=["documento_builder_borrador"]
        )

        response = self.client.get(
            reverse(
                "ver_invitacion",
                args=[self.grupo.codigo],
            ) + "?preview=1"
        )

        self.assertNotContains(
            response,
            "SECRET-DRAFT",
        )

    def test_rsvp_get_and_post(self):
        url = reverse(
            "builder_public_rsvp_api",
            args=[self.grupo.codigo],
        )

        response = self.client.get(url)
        self.assertEqual(
            response.status_code,
            200,
        )

        data = response.json()["data"]
        self.assertEqual(
            len(data["guests"]),
            2,
        )
        self.assertIsNone(
            data["guests"][0]["attending"],
        )
        self.assertIsNone(
            data["guests"][1]["attending"],
        )

        response = self.client.post(
            url,
            data=json.dumps({
                "guestId": self.titular.id,
                "attending": True,
            }),
            content_type="application/json",
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.titular.refresh_from_db()
        self.acompanante.refresh_from_db()
        self.grupo.refresh_from_db()

        self.assertIs(
            self.titular.asistira,
            True,
        )
        self.assertIsNone(
            self.acompanante.asistira,
        )

        # Legacy group fields remain only an aggregate summary.
        self.assertEqual(
            self.grupo.cantidad_confirmada,
            1,
        )
        self.assertIsNone(
            self.grupo.asistira,
        )

        payload = response.json()["data"]
        guests = {
            int(guest["id"]): guest
            for guest in payload["guests"]
        }

        self.assertIs(
            guests[self.titular.id]["attending"],
            True,
        )
        self.assertIsNone(
            guests[self.acompanante.id]["attending"],
        )

    def test_rsvp_second_person_does_not_overwrite_first(self):
        url = reverse(
            "builder_public_rsvp_api",
            args=[self.grupo.codigo],
        )

        first = self.client.post(
            url,
            data=json.dumps({
                "guestId": self.titular.id,
                "attending": True,
            }),
            content_type="application/json",
        )
        self.assertEqual(
            first.status_code,
            200,
        )

        second = self.client.post(
            url,
            data=json.dumps({
                "guestId": self.acompanante.id,
                "attending": False,
            }),
            content_type="application/json",
        )
        self.assertEqual(
            second.status_code,
            200,
        )

        self.titular.refresh_from_db()
        self.acompanante.refresh_from_db()

        self.assertIs(
            self.titular.asistira,
            True,
        )
        self.assertIs(
            self.acompanante.asistira,
            False,
        )

    def test_rsvp_rejects_guest_from_another_invitation(self):
        otro_grupo = Grupoinvitacion.objects.create(
            evento=self.evento,
            nombre_grupo="Otra invitación",
            tipo="FAMILIAR",
        )
        externo = Invitado.objects.create(
            grupo=otro_grupo,
            nombre="Persona externa",
            tipo_persona="ADULTO",
        )

        url = reverse(
            "builder_public_rsvp_api",
            args=[self.grupo.codigo],
        )

        response = self.client.post(
            url,
            data=json.dumps({
                "guestId": externo.id,
                "attending": True,
            }),
            content_type="application/json",
        )

        self.assertEqual(
            response.status_code,
            404,
        )

        externo.refresh_from_db()
        self.assertIsNone(
            externo.asistira,
        )

    def test_rsvp_requires_guest_id(self):
        url = reverse(
            "builder_public_rsvp_api",
            args=[self.grupo.codigo],
        )

        response = self.client.post(
            url,
            data=json.dumps({
                "attending": True,
                "confirmedGuests": 2,
                "comment": "Contrato legacy",
            }),
            content_type="application/json",
        )

        self.assertEqual(
            response.status_code,
            400,
        )

        self.titular.refresh_from_db()
        self.acompanante.refresh_from_db()

        self.assertIsNone(
            self.titular.asistira,
        )
        self.assertIsNone(
            self.acompanante.asistira,
        )

    def test_no_published_document_never_falls_back_to_legacy(self):
        self.diseno.documento_builder_publicado = {}
        self.diseno.save(
            update_fields=["documento_builder_publicado"]
        )

        response = self.client.get(
            reverse(
                "ver_invitacion",
                args=[self.grupo.codigo],
            )
        )

        self.assertEqual(
            response.status_code,
            404,
        )
        self.assertTemplateUsed(
            response,
            "invitaciones/builder/not_published.html",
        )
        self.assertNotContains(
            response,
            "invitaciones/ver_invitacion.html",
            status_code=404,
        )
