from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from documentos.models import DocumentoEvento
from invitaciones.models import EventoBoda
from organizaciones.models import EmpresaSuscriptora, MembresiaEmpresa
from presupuesto.models import CategoriaGasto, GastoEvento, PagoEvento
from proveedores.models import Proveedor, ServicioEvento
from suscripciones.models import PlanSuscripcion, SuscripcionEmpresa


def crear_evento_base(empresa, *, wedding_planner=None, cliente=None, nombre="Evento K91"):
    ahora = timezone.now()
    evento = EventoBoda.objects.create(
        empresa=empresa,
        wedding_planner=wedding_planner,
        nombre_evento=nombre,
        novio="A",
        novia="B",
        frase_portada="Test",
        mensaje_general="Test",
        fecha_misa=ahora + timedelta(days=20),
        lugar_misa="Ceremonia",
        fecha_fiesta=ahora + timedelta(days=20),
        lugar_fiesta="Recepcion",
    )
    if cliente:
        evento.clientes.add(cliente)
    return evento


def crear_suscripcion_suspendida(empresa):
    plan = PlanSuscripcion.objects.create(nombre=f"Plan {empresa.slug}")
    return SuscripcionEmpresa.objects.create(
        empresa=empresa,
        plan=plan,
        fecha_vencimiento=timezone.localdate() + timedelta(days=30),
        estado="SUSPENDIDA",
    )


def archivo_pdf(nombre="archivo.pdf"):
    return SimpleUploadedFile(nombre, b"%PDF-1.4 test", content_type="application/pdf")


@override_settings(MEDIA_ROOT="media/test/k91_security")
class K91SaasMiddlewareTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.empresa = EmpresaSuscriptora.objects.create(nombre_comercial="Empresa K91", slug="empresa-k91")
        crear_suscripcion_suspendida(self.empresa)
        self.planner = User.objects.create_user(username="planner-k91", password="test123")
        self.cliente = User.objects.create_user(username="cliente-k91", password="test123")
        self.proveedor_user = User.objects.create_user(username="proveedor-k91", password="test123")
        for user, rol in [
            (self.planner, "WEDDING_PLANNER"),
            (self.cliente, "CLIENTE"),
            (self.proveedor_user, "PROVEEDOR"),
        ]:
            MembresiaEmpresa.objects.create(empresa=self.empresa, usuario=user, rol=rol)
        self.evento = crear_evento_base(self.empresa, wedding_planner=self.planner, cliente=self.cliente)
        self.proveedor = Proveedor.objects.create(
            empresa=self.empresa,
            usuario=self.proveedor_user,
            nombre_comercial="Proveedor K91",
        )
        self.servicio = ServicioEvento.objects.create(
            evento=self.evento,
            proveedor=self.proveedor,
            nombre_servicio="Decoracion",
        )

    def assert_saas_redirect(self, response):
        self.assertEqual(response.status_code, 302)
        self.assertIn("/suscripcion/estado/", response["Location"])

    def test_saas_bloquea_colaboracion_get_empresa_suspendida(self):
        self.client.force_login(self.planner)
        response = self.client.get(reverse("colaboracion_workspace_servicio", args=[self.servicio.id]))
        self.assert_saas_redirect(response)

    def test_saas_bloquea_colaboracion_post_empresa_suspendida(self):
        self.client.force_login(self.planner)
        response = self.client.post(
            reverse("colaboracion_workspace_crear_tema", args=[self.servicio.id]),
            {"nombre": "Tema bloqueado"},
        )
        self.assert_saas_redirect(response)

    def test_saas_bloquea_presupuesto_get_empresa_suspendida(self):
        self.client.force_login(self.cliente)
        response = self.client.get(reverse("pago_cliente_evento_registrar", args=[self.evento.id]))
        self.assert_saas_redirect(response)

    def test_saas_bloquea_presupuesto_post_empresa_suspendida(self):
        self.client.force_login(self.cliente)
        response = self.client.post(
            reverse("pago_cliente_evento_registrar", args=[self.evento.id]),
            {"monto": "1000", "comprobante": archivo_pdf("comprobante.pdf")},
        )
        self.assert_saas_redirect(response)


@override_settings(MEDIA_ROOT="media/test/k91_secure_files")
class K91SecureFilesTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.empresa = EmpresaSuscriptora.objects.create(nombre_comercial="Empresa Files", slug="empresa-files")
        self.otra_empresa = EmpresaSuscriptora.objects.create(nombre_comercial="Otra Files", slug="otra-files")
        self.cliente = User.objects.create_user(username="cliente-files", password="test123")
        self.proveedor_user = User.objects.create_user(username="proveedor-files", password="test123")
        self.proveedor_mismo_evento_user = User.objects.create_user(username="proveedor-mismo-evento-files", password="test123")
        self.proveedor_otro_user = User.objects.create_user(username="proveedor-otro-files", password="test123")
        self.proveedor_inactivo_user = User.objects.create_user(username="proveedor-inactivo-files", password="test123")
        for user, empresa in [
            (self.cliente, self.empresa),
            (self.proveedor_user, self.empresa),
            (self.proveedor_mismo_evento_user, self.empresa),
            (self.proveedor_otro_user, self.otra_empresa),
            (self.proveedor_inactivo_user, self.empresa),
        ]:
            MembresiaEmpresa.objects.create(empresa=empresa, usuario=user, rol="PROVEEDOR" if user != self.cliente else "CLIENTE")
        self.evento = crear_evento_base(self.empresa, cliente=self.cliente)
        self.otro_evento = crear_evento_base(self.otra_empresa, nombre="Otro evento")
        self.proveedor = Proveedor.objects.create(
            empresa=self.empresa,
            usuario=self.proveedor_user,
            nombre_comercial="Proveedor autorizado",
        )
        self.proveedor_mismo_evento = Proveedor.objects.create(
            empresa=self.empresa,
            usuario=self.proveedor_mismo_evento_user,
            nombre_comercial="Proveedor mismo evento",
        )
        self.proveedor_otro = Proveedor.objects.create(
            empresa=self.otra_empresa,
            usuario=self.proveedor_otro_user,
            nombre_comercial="Proveedor otro tenant",
        )
        self.proveedor_inactivo = Proveedor.objects.create(
            empresa=self.empresa,
            usuario=self.proveedor_inactivo_user,
            nombre_comercial="Proveedor inactivo",
            activo=False,
        )
        self.servicio = ServicioEvento.objects.create(
            evento=self.evento,
            proveedor=self.proveedor,
            nombre_servicio="Foto",
        )
        self.servicio_mismo_evento = ServicioEvento.objects.create(
            evento=self.evento,
            proveedor=self.proveedor_mismo_evento,
            nombre_servicio="Audio",
        )
        self.servicio_otro = ServicioEvento.objects.create(
            evento=self.otro_evento,
            proveedor=self.proveedor_otro,
            nombre_servicio="Video",
        )
        self.categoria = CategoriaGasto.objects.create(nombre="General K91")

    def test_secure_documento_proveedor_inactivo_no_descarga(self):
        servicio = ServicioEvento.objects.create(
            evento=self.evento,
            proveedor=self.proveedor_inactivo,
            nombre_servicio="Audio",
        )
        documento = DocumentoEvento.objects.create(
            evento=self.evento,
            servicio_evento=servicio,
            titulo="Documento inactivo",
            archivo=archivo_pdf("inactivo.pdf"),
            visible_proveedor=True,
        )
        self.client.force_login(self.proveedor_inactivo_user)
        response = self.client.get(reverse("secure_documento_evento", args=[documento.id]))
        self.assertEqual(response.status_code, 403)

    def test_secure_documento_proveedor_otro_tenant_no_descarga(self):
        documento = DocumentoEvento.objects.create(
            evento=self.otro_evento,
            servicio_evento=self.servicio_otro,
            titulo="Documento otro tenant",
            archivo=archivo_pdf("otro.pdf"),
            visible_proveedor=True,
        )
        self.client.force_login(self.proveedor_user)
        response = self.client.get(reverse("secure_documento_evento", args=[documento.id]))
        self.assertEqual(response.status_code, 403)

    def test_secure_proveedor_no_asignado_servicio_no_descarga(self):
        documento = DocumentoEvento.objects.create(
            evento=self.otro_evento,
            servicio_evento=self.servicio_otro,
            proveedor=self.proveedor,
            titulo="Documento servicio ajeno",
            archivo=archivo_pdf("servicio-ajeno.pdf"),
            visible_proveedor=True,
        )
        self.client.force_login(self.proveedor_user)
        response = self.client.get(reverse("secure_documento_evento", args=[documento.id]))
        self.assertEqual(response.status_code, 403)

    def test_secure_proveedor_servicio_a_no_descarga_documento_servicio_b_mismo_evento(self):
        documento = DocumentoEvento.objects.create(
            evento=self.evento,
            servicio_evento=self.servicio_mismo_evento,
            titulo="Documento servicio B",
            archivo=archivo_pdf("servicio-b.pdf"),
            visible_proveedor=True,
        )
        self.client.force_login(self.proveedor_user)
        response = self.client.get(reverse("secure_documento_evento", args=[documento.id]))
        self.assertEqual(response.status_code, 403)

    def test_secure_pago_operativo_no_visible_a_cliente(self):
        gasto = GastoEvento.objects.create(
            evento=self.evento,
            servicio_evento=self.servicio,
            proveedor=self.proveedor,
            categoria=self.categoria,
            concepto="Pago proveedor",
            monto_estimado=Decimal("1000"),
        )
        pago = PagoEvento.objects.create(
            gasto=gasto,
            monto=Decimal("500"),
            comprobante=archivo_pdf("pago-operativo.pdf"),
        )
        self.client.force_login(self.cliente)
        response = self.client.get(reverse("secure_pago_operativo_comprobante", args=[pago.id]))
        self.assertEqual(response.status_code, 403)

    def test_secure_documento_proveedor_correcto_activo_descarga(self):
        documento = DocumentoEvento.objects.create(
            evento=self.evento,
            servicio_evento=self.servicio,
            titulo="Documento autorizado",
            archivo=archivo_pdf("autorizado.pdf"),
            visible_proveedor=True,
        )
        self.client.force_login(self.proveedor_user)
        response = self.client.get(reverse("secure_documento_evento", args=[documento.id]))
        self.assertEqual(response.status_code, 200)


class K91LoginNextTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.empresa_a = EmpresaSuscriptora.objects.create(nombre_comercial="Empresa Login A", slug="login-a")
        self.empresa_b = EmpresaSuscriptora.objects.create(nombre_comercial="Empresa Login B", slug="login-b")
        self.admin_a = User.objects.create_user(username="admin-login-a", password="test123")
        self.admin_b = User.objects.create_user(username="admin-login-b", password="test123")
        self.planner = User.objects.create_user(username="planner-login", password="test123")
        self.cliente = User.objects.create_user(username="cliente-login", password="test123")
        self.proveedor = User.objects.create_user(username="proveedor-login", password="test123")
        self.dirtec = User.objects.create_superuser(username="dirtec-login", password="test123")
        MembresiaEmpresa.objects.create(empresa=self.empresa_a, usuario=self.admin_a, rol="ADMIN_EMPRESA")
        MembresiaEmpresa.objects.create(empresa=self.empresa_b, usuario=self.admin_b, rol="ADMIN_EMPRESA")
        MembresiaEmpresa.objects.create(empresa=self.empresa_a, usuario=self.planner, rol="WEDDING_PLANNER")
        MembresiaEmpresa.objects.create(empresa=self.empresa_a, usuario=self.cliente, rol="CLIENTE")
        MembresiaEmpresa.objects.create(empresa=self.empresa_a, usuario=self.proveedor, rol="PROVEEDOR")
        self.evento_cliente = crear_evento_base(self.empresa_a, cliente=self.cliente, nombre="Evento cliente")
        self.evento_ajeno = crear_evento_base(self.empresa_a, nombre="Evento ajeno")

    def login(self, username, *, next_url=None):
        url = "/login/"
        if next_url:
            url = f"{url}?next={next_url}"
        return self.client.post(url, {"username": username, "password": "test123"})

    def test_login_descarta_next_privado_de_usuario_anterior(self):
        response = self.login("admin-login-b", next_url="/empresa/login-a/dashboard/")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], "/redirigir/")
        follow = self.client.get(response["Location"])
        self.assertEqual(follow["Location"], "/empresa/login-b/dashboard/")

    def test_login_descarta_next_externo(self):
        response = self.login("admin-login-a", next_url="https://example.invalid/empresa/login-a/dashboard/")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], "/redirigir/")

    def test_login_descarta_next_protocol_relative(self):
        response = self.login("admin-login-a", next_url="//evil.example/empresa/login-a/dashboard/")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], "/redirigir/")

    def test_login_honra_next_solo_si_usuario_autorizado(self):
        response = self.login("admin-login-a", next_url="/empresa/login-a/dashboard/")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], "/empresa/login-a/dashboard/")

    def test_login_descarta_next_cliente_evento_ajeno(self):
        response = self.login("cliente-login", next_url=f"/cliente/dashboard/?evento={self.evento_ajeno.id}")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], "/redirigir/")

    def test_login_honra_next_cliente_evento_propio(self):
        response = self.login("cliente-login", next_url=f"/cliente/dashboard/?evento={self.evento_cliente.id}")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], f"/cliente/dashboard/?evento={self.evento_cliente.id}")

    def test_logout_vuelve_login_neutral(self):
        self.client.force_login(self.admin_a)
        response = self.client.post("/logout/?next=/empresa/login-a/dashboard/")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], "/login/")

    def test_login_empresa_redirige_dashboard_empresa(self):
        response = self.login("admin-login-a")
        follow = self.client.get(response["Location"])
        self.assertEqual(follow["Location"], "/empresa/login-a/dashboard/")

    def test_login_planner_redirige_dashboard_planner(self):
        response = self.login("planner-login")
        follow = self.client.get(response["Location"])
        self.assertEqual(follow["Location"], "/empresa/login-a/planner/dashboard/")

    def test_login_cliente_redirige_dashboard_cliente(self):
        response = self.login("cliente-login")
        follow = self.client.get(response["Location"])
        self.assertEqual(follow["Location"], "/cliente/dashboard/")

    def test_login_proveedor_redirige_dashboard_proveedor(self):
        response = self.login("proveedor-login")
        follow = self.client.get(response["Location"])
        self.assertEqual(follow["Location"], "/proveedor/dashboard/")

    def test_login_dirtec_redirige_dashboard_dirtec(self):
        response = self.login("dirtec-login")
        follow = self.client.get(response["Location"])
        self.assertEqual(follow["Location"], "/dirtec/dashboard/")
