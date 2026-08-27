from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.test import TestCase
from django.utils import timezone

from eventos.data_lifecycle import (
    RETENTION_DAYS_HISTORICAL,
    autorizar_purga_historica,
    confirmar_respaldo_externo,
    evaluar_ciclo_datos_evento,
    generar_expediente_estructurado,
)
from eventos.event_domain import evaluar_purga_evento
from eventos.models import ContratoEvento
from invitaciones.models import EventoBoda
from organizaciones.models import EmpresaSuscriptora, MembresiaEmpresa


class D63RetentionAuthorizationTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.empresa = EmpresaSuscriptora.objects.create(
            nombre_comercial="Empresa D63",
            slug="empresa-d63",
        )
        self.admin = User.objects.create_user(
            username="admin-d63",
            password="test123",
        )
        self.dirtec = User.objects.create_superuser(
            username="dirtec-d63",
            password="test123",
            email="dirtec-d63@example.com",
        )
        MembresiaEmpresa.objects.create(
            empresa=self.empresa,
            usuario=self.admin,
            rol="ADMIN_EMPRESA",
        )
        now = timezone.now()
        self.evento = EventoBoda.objects.create(
            empresa=self.empresa,
            nombre_evento="Evento D63",
            novio="A",
            novia="B",
            frase_portada="D63",
            mensaje_general="D63",
            fecha_misa=now,
            lugar_misa="X",
            fecha_fiesta=now,
            lugar_fiesta="Y",
            estado="ARCHIVADO",
            activo=False,
            estado_previo_archivado="FINALIZADO",
        )
        ContratoEvento.objects.create(
            evento=self.evento,
            version=1,
            estado="CANCELADO",
            monto_base=Decimal("1000.00"),
            snapshot_version=2,
            snapshot_comercial={
                "version": 2,
                "totales": {"total_final": "1000.00"},
            },
        )
        _content, self.receipt = generar_expediente_estructurado(
            self.evento,
            user=self.admin,
        )

    def test_wrong_hash_does_not_confirm_external_custody(self):
        with self.assertRaises(ValidationError):
            confirmar_respaldo_externo(
                self.evento,
                expediente=self.receipt,
                user=self.admin,
                sha256="0" * 64,
            )
        self.receipt.refresh_from_db()
        self.assertIsNone(self.receipt.respaldo_externo_confirmado_en)

    def test_confirmation_starts_30_day_retention(self):
        before = timezone.now()
        confirmar_respaldo_externo(
            self.evento,
            expediente=self.receipt,
            user=self.admin,
            sha256=self.receipt.sha256,
        )
        self.receipt.refresh_from_db()
        self.assertIsNotNone(self.receipt.respaldo_externo_confirmado_en)
        self.assertEqual(
            self.receipt.respaldo_externo_confirmado_por_id,
            self.admin.id,
        )
        expected = before + timedelta(days=RETENTION_DAYS_HISTORICAL)
        self.assertLess(
            abs((self.receipt.retencion_hasta - expected).total_seconds()),
            5,
        )

    def test_company_admin_cannot_authorize_historical_purge(self):
        confirmar_respaldo_externo(
            self.evento,
            expediente=self.receipt,
            user=self.admin,
            sha256=self.receipt.sha256,
        )
        self.receipt.retencion_hasta = timezone.now() - timedelta(seconds=1)
        self.receipt.save(update_fields=["retencion_hasta"])
        with self.assertRaises(PermissionDenied):
            autorizar_purga_historica(
                self.evento,
                expediente=self.receipt,
                user=self.admin,
                motivo="Autorizacion historica de prueba.",
            )

    def test_dirtec_cannot_authorize_before_retention(self):
        confirmar_respaldo_externo(
            self.evento,
            expediente=self.receipt,
            user=self.admin,
            sha256=self.receipt.sha256,
        )
        with self.assertRaises(ValidationError):
            autorizar_purga_historica(
                self.evento,
                expediente=self.receipt,
                user=self.dirtec,
                motivo="Autorizacion historica de prueba.",
            )

    def test_dirtec_can_authorize_after_retention(self):
        confirmar_respaldo_externo(
            self.evento,
            expediente=self.receipt,
            user=self.admin,
            sha256=self.receipt.sha256,
        )
        self.receipt.retencion_hasta = timezone.now() - timedelta(seconds=1)
        self.receipt.save(update_fields=["retencion_hasta"])
        autorizar_purga_historica(
            self.evento,
            expediente=self.receipt,
            user=self.dirtec,
            motivo="Autorizacion historica de prueba.",
        )
        self.receipt.refresh_from_db()
        self.assertEqual(
            self.receipt.purga_historica_autorizada_por_id,
            self.dirtec.id,
        )
        state = evaluar_ciclo_datos_evento(self.evento)
        self.assertTrue(state["purga_historica_autorizada"])
        self.assertFalse(state["purga_historica_permitida"])

    def test_authorization_does_not_weaken_existing_historical_purge_guard(self):
        confirmar_respaldo_externo(
            self.evento,
            expediente=self.receipt,
            user=self.admin,
            sha256=self.receipt.sha256,
        )
        self.receipt.retencion_hasta = timezone.now() - timedelta(seconds=1)
        self.receipt.save(update_fields=["retencion_hasta"])
        autorizar_purga_historica(
            self.evento,
            expediente=self.receipt,
            user=self.dirtec,
            motivo="Autorizacion historica de prueba.",
        )
        self.assertFalse(evaluar_purga_evento(self.evento).permitido)
