from datetime import time, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from colaboracion.models import CotizacionServicio
from documentos.models import DocumentoEvento
from invitaciones.models import EventoBoda
from itinerario.models import ActividadItinerario, ParticipanteActividad
from organizaciones.models import EmpresaSuscriptora, MembresiaEmpresa
from presupuesto.models import CategoriaGasto, GastoEvento, PagoClienteEvento, PagoEvento
from proveedores.models import Proveedor, ServicioEvento
from tareas.models import TareaEvento


class ProviderPortalV3Tests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.empresa = EmpresaSuscriptora.objects.create(
            nombre_comercial="Empresa Provider V3",
            slug="empresa-provider-v3",
        )
        self.planner = User.objects.create_user(username="planner-provider-v3", password="test123")
        self.cliente = User.objects.create_user(username="cliente-provider-v3", password="test123")
        self.provider_user = User.objects.create_user(username="provider-v3", password="test123")
        self.other_provider_user = User.objects.create_user(username="other-provider-v3", password="test123")
        for user, rol in [
            (self.planner, "WEDDING_PLANNER"),
            (self.cliente, "CLIENTE"),
            (self.provider_user, "PROVEEDOR"),
            (self.other_provider_user, "PROVEEDOR"),
        ]:
            MembresiaEmpresa.objects.create(empresa=self.empresa, usuario=user, rol=rol)

        now = timezone.now()
        self.evento = EventoBoda.objects.create(
            empresa=self.empresa,
            wedding_planner=self.planner,
            nombre_evento="Boda Provider V3",
            novio="A", novia="B", frase_portada="Test", mensaje_general="Test",
            fecha_misa=now + timedelta(days=20), lugar_misa="Ceremonia",
            fecha_fiesta=now + timedelta(days=20), lugar_fiesta="Recepción",
        )
        self.evento.clientes.add(self.cliente)
        self.proveedor = Proveedor.objects.create(
            empresa=self.empresa,
            usuario=self.provider_user,
            nombre_comercial="Banquetes Provider V3",
            tipo_proveedor="BANQUETE",
        )
        self.other_provider = Proveedor.objects.create(
            empresa=self.empresa,
            usuario=self.other_provider_user,
            nombre_comercial="DJ Provider V3",
            tipo_proveedor="DJ",
        )
        self.servicio = ServicioEvento.objects.create(
            evento=self.evento,
            proveedor=self.proveedor,
            nombre_servicio="Banquete Provider V3",
            origen="MANUAL",
            costo_proveedor=Decimal("15000"),
            valor_contratado=Decimal("30000"),
            cargo_adicional_cliente=Decimal("5000"),
        )
        self.other_service = ServicioEvento.objects.create(
            evento=self.evento,
            proveedor=self.other_provider,
            nombre_servicio="DJ privado",
            origen="MANUAL",
        )
        self.client.force_login(self.provider_user)

    def test_portal_reemplaza_flujo_legacy(self):
        response = self.client.get(reverse("portal_proveedor"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Lo que necesitas hacer")
        self.assertContains(response, "Mis servicios")
        self.assertContains(response, "Cotizaciones")
        self.assertNotContains(response, "Respuesta operativa")
        self.assertNotContains(response, "Solicitudes y propuestas")
        self.assertNotContains(response, "Nueva solicitud")

    def test_proveedor_no_ve_precio_cliente_ni_pago_cliente_empresa(self):
        PagoClienteEvento.objects.create(
            evento=self.evento,
            registrado_por=self.cliente,
            concepto="Pago cliente secreto",
            monto=Decimal("98765.43"),
            comprobante="presupuesto/pagos_cliente_evento/test.jpg",
        )
        response = self.client.get(reverse("portal_proveedor"))
        self.assertNotContains(response, "98765.43")
        self.assertNotContains(response, "Pago cliente secreto")
        self.assertNotContains(response, "5000.00")  # cargo_adicional_cliente
        self.assertNotContains(response, "30000.00")  # valor_contratado

    def test_documentos_requieren_visibilidad_proveedor(self):
        DocumentoEvento.objects.create(
            evento=self.evento,
            servicio_evento=self.servicio,
            proveedor=self.proveedor,
            titulo="Documento interno",
            tipo_documento="OTRO",
            archivo="documentos/eventos/interno.pdf",
            visible_proveedor=False,
            cargado_por=self.planner,
        )
        DocumentoEvento.objects.create(
            evento=self.evento,
            servicio_evento=self.servicio,
            proveedor=self.proveedor,
            titulo="Documento compartido",
            tipo_documento="OTRO",
            archivo="documentos/eventos/compartido.pdf",
            visible_proveedor=True,
            cargado_por=self.planner,
        )
        response = self.client.get(reverse("portal_proveedor"))
        self.assertContains(response, "Documento compartido")
        self.assertNotContains(response, "Documento interno")

    def test_tareas_y_citas_solo_propias(self):
        TareaEvento.objects.create(
            evento=self.evento,
            servicio_evento=self.servicio,
            titulo="Enviar ficha técnica",
            responsable=self.provider_user,
            fecha_limite=timezone.localdate() + timedelta(days=2),
        )
        TareaEvento.objects.create(
            evento=self.evento,
            servicio_evento=self.servicio,
            titulo="Tarea interna Planner",
            responsable=self.planner,
            fecha_limite=timezone.localdate() + timedelta(days=2),
        )
        cita = ActividadItinerario.objects.create(
            evento=self.evento,
            servicio_evento=self.servicio,
            proveedor=self.proveedor,
            tipo="CITA",
            titulo="Prueba montaje proveedor",
            fecha=timezone.localdate() + timedelta(days=3),
            hora_inicio=time(10, 0),
        )
        ParticipanteActividad.objects.create(
            actividad=cita,
            proveedor=self.proveedor,
            rol="PROVEEDOR",
            estado="PENDIENTE",
        )
        response = self.client.get(reverse("portal_proveedor"))
        self.assertContains(response, "Enviar ficha técnica")
        self.assertNotContains(response, "Tarea interna Planner")
        self.assertContains(response, "Prueba montaje proveedor")
        self.assertContains(response, "Confirmar cita")

    def test_proveedor_envia_nueva_version_cotizacion(self):
        CotizacionServicio.objects.create(
            servicio_evento=self.servicio,
            version=1,
            costo_proveedor=Decimal("12000"),
            estado="CAMBIOS_SOLICITADOS",
            respuesta_planner="Ajustar alcance",
            creado_por=self.provider_user,
        )
        response = self.client.post(
            reverse("colaboracion_k85_cotizacion_crear", args=[self.servicio.id]),
            {
                "costo_proveedor": "12500.00",
                "descripcion": "Versión ajustada",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("portal_proveedor"), response.url)
        nueva = CotizacionServicio.objects.get(version=2)
        self.assertEqual(nueva.costo_proveedor, Decimal("12500.00"))
        self.assertEqual(nueva.estado, "ENVIADA")

    def test_proveedor_sube_documento_a_su_servicio(self):
        upload = SimpleUploadedFile(
            "ficha.pdf",
            b"%PDF-1.4 test",
            content_type="application/pdf",
        )
        response = self.client.post(
            reverse("subir_documento_proveedor"),
            {
                "servicio_evento_id": self.servicio.id,
                "tipo_documento": "OTRO",
                "titulo": "Ficha proveedor",
                "archivo": upload,
            },
        )
        self.assertEqual(response.status_code, 302)
        doc = DocumentoEvento.objects.get(titulo="Ficha proveedor")
        self.assertEqual(doc.servicio_evento, self.servicio)
        self.assertEqual(doc.proveedor, self.proveedor)
        self.assertTrue(doc.visible_proveedor)
        self.assertFalse(doc.visible_cliente)

    def test_proveedor_no_puede_subir_documento_a_servicio_ajeno(self):
        upload = SimpleUploadedFile("x.pdf", b"%PDF-1.4", content_type="application/pdf")
        response = self.client.post(
            reverse("subir_documento_proveedor"),
            {
                "servicio_evento_id": self.other_service.id,
                "titulo": "No permitido",
                "archivo": upload,
            },
        )
        self.assertEqual(response.status_code, 404)

    def test_pagos_muestran_solo_egresos_empresa_hacia_este_proveedor(self):
        categoria = CategoriaGasto.objects.create(nombre="Proveedor V3")
        gasto = GastoEvento.objects.create(
            evento=self.evento,
            servicio_evento=self.servicio,
            categoria=categoria,
            proveedor=self.proveedor,
            concepto="Pago banquete",
            monto_real=Decimal("15000"),
        )
        PagoEvento.objects.create(
            gasto=gasto,
            monto=Decimal("5000"),
            referencia="PAGO-PROPIO",
        )
        gasto_otro = GastoEvento.objects.create(
            evento=self.evento,
            servicio_evento=self.other_service,
            categoria=categoria,
            proveedor=self.other_provider,
            concepto="Pago DJ secreto",
            monto_real=Decimal("99999"),
        )
        PagoEvento.objects.create(
            gasto=gasto_otro,
            monto=Decimal("77777"),
            referencia="PAGO-AJENO",
        )

        response = self.client.get(reverse("portal_proveedor"))
        self.assertContains(response, "PAGO-PROPIO")
        self.assertNotContains(response, "PAGO-AJENO")
        self.assertNotContains(response, "77777")
