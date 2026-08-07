import json

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import DisenoInvitacion, EventoBoda, VersionDisenoInvitacion


class BuilderEnginePersistenceApiTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_superuser(
            username="builder-admin",
            email="builder@example.com",
            password="test-password",
        )
        self.client.force_login(self.user)

        ahora = timezone.now()
        self.evento = EventoBoda.objects.create(
            nombre_evento="Evento Builder",
            novio="Persona A",
            novia="Persona B",
            frase_portada="Bienvenidos",
            mensaje_general="Mensaje",
            fecha_misa=ahora,
            lugar_misa="Ceremonia",
            fecha_fiesta=ahora,
            lugar_fiesta="Recepción",
        )

    def documento(self, nombre="Documento"):
        return {
            "schemaVersion": 1,
            "documentVersion": 1,
            "builderVersion": "0.14.0",
            "metadata": {
                "eventId": self.evento.id,
                "name": nombre,
                "status": "draft",
            },
            "theme": {},
            "assets": [],
            "globals": {},
            "canvases": [],
        }

    def test_load_crea_documento_schema_1(self):
        response = self.client.get(
            reverse(
                "builder_engine_document_load",
                args=[self.evento.id],
            )
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["document"]["schemaVersion"], 1)
        self.assertEqual(
            payload["document"]["metadata"]["eventId"],
            self.evento.id,
        )

    def test_save_guarda_configuracion_borrador(self):
        response = self.client.post(
            reverse(
                "builder_engine_document_save",
                args=[self.evento.id],
            ),
            data=json.dumps({
                "document": self.documento("Guardado"),
                "reason": "manual",
            }),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        diseno = DisenoInvitacion.objects.get(evento=self.evento)
        self.assertEqual(
            diseno.configuracion_borrador["metadata"]["name"],
            "Guardado",
        )
        self.assertEqual(diseno.estado, "BORRADOR")

    def test_save_rechaza_base64(self):
        documento = self.documento()
        documento["assets"] = [{
            "id": "imagen",
            "url": "data:image/png;base64,AAA",
        }]

        response = self.client.post(
            reverse(
                "builder_engine_document_save",
                args=[self.evento.id],
            ),
            data=json.dumps({"document": documento}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("Base64", json.dumps(response.json()))

    def test_publish_copia_documento_y_crea_version(self):
        response = self.client.post(
            reverse(
                "builder_engine_document_publish",
                args=[self.evento.id],
            ),
            data=json.dumps({
                "document": self.documento("Publicado"),
            }),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        diseno = DisenoInvitacion.objects.get(evento=self.evento)
        self.assertEqual(diseno.estado, "PUBLICADO")
        self.assertEqual(
            diseno.configuracion_publicada["metadata"]["status"],
            "published",
        )
        self.assertEqual(
            VersionDisenoInvitacion.objects.filter(
                diseno=diseno,
                publicado=True,
            ).count(),
            1,
        )
