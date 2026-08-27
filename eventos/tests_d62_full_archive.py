import hashlib
import io
import json
import zipfile
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from eventos.models import ContratoEvento, ExpedienteHistoricoEvento
from invitaciones.models import EventoBoda
from organizaciones.models import EmpresaSuscriptora, MembresiaEmpresa


class D62FullArchiveTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.empresa = EmpresaSuscriptora.objects.create(
            nombre_comercial="Empresa D62",
            slug="empresa-d62",
        )
        self.admin = User.objects.create_user(
            username="admin-d62",
            password="test123",
        )
        MembresiaEmpresa.objects.create(
            empresa=self.empresa,
            usuario=self.admin,
            rol="ADMIN_EMPRESA",
        )
        now = timezone.now()
        self.evento = EventoBoda.objects.create(
            empresa=self.empresa,
            nombre_evento="Evento D62",
            novio="A",
            novia="B",
            frase_portada="D62",
            mensaje_general="D62",
            fecha_misa=now,
            lugar_misa="X",
            fecha_fiesta=now,
            lugar_fiesta="Y",
            estado="ARCHIVADO",
            activo=False,
            estado_previo_archivado="FINALIZADO",
        )
        self.client.force_login(self.admin)

    def _url(self):
        return reverse(
            "k9_evento_exportar_expediente",
            kwargs={
                "empresa_slug": self.empresa.slug,
                "evento_id": self.evento.id,
            },
        )

    def test_full_archive_without_binary_references_is_verified(self):
        response = self.client.get(self._url())
        self.assertEqual(response.status_code, 200)
        receipt = ExpedienteHistoricoEvento.objects.get(
            evento_id_snapshot=self.evento.id
        )
        self.assertEqual(receipt.formato, "K9_D6_FULL_V2")
        self.assertTrue(receipt.incluye_binarios)
        self.assertTrue(receipt.integridad_verificada)
        self.assertTrue(receipt.completo_para_purga_historica)
        self.assertEqual(receipt.binarios_faltantes, 0)

    def test_contract_binary_is_embedded_and_hashed(self):
        contrato = ContratoEvento.objects.create(
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
        contrato.archivo.save(
            "contrato_d62.txt",
            ContentFile(b"contrato d62"),
            save=True,
        )
        self.addCleanup(lambda: contrato.archivo.storage.delete(contrato.archivo.name))

        response = self.client.get(self._url())
        self.assertEqual(response.status_code, 200)
        receipt = ExpedienteHistoricoEvento.objects.get(
            evento_id_snapshot=self.evento.id
        )
        self.assertTrue(receipt.integridad_verificada)
        self.assertEqual(receipt.binarios_encontrados, 1)
        self.assertEqual(receipt.binarios_faltantes, 0)

        with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
            inventory = json.loads(archive.read("file_inventory.json"))
            included = [x for x in inventory if x["estado"] == "INCLUIDO"]
            self.assertEqual(len(included), 1)
            item = included[0]
            blob = archive.read(item["archive_path"])
            self.assertEqual(blob, b"contrato d62")
            self.assertEqual(
                hashlib.sha256(blob).hexdigest(),
                item["sha256"],
            )

    def test_complete_archive_still_does_not_unlock_historical_purge(self):
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
        self.client.get(self._url())
        receipt = ExpedienteHistoricoEvento.objects.get(
            evento_id_snapshot=self.evento.id
        )
        self.assertTrue(receipt.integridad_verificada)

        response = self.client.post(
            reverse(
                "k9_evento_purgar",
                kwargs={
                    "empresa_slug": self.empresa.slug,
                    "evento_id": self.evento.id,
                },
            ),
            {"confirmacion": "PURGAR"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(EventoBoda.objects.filter(pk=self.evento.id).exists())
