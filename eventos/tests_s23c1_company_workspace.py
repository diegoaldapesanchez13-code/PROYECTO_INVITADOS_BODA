from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from catalogo.models import ServicioCatalogo
from invitaciones.models import EventoBoda
from organizaciones.models import EmpresaSuscriptora, MembresiaEmpresa
from proveedores.models import Proveedor


class CompanyWorkspaceC1Tests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.empresa = EmpresaSuscriptora.objects.create(
            nombre_comercial="Empresa C1",
            slug="empresa-c1",
        )
        self.otra = EmpresaSuscriptora.objects.create(
            nombre_comercial="Otra C1",
            slug="otra-c1",
        )
        self.admin = User.objects.create_user(
            username="admin-c1",
            password="Pass-C1-2026!",
        )
        MembresiaEmpresa.objects.create(
            empresa=self.empresa,
            usuario=self.admin,
            rol="ADMIN_EMPRESA",
        )
        self.planner = User.objects.create_user(
            username="planner-c1",
            password="Pass-C1-2026!",
        )
        MembresiaEmpresa.objects.create(
            empresa=self.empresa,
            usuario=self.planner,
            rol="WEDDING_PLANNER",
        )

    def test_company_navigation_uses_canonical_workspace_routes(self):
        self.client.force_login(self.admin)
        response = self.client.get(
            reverse("empresa_dashboard", kwargs={"empresa_slug": self.empresa.slug})
        )
        self.assertContains(response, reverse("empresa_clientes", kwargs={"empresa_slug": self.empresa.slug}))
        self.assertContains(response, reverse("empresa_equipo", kwargs={"empresa_slug": self.empresa.slug}))
        self.assertContains(response, reverse("empresa_proveedores", kwargs={"empresa_slug": self.empresa.slug}))
        self.assertContains(response, reverse("empresa_catalogo", kwargs={"empresa_slug": self.empresa.slug}))
        self.assertContains(response, reverse("empresa_configuracion", kwargs={"empresa_slug": self.empresa.slug}))

    def test_clientes_route_is_tenant_scoped(self):
        cliente = get_user_model().objects.create_user(username="cliente-c1", password="Pass-C1-2026!")
        otro_cliente = get_user_model().objects.create_user(username="cliente-otro-c1", password="Pass-C1-2026!")
        MembresiaEmpresa.objects.create(empresa=self.empresa, usuario=cliente, rol="CLIENTE")
        MembresiaEmpresa.objects.create(empresa=self.otra, usuario=otro_cliente, rol="CLIENTE")
        self.client.force_login(self.admin)
        response = self.client.get(reverse("empresa_clientes", kwargs={"empresa_slug": self.empresa.slug}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "cliente-c1")
        self.assertNotContains(response, "cliente-otro-c1")

    def test_planner_cannot_open_company_management_routes(self):
        self.client.force_login(self.planner)
        response = self.client.get(reverse("empresa_equipo", kwargs={"empresa_slug": self.empresa.slug}))
        self.assertEqual(response.status_code, 403)

    def test_client_creation_reuses_membership_runtime(self):
        evento = EventoBoda.objects.create(empresa=self.empresa, nombre_evento="Evento cliente C1")
        self.client.force_login(self.admin)
        response = self.client.post(
            reverse("empresa_clientes", kwargs={"empresa_slug": self.empresa.slug}),
            {
                "accion": "crear_cliente",
                "empresa_id": str(self.empresa.id),
                "username_usuario": "nuevo-cliente-c1",
                "email_usuario": "cliente@example.com",
                "password_usuario": "ClienteC1-123",
                "password_usuario_confirmar": "ClienteC1-123",
                "evento_cliente_id": str(evento.id),
                "activo_usuario": "on",
            },
        )
        self.assertEqual(response.status_code, 302)
        membresia = MembresiaEmpresa.objects.get(
            empresa=self.empresa,
            usuario__username="nuevo-cliente-c1",
            rol="CLIENTE",
        )
        self.assertTrue(evento.clientes.filter(id=membresia.usuario_id).exists())

    def test_provider_creation_preserves_provider_runtime(self):
        self.client.force_login(self.admin)
        response = self.client.post(
            reverse("empresa_proveedores", kwargs={"empresa_slug": self.empresa.slug}),
            {
                "accion": "crear_proveedor",
                "empresa_id": str(self.empresa.id),
                "nombre_proveedor": "Proveedor C1",
                "tipo_proveedor": "DJ",
                "contacto_proveedor": "Contacto",
                "username_usuario": "proveedor-c1",
                "password_usuario": "ProveedorC1-123",
                "password_usuario_confirmar": "ProveedorC1-123",
                "visible_wedding_planners_proveedor": "on",
            },
        )
        self.assertEqual(response.status_code, 302)
        proveedor = Proveedor.objects.get(empresa=self.empresa, nombre_comercial="Proveedor C1")
        self.assertEqual(proveedor.tipo_proveedor, "DJ")
        self.assertTrue(
            MembresiaEmpresa.objects.filter(
                empresa=self.empresa,
                usuario__username="proveedor-c1",
                rol="PROVEEDOR",
            ).exists()
        )

    def test_catalog_canonical_company_route_uses_app_shell(self):
        ServicioCatalogo.objects.create(
            empresa=self.empresa,
            nombre="Servicio Catalogo C1",
            categoria="MUSICA",
            unidad="EVENTO",
        )
        self.client.force_login(self.admin)
        response = self.client.get(reverse("empresa_catalogo", kwargs={"empresa_slug": self.empresa.slug}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Servicio Catalogo C1")
        self.assertContains(response, "app-shell")
        self.assertContains(response, "catalogo.css")

    def test_configuracion_reads_existing_company_state(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse("empresa_configuracion", kwargs={"empresa_slug": self.empresa.slug}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Empresa C1")
        self.assertContains(response, "Datos relacionados")


class CompanyAccessPasswordSmokeTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.empresa = EmpresaSuscriptora.objects.create(
            nombre_comercial="Empresa Passwords",
            slug="empresa-passwords",
        )
        self.admin = User.objects.create_user(
            username="admin-passwords",
            password="admin12345",
        )
        MembresiaEmpresa.objects.create(
            empresa=self.empresa,
            usuario=self.admin,
            rol="ADMIN_EMPRESA",
            activo=True,
            puede_gestionar_catalogos=True,
        )
        self.client.force_login(self.admin)

    def test_cliente_nuevo_recibe_password_definido(self):
        response = self.client.post(
            reverse("empresa_clientes", kwargs={"empresa_slug": self.empresa.slug}),
            {
                "accion": "crear_cliente",
                "username_usuario": "cliente.password",
                "email_usuario": "cliente@example.com",
                "password_usuario": "Cliente123!",
                "password_usuario_confirmar": "Cliente123!",
                "activo_usuario": "on",
            },
        )
        self.assertEqual(response.status_code, 302)
        user = get_user_model().objects.get(username="cliente.password")
        self.assertTrue(user.check_password("Cliente123!"))
        self.assertTrue(
            MembresiaEmpresa.objects.filter(
                empresa=self.empresa,
                usuario=user,
                rol="CLIENTE",
                activo=True,
            ).exists()
        )

    def test_cliente_nuevo_rechaza_password_sin_confirmacion(self):
        self.client.post(
            reverse("empresa_clientes", kwargs={"empresa_slug": self.empresa.slug}),
            {
                "accion": "crear_cliente",
                "username_usuario": "cliente.bad",
                "password_usuario": "Cliente123!",
                "password_usuario_confirmar": "Otro123!",
                "activo_usuario": "on",
            },
        )
        self.assertFalse(
            get_user_model().objects.filter(username="cliente.bad").exists()
        )

    def test_planner_nuevo_recibe_password_definido(self):
        response = self.client.post(
            reverse("empresa_equipo", kwargs={"empresa_slug": self.empresa.slug}),
            {
                "accion": "crear_planner",
                "username_usuario": "planner.password",
                "password_usuario": "Planner123!",
                "password_usuario_confirmar": "Planner123!",
                "rol_usuario": "WEDDING_PLANNER",
                "activo_usuario": "on",
            },
        )
        self.assertEqual(response.status_code, 302)
        user = get_user_model().objects.get(username="planner.password")
        self.assertTrue(user.check_password("Planner123!"))

    def test_proveedor_portal_recibe_password_definido(self):
        response = self.client.post(
            reverse("empresa_proveedores", kwargs={"empresa_slug": self.empresa.slug}),
            {
                "accion": "crear_proveedor",
                "nombre_proveedor": "Proveedor Portal",
                "tipo_proveedor": "DJ",
                "username_usuario": "proveedor.password",
                "email_usuario": "proveedor@example.com",
                "password_usuario": "Proveedor123!",
                "password_usuario_confirmar": "Proveedor123!",
                "visible_wedding_planners_proveedor": "on",
            },
        )
        self.assertEqual(response.status_code, 302)
        proveedor = Proveedor.objects.get(
            empresa=self.empresa,
            nombre_comercial="Proveedor Portal",
        )
        self.assertIsNotNone(proveedor.usuario_id)
        self.assertTrue(proveedor.usuario.check_password("Proveedor123!"))
        self.assertTrue(
            MembresiaEmpresa.objects.filter(
                empresa=self.empresa,
                usuario=proveedor.usuario,
                rol="PROVEEDOR",
            ).exists()
        )
