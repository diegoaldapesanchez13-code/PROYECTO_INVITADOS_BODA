from copy import deepcopy

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from invitaciones.builder.services import BUILDER_BUILD_VERSION
from invitaciones.models import DisenoInvitacion, EventoBoda


def document_fixture():
    return {
        "schemaVersion": 3,
        "page": {"name": "Prueba Django"},
        "sections": [],
        "nodes": [],
    }


class DirtecBuilderDjangoTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_superuser(
            username="builder-admin",
            email="builder@example.com",
            password="password",
        )
        self.client.force_login(self.user)
        now = timezone.now()
        self.evento = EventoBoda.objects.create(
            nombre_evento="DIRTEC Builder",
            novio="Fernando",
            novia="Diego",
            frase_portada="Portada",
            mensaje_general="Mensaje",
            fecha_misa=now,
            lugar_misa="Ceremonia",
            fecha_fiesta=now,
            lugar_fiesta="Recepción",
        )

    def test_editor_oficial_es_dirtec_builder(self):
        response = self.client.get(
            reverse("editor_invitacion_visual", args=[self.evento.id])
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "DIRTEC Studio")
        self.assertContains(response, "dirtec-builder-bootstrap")
        self.assertContains(response, f"?v={BUILDER_BUILD_VERSION}")
        self.assertEqual(
            response.context["builder_bootstrap"]["buildVersion"],
            BUILDER_BUILD_VERSION,
        )

    def test_document_api_guarda_y_recarga(self):
        url = reverse("builder_document_api", args=[self.evento.id])
        response = self.client.post(
            url,
            data={
                "document": document_fixture(),
                "baseRevision": 0,
                "reset": False,
            },
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["revision"], 1)

        loaded = self.client.get(url)
        self.assertEqual(loaded.status_code, 200)
        self.assertEqual(loaded.json()["document"]["schemaVersion"], 3)
        self.assertEqual(loaded.json()["revision"], 1)

    def test_revision_evitar_sobrescritura_silenciosa(self):
        url = reverse("builder_document_api", args=[self.evento.id])
        self.client.post(
            url,
            data={
                "document": document_fixture(),
                "baseRevision": 0,
            },
            content_type="application/json",
        )

        conflict = self.client.post(
            url,
            data={
                "document": document_fixture(),
                "baseRevision": 0,
            },
            content_type="application/json",
        )
        self.assertEqual(conflict.status_code, 409)
        self.assertEqual(conflict.json()["revision"], 1)

    def test_publicar_crea_snapshot_independiente(self):
        save_url = reverse("builder_document_api", args=[self.evento.id])
        publish_url = reverse("builder_publish_api", args=[self.evento.id])

        document = document_fixture()
        self.client.post(
            save_url,
            data={
                "document": document,
                "baseRevision": 0,
            },
            content_type="application/json",
        )

        response = self.client.post(
            publish_url,
            data={"baseRevision": 1},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)

        diseno = DisenoInvitacion.objects.get(evento=self.evento)
        self.assertEqual(diseno.documento_builder_publicado, document)
        self.assertIsNot(
            diseno.documento_builder_publicado,
            diseno.documento_builder_borrador,
        )
        self.assertEqual(diseno.versiones.filter(publicado=True).count(), 1)

    def test_schema_invalido_es_rechazado(self):
        response = self.client.post(
            reverse("builder_document_api", args=[self.evento.id]),
            data={
                "document": {
                    "schemaVersion": 99,
                    "sections": [],
                    "nodes": [],
                },
                "baseRevision": 0,
            },
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
