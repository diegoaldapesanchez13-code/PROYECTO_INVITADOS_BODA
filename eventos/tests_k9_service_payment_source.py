from decimal import Decimal

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.utils import timezone

from invitaciones.models import EventoBoda
from presupuesto.models import CategoriaGasto, GastoEvento, PagoEvento
from proveedores.models import Proveedor, ServicioEvento


class ServicioPaymentSourceK9Tests(TestCase):
    def setUp(self):
        ahora = timezone.now()
        self.evento = EventoBoda.objects.create(
            novio="A",
            novia="B",
            frase_portada="Test",
            mensaje_general="Test",
            fecha_misa=ahora,
            lugar_misa="Templo",
            fecha_fiesta=ahora,
            lugar_fiesta="Salon",
        )
        self.proveedor = Proveedor.objects.create(nombre_comercial="Foto Luz")
        self.servicio = ServicioEvento.objects.create(
            evento=self.evento,
            proveedor=self.proveedor,
            nombre_servicio="Fotografia",
            costo_proveedor=Decimal("15000.00"),
        )
        self.categoria = CategoriaGasto.objects.create(nombre="Fotografia")

    def test_servicio_no_duplica_datos_de_pago(self):
        field_names = {field.name for field in ServicioEvento._meta.get_fields()}
        self.assertNotIn("anticipo", field_names)
        self.assertNotIn("fecha_limite_pago", field_names)
        self.assertNotIn("comprobante_pago", field_names)
        self.assertFalse(hasattr(self.servicio, "saldo_pendiente"))

    def test_pago_y_saldo_viven_en_gasto_evento(self):
        gasto = GastoEvento.objects.create(
            evento=self.evento,
            servicio_evento=self.servicio,
            categoria=self.categoria,
            proveedor=self.proveedor,
            concepto="Fotografia",
            monto_estimado=Decimal("15000.00"),
        )
        pago = PagoEvento.objects.create(
            gasto=gasto,
            monto=Decimal("5000.00"),
            comprobante=SimpleUploadedFile(
                "anticipo.pdf",
                b"%PDF-1.4 test",
                content_type="application/pdf",
            ),
        )

        gasto.refresh_from_db()
        self.servicio.refresh_from_db()
        self.assertEqual(gasto.total_pagado, Decimal("5000.00"))
        self.assertEqual(gasto.saldo_pendiente, Decimal("10000.00"))
        self.assertTrue(pago.comprobante.name.endswith(".pdf"))
        self.assertEqual(self.servicio.costo_proveedor, Decimal("15000.00"))
