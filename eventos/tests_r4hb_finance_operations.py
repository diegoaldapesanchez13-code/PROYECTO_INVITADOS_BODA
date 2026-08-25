from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from eventos.models import ParticipanteEvento
from invitaciones.models import EventoBoda
from organizaciones.models import EmpresaSuscriptora, MembresiaEmpresa
from presupuesto.models import CategoriaGasto, GastoEvento, PagoClienteEvento, PagoEvento


class FinanceOperationsR4HBTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.empresa = EmpresaSuscriptora.objects.create(
            nombre_comercial="Empresa R4HB",
            slug="empresa-r4hb",
        )
        self.otra = EmpresaSuscriptora.objects.create(
            nombre_comercial="Otra R4HB",
            slug="otra-r4hb",
        )
        self.admin = User.objects.create_user(
            username="admin-r4hb",
            password="Pass-R4HB-2026!",
        )
        MembresiaEmpresa.objects.create(
            empresa=self.empresa,
            usuario=self.admin,
            rol="ADMIN_EMPRESA",
        )
        self.ventas = User.objects.create_user(
            username="ventas-r4hb",
            password="Pass-R4HB-2026!",
        )
        MembresiaEmpresa.objects.create(
            empresa=self.empresa,
            usuario=self.ventas,
            rol="VENTAS",
        )
        self.planner = User.objects.create_user(
            username="planner-r4hb",
            password="Pass-R4HB-2026!",
        )
        MembresiaEmpresa.objects.create(
            empresa=self.empresa,
            usuario=self.planner,
            rol="WEDDING_PLANNER",
        )
        self.evento = EventoBoda.objects.create(
            empresa=self.empresa,
            nombre_evento="Evento R4HB",
            wedding_planner=self.planner,
        )
        ParticipanteEvento.objects.update_or_create(
            evento=self.evento,
            usuario=self.planner,
            rol="PLANNER",
            defaults={"activo": True, "puede_ver_finanzas": True},
        )
        self.categoria = CategoriaGasto.objects.create(
            nombre="Operación R4HB",
        )

    def finance_url(self):
        return reverse(
            "k9_evento_finanzas",
            kwargs={
                "empresa_slug": self.empresa.slug,
                "evento_id": self.evento.id,
            },
        )

    def gasto(self, **kwargs):
        data = {
            "evento": self.evento,
            "categoria": self.categoria,
            "concepto": "Gasto R4HB",
            "monto_estimado": Decimal("1000.00"),
            "monto_real": Decimal("0.00"),
            "estado": "PENDIENTE",
        }
        data.update(kwargs)
        return GastoEvento.objects.create(**data)

    def test_admin_sees_finance_operation_controls(self):
        self.client.force_login(self.admin)
        response = self.client.get(self.finance_url())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Nuevo gasto")
        self.assertContains(response, "workspace_finance_r4.js")

    def test_ventas_keeps_read_only_finance_access(self):
        self.client.force_login(self.ventas)
        response = self.client.get(self.finance_url())
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Nuevo gasto")

    def test_admin_can_create_expense(self):
        self.client.force_login(self.admin)
        response = self.client.post(
            reverse(
                "k9_finanzas_gasto_crear",
                kwargs={
                    "empresa_slug": self.empresa.slug,
                    "evento_id": self.evento.id,
                },
            ),
            {
                "categoria": self.categoria.id,
                "concepto": "Audio adicional",
                "monto_estimado": "2500.00",
                "monto_real": "0",
                "fecha_limite": (timezone.localdate() + timedelta(days=5)).isoformat(),
                "notas": "Prueba R4HB",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            GastoEvento.objects.filter(
                evento=self.evento,
                concepto="Audio adicional",
            ).exists()
        )

    def test_ventas_cannot_create_expense(self):
        self.client.force_login(self.ventas)
        response = self.client.post(
            reverse(
                "k9_finanzas_gasto_crear",
                kwargs={
                    "empresa_slug": self.empresa.slug,
                    "evento_id": self.evento.id,
                },
            ),
            {
                "categoria": self.categoria.id,
                "concepto": "No permitido",
                "monto_estimado": "100.00",
                "monto_real": "0",
            },
        )
        self.assertEqual(response.status_code, 403)

    def test_edit_expense_rejects_target_below_active_payments(self):
        gasto = self.gasto(monto_estimado=Decimal("1000.00"))
        PagoEvento.objects.create(
            gasto=gasto,
            monto=Decimal("700.00"),
            estado="ACTIVO",
        )
        self.client.force_login(self.admin)
        response = self.client.post(
            reverse(
                "k9_finanzas_gasto_editar",
                kwargs={
                    "empresa_slug": self.empresa.slug,
                    "evento_id": self.evento.id,
                    "gasto_id": gasto.id,
                },
            ),
            {
                "categoria": self.categoria.id,
                "concepto": gasto.concepto,
                "monto_estimado": "500.00",
                "monto_real": "0",
            },
        )
        self.assertEqual(response.status_code, 302)
        gasto.refresh_from_db()
        self.assertEqual(gasto.monto_estimado, Decimal("1000.00"))

    def test_register_partial_payment_updates_expense_state(self):
        gasto = self.gasto(monto_estimado=Decimal("1000.00"))
        self.client.force_login(self.admin)
        response = self.client.post(
            reverse(
                "k9_finanzas_pago_registrar",
                kwargs={
                    "empresa_slug": self.empresa.slug,
                    "evento_id": self.evento.id,
                    "gasto_id": gasto.id,
                },
            ),
            {
                "monto": "400.00",
                "fecha_pago": timezone.localdate().isoformat(),
                "metodo_pago": "TRANSFERENCIA",
                "referencia": "R4HB-001",
            },
        )
        self.assertEqual(response.status_code, 302)
        gasto.refresh_from_db()
        self.assertEqual(gasto.estado, "PARCIAL")
        self.assertEqual(gasto.total_pagado, Decimal("400.00"))

    def test_register_full_payment_marks_paid(self):
        gasto = self.gasto(monto_estimado=Decimal("1000.00"))
        self.client.force_login(self.admin)
        self.client.post(
            reverse(
                "k9_finanzas_pago_registrar",
                kwargs={
                    "empresa_slug": self.empresa.slug,
                    "evento_id": self.evento.id,
                    "gasto_id": gasto.id,
                },
            ),
            {
                "monto": "1000.00",
                "fecha_pago": timezone.localdate().isoformat(),
                "metodo_pago": "EFECTIVO",
            },
        )
        gasto.refresh_from_db()
        self.assertEqual(gasto.estado, "PAGADO")

    def test_payment_cannot_exceed_pending_balance(self):
        gasto = self.gasto(monto_estimado=Decimal("1000.00"))
        self.client.force_login(self.admin)
        response = self.client.post(
            reverse(
                "k9_finanzas_pago_registrar",
                kwargs={
                    "empresa_slug": self.empresa.slug,
                    "evento_id": self.evento.id,
                    "gasto_id": gasto.id,
                },
            ),
            {
                "monto": "1000.01",
                "fecha_pago": timezone.localdate().isoformat(),
                "metodo_pago": "TRANSFERENCIA",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertFalse(PagoEvento.objects.filter(gasto=gasto).exists())

    def test_annul_payment_keeps_history_and_recalculates_expense(self):
        gasto = self.gasto(monto_estimado=Decimal("1000.00"), estado="PARCIAL")
        pago = PagoEvento.objects.create(
            gasto=gasto,
            monto=Decimal("300.00"),
            estado="ACTIVO",
        )
        self.client.force_login(self.admin)
        response = self.client.post(
            reverse(
                "k9_finanzas_pago_anular",
                kwargs={
                    "empresa_slug": self.empresa.slug,
                    "evento_id": self.evento.id,
                    "pago_id": pago.id,
                },
            ),
            {"motivo": "Captura duplicada"},
        )
        self.assertEqual(response.status_code, 302)
        pago.refresh_from_db()
        gasto.refresh_from_db()
        self.assertEqual(pago.estado, "ANULADO")
        self.assertEqual(gasto.estado, "PENDIENTE")
        self.assertEqual(gasto.total_pagado, 0)

    def test_cancel_expense_with_active_payment_is_rejected(self):
        gasto = self.gasto()
        PagoEvento.objects.create(
            gasto=gasto,
            monto=Decimal("100.00"),
            estado="ACTIVO",
        )
        self.client.force_login(self.admin)
        response = self.client.post(
            reverse(
                "k9_finanzas_gasto_cancelar",
                kwargs={
                    "empresa_slug": self.empresa.slug,
                    "evento_id": self.evento.id,
                    "gasto_id": gasto.id,
                },
            ),
            {"motivo": "Ya no se requiere"},
        )
        self.assertEqual(response.status_code, 302)
        gasto.refresh_from_db()
        self.assertNotEqual(gasto.estado, "CANCELADO")

    def test_cancel_expense_without_payments_succeeds(self):
        gasto = self.gasto()
        self.client.force_login(self.admin)
        self.client.post(
            reverse(
                "k9_finanzas_gasto_cancelar",
                kwargs={
                    "empresa_slug": self.empresa.slug,
                    "evento_id": self.evento.id,
                    "gasto_id": gasto.id,
                },
            ),
            {"motivo": "Servicio descartado"},
        )
        gasto.refresh_from_db()
        self.assertEqual(gasto.estado, "CANCELADO")
        self.assertIsNotNone(gasto.cancelado_en)

    def test_archive_and_restore_expense_preserve_record(self):
        gasto = self.gasto()
        self.client.force_login(self.admin)
        self.client.post(
            reverse(
                "k9_finanzas_gasto_archivar",
                kwargs={
                    "empresa_slug": self.empresa.slug,
                    "evento_id": self.evento.id,
                    "gasto_id": gasto.id,
                },
            ),
            {"motivo": "Cerrar expediente"},
        )
        gasto.refresh_from_db()
        self.assertIsNotNone(gasto.archivado_en)

        self.client.post(
            reverse(
                "k9_finanzas_gasto_restaurar",
                kwargs={
                    "empresa_slug": self.empresa.slug,
                    "evento_id": self.evento.id,
                    "gasto_id": gasto.id,
                },
            ),
        )
        gasto.refresh_from_db()
        self.assertIsNone(gasto.archivado_en)

    def test_review_client_payment_as_received(self):
        User = get_user_model()
        cliente = User.objects.create_user(
            username="cliente-r4hb",
            password="Pass-R4HB-2026!",
        )
        self.evento.clientes.add(cliente)
        pago = PagoClienteEvento.objects.create(
            evento=self.evento,
            registrado_por=cliente,
            concepto="Anticipo",
            monto=Decimal("1500.00"),
            fecha_pago=timezone.localdate(),
            metodo_pago="TRANSFERENCIA",
            comprobante=SimpleUploadedFile(
                "comprobante.pdf",
                b"%PDF-1.4 test",
                content_type="application/pdf",
            ),
        )

        self.client.force_login(self.admin)
        response = self.client.post(
            reverse(
                "k9_finanzas_pago_cliente_revisar",
                kwargs={
                    "empresa_slug": self.empresa.slug,
                    "evento_id": self.evento.id,
                    "pago_id": pago.id,
                },
            ),
            {
                "estado": "RECIBIDO",
                "comentario_equipo": "Validado",
            },
        )
        self.assertEqual(response.status_code, 302)
        pago.refresh_from_db()
        self.assertEqual(pago.estado, "RECIBIDO")
        self.assertEqual(pago.revisado_por, self.admin)

    def test_cross_event_expense_route_returns_404(self):
        otro_evento = EventoBoda.objects.create(
            empresa=self.empresa,
            nombre_evento="Otro Evento R4HB",
        )
        gasto = GastoEvento.objects.create(
            evento=otro_evento,
            categoria=self.categoria,
            concepto="Otro gasto",
            monto_estimado=Decimal("100.00"),
        )
        self.client.force_login(self.admin)
        response = self.client.post(
            reverse(
                "k9_finanzas_gasto_cancelar",
                kwargs={
                    "empresa_slug": self.empresa.slug,
                    "evento_id": self.evento.id,
                    "gasto_id": gasto.id,
                },
            ),
            {"motivo": "No debe cruzar"},
        )
        self.assertEqual(response.status_code, 404)
