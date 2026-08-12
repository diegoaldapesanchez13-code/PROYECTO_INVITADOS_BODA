from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.test import RequestFactory, TestCase

from core.services.authorization import (
    Actions,
    usuario_puede_evento,
    usuario_tiene_permiso,
)
from core.services.tenant_context import (
    resolver_tenant_usuario,
    tenant_desde_request,
)
from invitaciones.models import EventoBoda
from organizaciones.models import EmpresaSuscriptora, MembresiaEmpresa


class TenantContextKTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.empresa_a = EmpresaSuscriptora.objects.create(
            nombre_comercial="Empresa A",
            slug="empresa-a",
        )
        self.empresa_b = EmpresaSuscriptora.objects.create(
            nombre_comercial="Empresa B",
            slug="empresa-b",
        )
        self.admin = User.objects.create_user(
            username="admin_a",
            password="test123",
        )
        MembresiaEmpresa.objects.create(
            empresa=self.empresa_a,
            usuario=self.admin,
            rol="ADMIN_EMPRESA",
        )
        self.planner = User.objects.create_user(
            username="planner_a",
            password="test123",
        )
        MembresiaEmpresa.objects.create(
            empresa=self.empresa_a,
            usuario=self.planner,
            rol="WEDDING_PLANNER",
        )
        self.dirtec = User.objects.create_superuser(
            username="dirtec_k",
            password="test123",
        )
        self.evento = EventoBoda.objects.create(
            empresa=self.empresa_a,
            wedding_planner=self.planner,
            novio="A",
            novia="B",
            frase_portada="Test",
            mensaje_general="Test",
            fecha_misa="2030-01-01T12:00:00Z",
            lugar_misa="Ceremonia",
            fecha_fiesta="2030-01-01T18:00:00Z",
            lugar_fiesta="Recepción",
        )

    def test_non_dirtec_ignores_requested_company(self):
        request = RequestFactory().get(
            "/dashboard/",
            {"empresa": self.empresa_b.id},
        )
        request.user = self.admin
        context = tenant_desde_request(request)
        self.assertEqual(context.empresa, self.empresa_a)
        self.assertFalse(context.puede_cambiar_empresa)

    def test_dirtec_can_switch_company(self):
        context = resolver_tenant_usuario(
            self.dirtec,
            requested_company_id=self.empresa_b.id,
        )
        self.assertTrue(context.es_dirtec)
        self.assertEqual(context.empresa, self.empresa_b)

    def test_ambiguous_tenant_fails_closed(self):
        MembresiaEmpresa.objects.create(
            empresa=self.empresa_b,
            usuario=self.admin,
            rol="ADMIN_EMPRESA",
        )
        with self.assertRaises(PermissionDenied):
            resolver_tenant_usuario(self.admin)

    def test_company_admin_matrix(self):
        self.assertTrue(
            usuario_tiene_permiso(
                self.admin,
                Actions.COMPANY_MANAGE_USERS,
                empresa=self.empresa_a,
            )
        )
        self.assertTrue(
            usuario_tiene_permiso(
                self.admin,
                Actions.EVENT_BUILDER,
                empresa=self.empresa_a,
            )
        )

    def test_planner_scope_is_event_assignment(self):
        self.assertTrue(
            usuario_puede_evento(
                self.planner,
                self.evento,
                Actions.EVENT_EDIT,
            )
        )
        other = get_user_model().objects.create_user(
            username="planner_other",
            password="test123",
        )
        MembresiaEmpresa.objects.create(
            empresa=self.empresa_a,
            usuario=other,
            rol="WEDDING_PLANNER",
        )
        self.assertFalse(
            usuario_puede_evento(
                other,
                self.evento,
                Actions.EVENT_EDIT,
            )
        )


class DjangoAdminDirtecKTests(TestCase):
    def setUp(self):
        User = get_user_model()
        empresa = EmpresaSuscriptora.objects.create(
            nombre_comercial="Empresa Staff",
            slug="empresa-staff",
        )
        self.company_staff = User.objects.create_user(
            username="company_staff",
            password="test123",
            is_staff=True,
        )
        MembresiaEmpresa.objects.create(
            empresa=empresa,
            usuario=self.company_staff,
            rol="ADMIN_EMPRESA",
        )
        self.dirtec = User.objects.create_superuser(
            username="dirtec_staff",
            password="test123",
        )

    def test_company_staff_cannot_open_django_admin(self):
        self.client.force_login(self.company_staff)
        response = self.client.get("/admin/")
        self.assertNotEqual(response.status_code, 200)

    def test_dirtec_can_open_django_admin(self):
        self.client.force_login(self.dirtec)
        response = self.client.get("/admin/")
        self.assertEqual(response.status_code, 200)
