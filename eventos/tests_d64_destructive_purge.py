from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.test import TestCase
from django.utils import timezone

from eventos.data_lifecycle import (
    autorizar_purga_historica,
    confirmar_respaldo_externo,
    ejecutar_purga_historica,
    generar_expediente_purge_ready,
)
from eventos.models import ContratoEvento, ExpedienteHistoricoEvento
from invitaciones.models import EventoBoda
from organizaciones.models import EmpresaSuscriptora, MembresiaEmpresa


class D64DestructivePurgeTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.empresa = EmpresaSuscriptora.objects.create(
            nombre_comercial="Empresa D64",
            slug="empresa-d64",
        )
        self.admin = User.objects.create_user(
            username="admin-d64",
            password="test123",
        )
        self.dirtec = User.objects.create_superuser(
            username="dirtec-d64",
            password="test123",
            email="dirtec-d64@example.com",
        )
        MembresiaEmpresa.objects.create(
            empresa=self.empresa,
            usuario=self.admin,
            rol="ADMIN_EMPRESA",
        )
        now = timezone.now()
        self.evento = EventoBoda.objects.create(
            empresa=self.empresa,
            nombre_evento="Evento D64",
            novio="A",
            novia="B",
            frase_portada="D64",
            mensaje_general="D64",
            fecha_misa=now,
            lugar_misa="X",
            fecha_fiesta=now,
            lugar_fiesta="Y",
            estado="ARCHIVADO",
            activo=False,
            estado_previo_archivado="FINALIZADO",
        )
        self.contrato = ContratoEvento.objects.create(
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

    def _prepare_authorized_receipt(self):
        _content, receipt = generar_expediente_purge_ready(
            self.evento,
            user=self.admin,
        )
        confirmar_respaldo_externo(
            self.evento,
            expediente=receipt,
            user=self.admin,
            sha256=receipt.sha256,
        )
        receipt.retencion_hasta = timezone.now() - timedelta(seconds=1)
        receipt.save(update_fields=["retencion_hasta"])
        autorizar_purga_historica(
            self.evento,
            expediente=receipt,
            user=self.dirtec,
            motivo="Purga historica D64 autorizada para prueba.",
        )
        receipt.refresh_from_db()
        return receipt

    def test_purge_ready_archive_contains_destructive_graph_fingerprint(self):
        _content, receipt = generar_expediente_purge_ready(
            self.evento,
            user=self.admin,
        )
        self.assertEqual(
            receipt.formato,
            "K9_D6_PURGE_READY_V3",
        )
        self.assertTrue(
            receipt.manifest["destructive_graph_sha256"]
        )
        self.assertIn(
            "invitaciones.eventoboda",
            receipt.manifest["model_counts"],
        )

    def test_graph_change_after_archive_blocks_execution(self):
        receipt = self._prepare_authorized_receipt()
        self.contrato.monto_base = Decimal("2000.00")
        self.contrato.save(update_fields=["monto_base"])

        with self.assertRaises(ValidationError):
            ejecutar_purga_historica(
                self.evento,
                expediente=receipt,
                user=self.dirtec,
                confirmacion=f"PURGAR HISTORICO {self.evento.id}",
                sha256=receipt.sha256,
            )
        self.assertTrue(
            EventoBoda.objects.filter(pk=self.evento.id).exists()
        )

    def test_wrong_strong_confirmation_blocks_execution(self):
        receipt = self._prepare_authorized_receipt()
        with self.assertRaises(ValidationError):
            ejecutar_purga_historica(
                self.evento,
                expediente=receipt,
                user=self.dirtec,
                confirmacion="PURGAR",
                sha256=receipt.sha256,
            )

    def test_successful_purge_deletes_event_and_keeps_receipt(self):
        receipt = self._prepare_authorized_receipt()
        evento_id = self.evento.id

        ejecutar_purga_historica(
            self.evento,
            expediente=receipt,
            user=self.dirtec,
            confirmacion=f"PURGAR HISTORICO {evento_id}",
            sha256=receipt.sha256,
        )

        self.assertFalse(
            EventoBoda.objects.filter(pk=evento_id).exists()
        )
        receipt.refresh_from_db()
        self.assertIsNone(receipt.evento_id)
        self.assertIsNotNone(receipt.purga_ejecutada_en)
        self.assertEqual(
            receipt.purga_ejecutada_por_id,
            self.dirtec.id,
        )
        self.assertEqual(
            receipt.resultado_purga["evento_id"],
            evento_id,
        )

    def test_successful_purge_removes_archived_binary(self):
        self.contrato.archivo.save(
            "contrato_d64.txt",
            ContentFile(b"contrato d64"),
            save=True,
        )
        storage = self.contrato.archivo.storage
        storage_name = self.contrato.archivo.name
        self.addCleanup(
            lambda: storage.delete(storage_name)
            if storage.exists(storage_name)
            else None
        )

        receipt = self._prepare_authorized_receipt()
        ejecutar_purga_historica(
            self.evento,
            expediente=receipt,
            user=self.dirtec,
            confirmacion=f"PURGAR HISTORICO {self.evento.id}",
            sha256=receipt.sha256,
        )
        self.assertFalse(storage.exists(storage_name))

    def test_v2_receipt_cannot_execute_destructive_purge(self):
        receipt = ExpedienteHistoricoEvento.objects.create(
            empresa=self.empresa,
            evento=self.evento,
            evento_id_snapshot=self.evento.id,
            evento_nombre_snapshot=self.evento.titulo_evento,
            formato="K9_D6_FULL_V2",
            sha256="a" * 64,
            incluye_binarios=True,
            integridad_verificada=True,
            completo_para_purga_historica=True,
            respaldo_externo_confirmado_en=timezone.now(),
            retencion_hasta=timezone.now() - timedelta(days=1),
            purga_historica_autorizada_en=timezone.now(),
            purga_historica_autorizada_por=self.dirtec,
        )
        with self.assertRaises(ValidationError):
            ejecutar_purga_historica(
                self.evento,
                expediente=receipt,
                user=self.dirtec,
                confirmacion=f"PURGAR HISTORICO {self.evento.id}",
                sha256=receipt.sha256,
            )
