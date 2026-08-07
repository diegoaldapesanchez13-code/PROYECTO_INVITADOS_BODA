from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import AssetInvitacion, EventoBoda


class BuilderAssetsApiTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_superuser(
            username="asset-admin",
            email="asset@example.com",
            password="test-password",
        )
        self.client.force_login(self.user)
        now = timezone.now()
        self.evento = EventoBoda.objects.create(
            nombre_evento="Evento Assets",
            novio="A",
            novia="B",
            frase_portada="Portada",
            mensaje_general="Mensaje",
            fecha_misa=now,
            lugar_misa="Ceremonia",
            fecha_fiesta=now,
            lugar_fiesta="Recepción",
        )
        self.asset = AssetInvitacion.objects.create(
            evento=self.evento,
            titulo="Imagen de prueba",
            tipo="DECORACION",
            archivo=SimpleUploadedFile(
                "prueba.png",
                b"\x89PNG\r\n\x1a\n",
                content_type="image/png",
            ),
            creado_por=self.user,
        )

    def test_lista_assets_normalizados(self):
        response = self.client.get(
            reverse("builder_engine_assets_list", args=[self.evento.id])
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["ok"])
        self.assertEqual(len(payload["assets"]), 1)
        self.assertEqual(payload["assets"][0]["type"], "IMAGE")
        self.assertEqual(payload["assets"][0]["backendId"], self.asset.id)
