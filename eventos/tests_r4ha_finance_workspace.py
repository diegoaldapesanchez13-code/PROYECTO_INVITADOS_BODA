from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from eventos.models import ParticipanteEvento
from invitaciones.models import EventoBoda
from organizaciones.models import EmpresaSuscriptora, MembresiaEmpresa
from presupuesto.models import CategoriaGasto, GastoEvento, PagoEvento


class FinanceWorkspaceR4HATests(TestCase):
    def setUp(self):
        User = get_user_model()

        self.empresa = EmpresaSuscriptora.objects.create(
            nombre_comercial="Empresa R4HA",
            slug="empresa-r4ha",
        )
        self.otra = EmpresaSuscriptora.objects.create(
            nombre_comercial="Otra R4HA",
            slug="otra-r4ha",
        )

        self.admin = User.objects.create_user(
            username="admin-r4ha",
            password="Pass-R4HA-2026!",
        )
        MembresiaEmpresa.objects.create(
            empresa=self.empresa,
            usuario=self.admin,
            rol="ADMIN_EMPRESA",
        )

        self.planner = User.objects.create_user(
            username="planner-r4ha",
            password="Pass-R4HA-2026!",
        )
        MembresiaEmpresa.objects.create(
            empresa=self.empresa,
            usuario=self.planner,
            rol="WEDDING_PLANNER",
        )

        self.evento = EventoBoda.objects.create(
            empresa=self.empresa,
            nombre_evento="Evento R4HA",
            wedding_planner=self.planner,
        )

        ParticipanteEvento.objects.update_or_create(
            evento=self.evento,
            usuario=self.planner,
            rol="PLANNER",
            defaults={
                "activo": True,
                "puede_ver_finanzas": True,
            },
        )

        self.categoria = CategoriaGasto.objects.create(
            nombre="Operación R4HA",
        )

    def url(self):
        return reverse(
            "k9_evento_finanzas",
            kwargs={
                "empresa_slug": self.empresa.slug,
                "evento_id": self.evento.id,
            },
        )

    def gasto(self, **kwargs):
        defaults = {
            "evento": self.evento,
            "categoria": self.categoria,
            "concepto": "Gasto R4HA",
            "monto_estimado": Decimal("1000.00"),
            "monto_real": Decimal("0.00"),
            "estado": "PENDIENTE",
        }
        defaults.update(kwargs)
        return GastoEvento.objects.create(**defaults)

    def test_finance_tab_is_enabled(self):
        self.client.force_login(self.admin)
        response = self.client.get(
            reverse(
                "k9_evento_resumen",
                kwargs={
                    "empresa_slug": self.empresa.slug,
                    "evento_id": self.evento.id,
                },
            )
        )
        tab = next(
            item
            for item in response.context["workspace_navigation"]["tabs"]
            if item["key"] == "finanzas"
        )
        self.assertTrue(tab["enabled"])
        self.assertEqual(tab["url"], self.url())

    def test_admin_can_open_finance_workspace(self):
        self.client.force_login(self.admin)
        response = self.client.get(self.url())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Finanzas")
        self.assertContains(response, "workspace_finance_r4.css")
        self.assertContains(response, "Total contratado")

    def test_planner_with_finance_permission_can_open(self):
        self.client.force_login(self.planner)
        response = self.client.get(self.url())
        self.assertEqual(response.status_code, 200)

    def test_planner_without_finance_permission_is_denied(self):
        ParticipanteEvento.objects.filter(
            evento=self.evento,
            usuario=self.planner,
            rol="PLANNER",
        ).update(puede_ver_finanzas=False)

        self.client.force_login(self.planner)
        response = self.client.get(self.url())
        self.assertEqual(response.status_code, 403)

    def test_other_tenant_cannot_open_finances(self):
        outsider = get_user_model().objects.create_user(
            username="outsider-r4ha",
            password="Pass-R4HA-2026!",
        )
        MembresiaEmpresa.objects.create(
            empresa=self.otra,
            usuario=outsider,
            rol="ADMIN_EMPRESA",
        )
        self.client.force_login(outsider)
        response = self.client.get(self.url())
        self.assertEqual(response.status_code, 404)

    def test_operational_cost_summary_uses_existing_finance_service(self):
        gasto = self.gasto(
            monto_estimado=Decimal("1500.00"),
            monto_real=Decimal("1800.00"),
        )
        PagoEvento.objects.create(
            gasto=gasto,
            monto=Decimal("600.00"),
            estado="ACTIVO",
        )

        self.client.force_login(self.admin)
        response = self.client.get(self.url())
        resumen = response.context["resumen"]

        self.assertEqual(
            resumen["costo_comprometido"],
            Decimal("1800.00"),
        )
        self.assertEqual(
            resumen["pagos_operativos_realizados"],
            Decimal("600.00"),
        )
        self.assertEqual(
            resumen["saldo_operativo"],
            Decimal("1200.00"),
        )

    def test_vencido_filter_uses_computed_due_state(self):
        overdue = self.gasto(
            concepto="Gasto vencido R4HA",
            fecha_limite=timezone.localdate() - timedelta(days=2),
        )
        future = self.gasto(
            concepto="Gasto futuro R4HA",
            fecha_limite=timezone.localdate() + timedelta(days=4),
        )

        self.client.force_login(self.admin)
        response = self.client.get(
            self.url(),
            {"estado_gasto": "VENCIDO"},
        )
        ids = {item.id for item in response.context["gastos"]}
        self.assertIn(overdue.id, ids)
        self.assertNotIn(future.id, ids)

    def test_cancelled_expense_is_not_part_of_financial_summary(self):
        self.gasto(
            concepto="Cancelado R4HA",
            monto_estimado=Decimal("9000.00"),
            estado="CANCELADO",
        )
        self.gasto(
            concepto="Activo R4HA",
            monto_estimado=Decimal("500.00"),
        )

        self.client.force_login(self.admin)
        response = self.client.get(self.url())
        self.assertEqual(
            response.context["resumen"]["costo_comprometido"],
            Decimal("500.00"),
        )

    def test_finance_workspace_exposes_r4hb_operations_for_admin(self):
        self.client.force_login(self.admin)
        response = self.client.get(self.url())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Nuevo gasto")
        self.assertContains(response, "Registrar pago operativo")

    def test_finance_navigation_preserves_workspace_context(self):
        self.client.force_login(self.admin)
        response = self.client.get(
            self.url(),
            {"return_to": f"/empresa/{self.empresa.slug}/dashboard/"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context["workspace_navigation"]["active_key"],
            "finanzas",
        )
