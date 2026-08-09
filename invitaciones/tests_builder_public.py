from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from invitaciones.models import DisenoInvitacion, EventoBoda, Grupoinvitacion


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
        self.grupo = Grupoinvitacion.objects.create(evento=self.evento, nombre_grupo="Familia Test", tipo="PERSONAL", cantidad_maxima=2, cantidad_extra_permitida=1)
        self.document = {"schemaVersion": 3, "page": {"name": "Public"}, "sections": [{"id":"section-1","type":"SECTION","name":"Portada","parentId":None,"order":0,"visible":True,"locked":False,"x":50,"y":50,"width":100,"height":800,"minHeight":800,"rotation":0,"scale":1,"opacity":1,"zIndex":1,"coordinateSpace":"CANVAS","layoutMode":"FLOW","style":{},"content":{},"responsive":{}}], "nodes": []}
        self.diseno = DisenoInvitacion.objects.create(evento=self.evento, documento_builder_borrador=self.document, documento_builder_publicado=self.document, estado="PUBLICADO")

    def test_public_route_uses_v3_template(self):
        response = self.client.get(reverse("ver_invitacion", args=[self.grupo.codigo]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "invitaciones/builder/public_invitation.html")
        self.assertContains(response, "dirtec-builder-public-bootstrap")

    def test_public_route_does_not_expose_draft_to_guest(self):
        self.diseno.documento_builder_borrador = {**self.document, "page": {"name": "SECRET-DRAFT"}}
        self.diseno.save(update_fields=["documento_builder_borrador"])
        response = self.client.get(reverse("ver_invitacion", args=[self.grupo.codigo]) + "?preview=1")
        self.assertNotContains(response, "SECRET-DRAFT")

    def test_rsvp_get_and_post(self):
        url = reverse("builder_public_rsvp_api", args=[self.grupo.codigo])
        self.assertEqual(self.client.get(url).status_code, 200)
        response = self.client.post(url, data='{"attending":true,"confirmedGuests":2,"comment":"Nos vemos"}', content_type="application/json")
        self.assertEqual(response.status_code, 200)
        self.grupo.refresh_from_db()
        self.assertTrue(self.grupo.asistira)
        self.assertEqual(self.grupo.cantidad_confirmada, 2)
        self.assertEqual(self.grupo.comentario, "Nos vemos")

    def test_no_published_document_never_falls_back_to_legacy(self):
        self.diseno.documento_builder_publicado = {}
        self.diseno.save(update_fields=["documento_builder_publicado"])
        response = self.client.get(reverse("ver_invitacion", args=[self.grupo.codigo]))
        self.assertEqual(response.status_code, 404)
        self.assertTemplateUsed(
            response,
            "invitaciones/builder/not_published.html",
        )
        self.assertNotContains(
            response,
            "invitaciones/ver_invitacion.html",
            status_code=404,
        )
