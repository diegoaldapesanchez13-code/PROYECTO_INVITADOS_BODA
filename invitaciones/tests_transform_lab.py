from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import EventoBoda


class TransformLabViewTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_superuser(
            username="transform-lab-admin",
            email="transform@example.com",
            password="test-password",
        )
        self.client.force_login(self.user)

        now = timezone.now()
        self.evento = EventoBoda.objects.create(
            nombre_evento="Transform Lab",
            novio="Fernando",
            novia="Diego",
            frase_portada="Portada",
            mensaje_general="Mensaje",
            fecha_misa=now,
            lugar_misa="Ceremonia",
            fecha_fiesta=now,
            lugar_fiesta="Recepción",
        )

    def test_transform_lab_renderiza_sin_escrituras(self):
        response = self.client.get(
            reverse("builder_engine_transform_lab", args=[self.evento.id])
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Canvas, Selection &amp; Transform")
        self.assertContains(response, "Sin persistencia")
        self.assertContains(response, "dirtec-transform-lab-bootstrap")

    def test_bootstrap_incluye_solo_endpoint_load(self):
        response = self.client.get(
            reverse("builder_engine_transform_lab", args=[self.evento.id])
        )
        self.assertContains(
            response,
            reverse("builder_engine_document_load", args=[self.evento.id]),
        )
