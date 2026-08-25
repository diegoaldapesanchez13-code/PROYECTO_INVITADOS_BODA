from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from documentos.models import DocumentoEvento
from invitaciones.models import EventoBoda
from organizaciones.models import (
    EmpresaSuscriptora,
    MembresiaEmpresa,
)
from proveedores.models import Proveedor, ServicioEvento


class ProviderPortalK7Tests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.empresa = EmpresaSuscriptora.objects.create(
            nombre_comercial="Casa Provider K7",
            slug="casa-provider-k7",
        )
        self.user = User.objects.create_user(
            username="provider_k7",
            password="test123",
        )
        MembresiaEmpresa.objects.create(
            empresa=self.empresa,
            usuario=self.user,
            rol="PROVEEDOR",
        )
        self.proveedor = Proveedor.objects.create(
            empresa=self.empresa,
            usuario=self.user,
            nombre_comercial="Foto K7",
            tipo_proveedor="FOTOGRAFIA",
        )
        self.evento = EventoBoda.objects.create(
            empresa=self.empresa,
            novio="A",
            novia="B",
            frase_portada="Test",
            mensaje_general="Test",
            fecha_misa=timezone.now() + timedelta(days=20),
            lugar_misa="Ceremonia",
            fecha_fiesta=timezone.now() + timedelta(days=20),
            lugar_fiesta="Salon",
        )
        self.servicio = ServicioEvento.objects.create(
            evento=self.evento,
            proveedor=self.proveedor,
            nombre_servicio="Fotografia completa",
            fecha_servicio=timezone.localdate() + timedelta(days=20),
            costo_proveedor=15000,
        )
        self.client.force_login(self.user)

    def test_provider_gets_dedicated_workspace(self):
        response = self.client.get(
            reverse("proveedor_dashboard")
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Portal Proveedor")
        self.assertContains(response, "Agenda")
        self.assertContains(response, "Mis servicios")
        self.assertContains(response, "Documentos")

    def test_provider_upload_never_self_publishes_to_client(self):
        upload = SimpleUploadedFile(
            "cotizacion.pdf",
            b"%PDF-1.4 test",
            content_type="application/pdf",
        )
        response = self.client.post(
            reverse("subir_documento_proveedor"),
            {
                "servicio_evento_id": self.servicio.id,
                "tipo_documento": "COTIZACION",
                "titulo": "Cotizacion proveedor",
                "visible_cliente": "on",
                "archivo": upload,
            },
        )
        self.assertEqual(response.status_code, 302)

        doc = DocumentoEvento.objects.get(
            titulo="Cotizacion proveedor"
        )
        self.assertEqual(doc.proveedor, self.proveedor)
        self.assertFalse(doc.visible_cliente)

    def test_provider_cannot_see_other_provider_documents(self):
        other = Proveedor.objects.create(
            empresa=self.empresa,
            nombre_comercial="Decoracion K7",
            tipo_proveedor="DECORACION",
        )
        DocumentoEvento.objects.create(
            evento=self.evento,
            proveedor=other,
            titulo="Documento privado otro proveedor",
            tipo_documento="OTRO",
            archivo="documentos/eventos/otro.pdf",
            visible_proveedor=True,
        )
        DocumentoEvento.objects.create(
            evento=self.evento,
            servicio_evento=self.servicio,
            proveedor=self.proveedor,
            titulo="Documento propio",
            tipo_documento="OTRO",
            archivo="documentos/eventos/propio.pdf",
            visible_proveedor=True,
        )
        DocumentoEvento.objects.create(
            evento=self.evento,
            servicio_evento=self.servicio,
            proveedor=self.proveedor,
            titulo="Documento interno no compartido",
            tipo_documento="OTRO",
            archivo="documentos/eventos/interno.pdf",
            visible_proveedor=False,
        )

        response = self.client.get(
            reverse("proveedor_dashboard")
        )
        self.assertContains(response, "Documento propio")
        self.assertNotContains(response, "Documento interno no compartido")
        self.assertNotContains(
            response,
            "Documento privado otro proveedor",
        )
