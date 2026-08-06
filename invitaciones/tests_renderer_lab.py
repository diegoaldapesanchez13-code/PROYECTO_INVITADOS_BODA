from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from .models import EventoBoda

class RendererLabViewTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_superuser(
            username="renderer-lab-admin", email="renderer-lab@example.com", password="test-password"
        )
        self.client.force_login(self.user)
        now = timezone.now()
        self.evento = EventoBoda.objects.create(
            nombre_evento="Renderer Lab", novio="Fernando", novia="Diego",
            frase_portada="Portada", mensaje_general="Mensaje",
            fecha_misa=now, lugar_misa="Ceremonia",
            fecha_fiesta=now, lugar_fiesta="Recepción",
        )

    def test_renderer_lab_renderiza_tres_modos(self):
        response = self.client.get(reverse("builder_engine_renderer_lab", args=[self.evento.id]))
        self.assertEqual(response.status_code, 200)
        for value in ("Universal Renderer", "EDIT", "PREVIEW", "PUBLIC", "dirtec-renderer-lab-bootstrap"):
            self.assertContains(response, value)

    def test_renderer_lab_incluye_solo_endpoint_de_carga(self):
        response = self.client.get(reverse("builder_engine_renderer_lab", args=[self.evento.id]))
        self.assertContains(response, reverse("builder_engine_document_load", args=[self.evento.id]))
        self.assertNotContains(response, '"save"')
        self.assertNotContains(response, '"publish"')
