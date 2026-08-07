from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import EventoBoda


class BuilderEngineEditorMountTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_superuser(
            username="engine-editor-admin",
            email="engine-editor@example.com",
            password="test-password",
        )
        self.client.force_login(self.user)
        now = timezone.now()
        self.evento = EventoBoda.objects.create(
            nombre_evento="Evento Engine",
            novio="A",
            novia="B",
            frase_portada="Portada",
            mensaje_general="Mensaje",
            fecha_misa=now,
            lugar_misa="Ceremonia",
            fecha_fiesta=now,
            lugar_fiesta="Recepción",
        )

    def test_editor_engine_renderiza_bootstrap_y_respaldo(self):
        response = self.client.get(
            reverse("builder_engine_editor", args=[self.evento.id])
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "DIRTEC Builder Engine")
        self.assertContains(response, "dirtec-builder-bootstrap")
        self.assertContains(
            response,
            reverse("builder_engine_document_load", args=[self.evento.id]),
        )
        self.assertContains(
            response,
            reverse("editor_invitacion_visual", args=[self.evento.id]),
        )
