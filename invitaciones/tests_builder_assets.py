import shutil
import tempfile

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from invitaciones.models import AssetInvitacion, DisenoInvitacion, EventoBoda


class DirtecBuilderAssetTests(TestCase):
    @classmethod
    def setUpClass(cls):
        cls._media_root = tempfile.mkdtemp(prefix="dirtec-builder-assets-")
        cls._override = override_settings(MEDIA_ROOT=cls._media_root)
        cls._override.enable()
        super().setUpClass()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        cls._override.disable()
        shutil.rmtree(cls._media_root, ignore_errors=True)

    def setUp(self):
        self.user = get_user_model().objects.create_superuser(
            username="asset-admin",
            email="asset@example.com",
            password="password",
        )
        self.client.force_login(self.user)

        now = timezone.now()
        self.evento = EventoBoda.objects.create(
            nombre_evento="Assets",
            novio="Fernando",
            novia="Diego",
            frase_portada="Portada",
            mensaje_general="Mensaje",
            fecha_misa=now,
            lugar_misa="Ceremonia",
            fecha_fiesta=now,
            lugar_fiesta="Recepción",
        )

    def test_upload_crea_asset_persistente_y_listable(self):
        url = reverse("builder_assets_api", args=[self.evento.id])
        upload = SimpleUploadedFile(
            "foto.jpg",
            b"contenido-prueba",
            content_type="image/jpeg",
        )

        response = self.client.post(
            url,
            {"archivo": upload},
        )

        self.assertEqual(response.status_code, 201)
        payload = response.json()
        self.assertTrue(payload["ok"])
        self.assertTrue(payload["asset"]["id"].startswith("db-"))
        self.assertTrue(payload["asset"]["url"].startswith("/media/"))
        self.assertFalse(payload["asset"]["url"].startswith("data:"))

        listed = self.client.get(url)
        self.assertEqual(listed.status_code, 200)
        self.assertEqual(len(listed.json()["assets"]), 1)

    def test_delete_borra_asset_no_usado(self):
        asset = AssetInvitacion.objects.create(
            evento=self.evento,
            titulo="Eliminar",
            archivo=SimpleUploadedFile("eliminar.jpg", b"x"),
            creado_por=self.user,
        )

        response = self.client.delete(
            reverse(
                "builder_asset_detail_api",
                args=[self.evento.id, asset.id],
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(
            AssetInvitacion.objects.filter(id=asset.id).exists()
        )

    def test_delete_rechaza_asset_referenciado_por_documento(self):
        asset = AssetInvitacion.objects.create(
            evento=self.evento,
            titulo="Usado",
            archivo=SimpleUploadedFile("usado.jpg", b"x"),
            creado_por=self.user,
        )
        diseno, _ = DisenoInvitacion.objects.get_or_create(
            evento=self.evento
        )
        diseno.documento_builder_borrador = {
            "schemaVersion": 3,
            "sections": [],
            "nodes": [
                {
                    "id": "image-1",
                    "content": {
                        "assetId": f"db-{asset.id}",
                        "src": asset.archivo.url,
                    },
                }
            ],
        }
        diseno.save(update_fields=["documento_builder_borrador"])

        response = self.client.delete(
            reverse(
                "builder_asset_detail_api",
                args=[self.evento.id, asset.id],
            )
        )

        self.assertEqual(response.status_code, 409)
        self.assertTrue(
            AssetInvitacion.objects.filter(id=asset.id).exists()
        )

    def test_editor_bootstrap_incluye_assets_persistentes(self):
        AssetInvitacion.objects.create(
            evento=self.evento,
            titulo="Persistente",
            archivo=SimpleUploadedFile("persistente.jpg", b"x"),
            creado_por=self.user,
        )

        response = self.client.get(
            reverse("editor_invitacion_visual", args=[self.evento.id])
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "initialAssets")
        self.assertContains(response, "Persistente")

    def test_imagenes_no_se_clasifican_por_formato_como_decoracion(self):
        for filename, title in [
            ("alpha.png", "PNG"),
            ("alpha.webp", "WEBP"),
            ("animado.gif", "GIF"),
        ]:
            AssetInvitacion.objects.create(
                evento=self.evento,
                titulo=title,
                archivo=SimpleUploadedFile(filename, b"x"),
                creado_por=self.user,
            )

        response = self.client.get(
            reverse("builder_assets_api", args=[self.evento.id])
        )

        self.assertEqual(response.status_code, 200)
        by_name = {
            asset["name"]: asset
            for asset in response.json()["assets"]
        }

        for title in ["PNG", "WEBP", "GIF"]:
            self.assertEqual(by_name[title]["type"], "IMAGE")
            self.assertNotEqual(by_name[title]["type"], "DECORATION")
            self.assertEqual(by_name[title]["metadata"]["mediaKind"], "IMAGE")
            self.assertTrue(by_name[title]["metadata"]["supportsAlpha"])

        self.assertTrue(by_name["GIF"]["metadata"]["animated"])
        self.assertFalse(by_name["PNG"]["metadata"]["animated"])

    def test_video_conserva_tipo_video_en_assets(self):
        AssetInvitacion.objects.create(
            evento=self.evento,
            titulo="Video",
            archivo=SimpleUploadedFile("clip.mp4", b"x"),
            creado_por=self.user,
        )

        response = self.client.get(
            reverse("builder_assets_api", args=[self.evento.id])
        )

        self.assertEqual(response.status_code, 200)
        asset = response.json()["assets"][0]
        self.assertEqual(asset["type"], "VIDEO")
        self.assertEqual(asset["metadata"]["mediaKind"], "VIDEO")
