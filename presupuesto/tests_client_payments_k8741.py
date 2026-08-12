from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from invitaciones.models import EventoBoda
from organizaciones.models import EmpresaSuscriptora, MembresiaEmpresa
from proveedores.models import Proveedor, ServicioEvento
from .models import PagoClienteEvento, PagoEvento


class ClientPaymentsK8741Tests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.empresa = EmpresaSuscriptora.objects.create(nombre_comercial="Empresa Pagos", slug="empresa-pagos")
        self.cliente = User.objects.create_user(username="cliente-pagos", password="test123")
        self.planner = User.objects.create_user(username="planner-pagos", password="test123")
        self.proveedor_user = User.objects.create_user(username="proveedor-pagos", password="test123")
        for user, rol in [(self.cliente,"CLIENTE"),(self.planner,"WEDDING_PLANNER"),(self.proveedor_user,"PROVEEDOR")]:
            MembresiaEmpresa.objects.create(empresa=self.empresa, usuario=user, rol=rol)
        now = timezone.now()
        self.evento = EventoBoda.objects.create(
            empresa=self.empresa, wedding_planner=self.planner, nombre_evento="Boda pagos",
            novio="A", novia="B", frase_portada="Test", mensaje_general="Test",
            fecha_misa=now+timedelta(days=20), lugar_misa="Ceremonia",
            fecha_fiesta=now+timedelta(days=20), lugar_fiesta="Recepción",
        )
        self.evento.clientes.add(self.cliente)
        self.proveedor = Proveedor.objects.create(
            empresa=self.empresa, usuario=self.proveedor_user,
            nombre_comercial="Proveedor", tipo_proveedor="BANQUETE",
        )
        self.servicio = ServicioEvento.objects.create(
            evento=self.evento, proveedor=self.proveedor, nombre_servicio="Banquete", origen="MANUAL",
        )

    def _archivo(self):
        return SimpleUploadedFile("comprobante.jpg", b"fake-image", content_type="image/jpeg")

    def test_cliente_reporta_pago_a_empresa(self):
        self.client.force_login(self.cliente)
        response = self.client.post(
            reverse("pago_cliente_evento_registrar", args=[self.evento.id]),
            {"concepto":"Anticipo","servicio_evento_id":self.servicio.id,"monto":"5000",
             "fecha_pago":timezone.localdate().isoformat(),"metodo_pago":"TRANSFERENCIA",
             "referencia":"ABC123","comprobante":self._archivo()},
        )
        self.assertEqual(response.status_code, 302)
        pago = PagoClienteEvento.objects.get()
        self.assertEqual(pago.evento, self.evento)
        self.assertEqual(pago.servicio_evento, self.servicio)
        self.assertEqual(pago.estado, "PENDIENTE")
        self.assertEqual(pago.registrado_por, self.cliente)
        self.assertEqual(PagoEvento.objects.count(), 0)

    def test_planner_puede_marcar_recibido(self):
        pago = PagoClienteEvento.objects.create(
            evento=self.evento, registrado_por=self.cliente, monto=Decimal("5000"),
            comprobante="presupuesto/pagos_cliente_evento/test.jpg",
        )
        self.client.force_login(self.planner)
        response = self.client.post(
            reverse("pago_cliente_evento_revisar", args=[pago.id]),
            {"estado":"RECIBIDO","comentario_equipo":"Pago recibido"},
        )
        self.assertEqual(response.status_code, 302)
        pago.refresh_from_db()
        self.assertEqual(pago.estado, "RECIBIDO")
        self.assertEqual(pago.revisado_por, self.planner)
        self.assertIsNotNone(pago.fecha_revision)

    def test_proveedor_no_puede_revisar_pago_cliente(self):
        pago = PagoClienteEvento.objects.create(
            evento=self.evento, registrado_por=self.cliente, monto=Decimal("5000"),
            comprobante="presupuesto/pagos_cliente_evento/test.jpg",
        )
        self.client.force_login(self.proveedor_user)
        response = self.client.post(
            reverse("pago_cliente_evento_revisar", args=[pago.id]),
            {"estado":"RECIBIDO"},
        )
        self.assertEqual(response.status_code, 403)
        pago.refresh_from_db()
        self.assertEqual(pago.estado, "PENDIENTE")

    def test_cliente_no_puede_reportar_pago_en_otro_evento(self):
        otro = EventoBoda.objects.create(
            empresa=self.empresa, novio="C", novia="D", frase_portada="x", mensaje_general="x",
            fecha_misa=timezone.now()+timedelta(days=2), lugar_misa="x",
            fecha_fiesta=timezone.now()+timedelta(days=2), lugar_fiesta="x",
        )
        self.client.force_login(self.cliente)
        response = self.client.post(
            reverse("pago_cliente_evento_registrar", args=[otro.id]),
            {"monto":"100","comprobante":self._archivo()},
        )
        self.assertEqual(response.status_code, 403)
