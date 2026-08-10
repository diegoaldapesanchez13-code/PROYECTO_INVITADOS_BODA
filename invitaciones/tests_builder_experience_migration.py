import shutil
import tempfile

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from invitaciones.builder.experience_migration import importar_experience_legacy
from invitaciones.models import AssetInvitacion, DisenoInvitacion, EventoBoda


def v4_document(experience=None):
    document = {
        "schemaVersion": 4,
        "page": {"id": "page", "name": "V4", "type": "PAGE", "settings": {}},
        "canvases": [],
        "nodes": [],
        "assets": [],
        "responsive": {
            "baseDevice": "mobile",
            "inheritance": {"tablet": "mobile", "desktop": "tablet"},
        },
        "meta": {},
    }
    if experience is not None:
        document["experience"] = experience
    return document


class BuilderExperienceMigrationTests(TestCase):
    @classmethod
    def setUpClass(cls):
        cls._media_root = tempfile.mkdtemp(prefix="dirtec-builder-experience-")
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
            username="experience-admin",
            email="experience@example.com",
            password="password",
        )
        self.client.force_login(self.user)
        now = timezone.now()
        self.evento = EventoBoda.objects.create(
            nombre_evento="Experience",
            novio="Fernando",
            novia="Diego",
            frase_portada="Portada",
            mensaje_general="Mensaje",
            fecha_misa=now,
            lugar_misa="Ceremonia",
            fecha_fiesta=now,
            lugar_fiesta="Recepcion",
            paleta_sobre="SALVIA_PERLA",
            monograma_sobre="F&D",
            texto_boton_sobre="Entrar",
        )

    def test_importa_legacy_envelope_y_audio_idempotente(self):
        self.evento.sello_sobre = SimpleUploadedFile(
            "sello.png",
            b"seal",
            content_type="image/png",
        )
        self.evento.cancion = SimpleUploadedFile(
            "cancion.mp3",
            b"audio",
            content_type="audio/mpeg",
        )
        self.evento.save(update_fields=["sello_sobre", "cancion"])
        diseno = DisenoInvitacion.objects.create(
            evento=self.evento,
            documento_builder_borrador=v4_document(),
        )

        result = importar_experience_legacy(diseno, usuario=self.user)

        self.assertTrue(result["applied"])
        self.assertEqual(result["assetsCreated"], 2)
        diseno.refresh_from_db()
        experience = diseno.documento_builder_borrador["experience"]
        self.assertEqual(experience["intro"]["mode"], "ENVELOPE")
        self.assertEqual(experience["intro"]["openLabel"], "Entrar")
        self.assertEqual(experience["intro"]["envelope"]["palette"], "SALVIA_PERLA")
        self.assertEqual(experience["intro"]["envelope"]["monogram"], "F&D")
        self.assertTrue(experience["intro"]["envelope"]["sealAssetId"].startswith("db-"))
        self.assertTrue(experience["audio"]["enabled"])
        self.assertTrue(experience["audio"]["assetId"].startswith("db-"))
        self.assertEqual(
            AssetInvitacion.objects.filter(evento=self.evento).count(),
            2,
        )
        self.assertTrue(
            AssetInvitacion.objects.filter(evento=self.evento, tipo="AUDIO").exists()
        )

        second = importar_experience_legacy(diseno, usuario=self.user)

        diseno.refresh_from_db()
        self.assertFalse(second["applied"])
        self.assertEqual(
            AssetInvitacion.objects.filter(evento=self.evento).count(),
            2,
        )
        self.assertEqual(diseno.builder_revision, 1)

    def test_no_sobrescribe_experience_configurado(self):
        self.evento.sello_sobre = SimpleUploadedFile(
            "sello.png",
            b"seal",
            content_type="image/png",
        )
        self.evento.save(update_fields=["sello_sobre"])
        configured = {
            "intro": {
                "enabled": True,
                "mode": "IMAGE",
                "assetId": "db-existing",
                "envelope": {},
            },
            "audio": {
                "enabled": False,
                "assetId": None,
            },
        }
        diseno = DisenoInvitacion.objects.create(
            evento=self.evento,
            documento_builder_borrador=v4_document(configured),
        )

        result = importar_experience_legacy(diseno, usuario=self.user)

        diseno.refresh_from_db()
        self.assertFalse(result["applied"])
        self.assertEqual(
            diseno.documento_builder_borrador["experience"],
            configured,
        )
        self.assertEqual(
            AssetInvitacion.objects.filter(evento=self.evento).count(),
            0,
        )

    def test_editor_bootstrap_aplica_import_legacy(self):
        self.evento.cancion = SimpleUploadedFile(
            "cancion.mp3",
            b"audio",
            content_type="audio/mpeg",
        )
        self.evento.save(update_fields=["cancion"])
        DisenoInvitacion.objects.create(
            evento=self.evento,
            documento_builder_borrador=v4_document(),
        )

        response = self.client.get(
            reverse("editor_invitacion_visual", args=[self.evento.id])
        )

        self.assertEqual(response.status_code, 200)
        diseno = DisenoInvitacion.objects.get(evento=self.evento)
        audio = diseno.documento_builder_borrador["experience"]["audio"]
        self.assertTrue(audio["enabled"])
        self.assertEqual(
            AssetInvitacion.objects.filter(evento=self.evento, tipo="AUDIO").count(),
            1,
        )
