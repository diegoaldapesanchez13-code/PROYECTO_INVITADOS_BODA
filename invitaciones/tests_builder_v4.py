from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from invitaciones.models import DisenoInvitacion, EventoBoda


def v4_document():
    return {
        "schemaVersion": 4,
        "page": {"id": "page", "name": "V4", "type": "PAGE", "settings": {}},
        "canvases": [{
            "id": "canvas-1",
            "type": "CANVAS",
            "name": "Portada",
            "canvasId": "canvas-1",
            "parentId": None,
            "order": 0,
        }],
        "nodes": [],
        "assets": [],
        "responsive": {
            "baseDevice": "mobile",
            "inheritance": {"tablet": "mobile", "desktop": "tablet"},
        },
        "meta": {},
    }


class BuilderV4DjangoTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_superuser(
            username="v4-admin",
            email="v4@example.com",
            password="password",
        )
        self.client.force_login(self.user)
        now = timezone.now()
        self.evento = EventoBoda.objects.create(
            nombre_evento="V4",
            novio="Diego",
            novia="Fernanda",
            frase_portada="Portada",
            mensaje_general="Mensaje",
            fecha_misa=now,
            lugar_misa="Ceremonia",
            fecha_fiesta=now,
            lugar_fiesta="Recepción",
        )

    def test_api_persists_v4(self):
        self.client.get(reverse("editor_invitacion_visual", args=[self.evento.id]))
        response = self.client.post(
            reverse("builder_document_api", args=[self.evento.id]),
            data={"document": v4_document(), "baseRevision": 0, "reset": False},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        d = DisenoInvitacion.objects.get(evento=self.evento)
        self.assertEqual(d.documento_builder_borrador["schemaVersion"], 4)
        self.assertIn("canvases", d.documento_builder_borrador)

    def test_editor_announces_v4_contract(self):
        response = self.client.get(
            reverse("editor_invitacion_visual", args=[self.evento.id])
        )
        self.assertContains(response, '"schemaVersion": 4')
