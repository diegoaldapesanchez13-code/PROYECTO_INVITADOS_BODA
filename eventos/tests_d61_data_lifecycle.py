import io
import json
import zipfile
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from eventos.event_domain import evaluar_purga_evento
from eventos.models import ContratoEvento, ExpedienteHistoricoEvento
from invitaciones.models import EventoBoda
from organizaciones.models import EmpresaSuscriptora, MembresiaEmpresa
from paquetes.models import PaqueteBoda, PropuestaEvento


class D61DataLifecycleTests(TestCase):
    def setUp(self):
        User=get_user_model()
        self.empresa=EmpresaSuscriptora.objects.create(nombre_comercial="Empresa D6",slug="empresa-d6")
        self.admin=User.objects.create_user(username="admin-d6",password="test123")
        MembresiaEmpresa.objects.create(empresa=self.empresa,usuario=self.admin,rol="ADMIN_EMPRESA")
        now=timezone.now()
        self.evento=EventoBoda.objects.create(
            empresa=self.empresa,nombre_evento="Evento D6",novio="A",novia="B",
            frase_portada="D6",mensaje_general="D6",fecha_misa=now,lugar_misa="X",
            fecha_fiesta=now,lugar_fiesta="Y",estado="ARCHIVADO",activo=False,
            estado_previo_archivado="CANCELADO",
        )
        self.client.force_login(self.admin)

    def test_archived_discardable_event_is_purge_eligible(self):
        self.assertTrue(evaluar_purga_evento(self.evento).permitido)

    def test_draft_proposal_does_not_block_discardable_purge(self):
        paquete=PaqueteBoda.objects.create(empresa=self.empresa,nombre="Paquete D6",precio_base=Decimal("1000.00"))
        PropuestaEvento.objects.create(
            empresa=self.empresa,evento=self.evento,paquete=paquete,estado="BORRADOR"
        )
        self.assertTrue(evaluar_purga_evento(self.evento).permitido)

    def test_real_contract_blocks_purge(self):
        ContratoEvento.objects.create(
            evento=self.evento,version=1,estado="CANCELADO",
            monto_base=Decimal("1000.00"),snapshot_version=2,
            snapshot_comercial={"version":2,"totales":{"total_final":"1000.00"}},
        )
        evaluacion=evaluar_purga_evento(self.evento)
        self.assertFalse(evaluacion.permitido)
        self.assertIn("Tiene un contrato.", evaluacion.motivos)

    def test_structured_export_creates_download_and_receipt(self):
        response=self.client.get(reverse(
            "k9_evento_exportar_expediente",
            kwargs={"empresa_slug":self.empresa.slug,"evento_id":self.evento.id},
        ))
        self.assertEqual(response.status_code,200)
        self.assertEqual(response["Content-Type"],"application/zip")
        receipt=ExpedienteHistoricoEvento.objects.get(evento_id_snapshot=self.evento.id)
        self.assertTrue(receipt.incluye_binarios)
        self.assertTrue(receipt.integridad_verificada)
        self.assertTrue(receipt.completo_para_purga_historica)
        self.assertEqual(receipt.binarios_faltantes, 0)
        self.assertEqual(response["X-DIRTEC-Archive-SHA256"],receipt.sha256)

        archive=zipfile.ZipFile(io.BytesIO(response.content))
        self.assertIn("manifest.json",archive.namelist())
        self.assertIn("data.json",archive.namelist())
        self.assertIn("file_inventory.json",archive.namelist())
        manifest=json.loads(archive.read("manifest.json"))
        self.assertEqual(manifest["formato"], "K9_D6_FULL_V2")
        self.assertTrue(receipt.manifest["integridad_verificada"])
        self.assertTrue(receipt.manifest["completo_para_purga_historica"])

    def test_export_receipt_survives_purge_of_discardable_event(self):
        self.client.get(reverse(
            "k9_evento_exportar_expediente",
            kwargs={"empresa_slug":self.empresa.slug,"evento_id":self.evento.id},
        ))
        evento_id=self.evento.id
        response=self.client.post(reverse(
            "k9_evento_purgar",
            kwargs={"empresa_slug":self.empresa.slug,"evento_id":evento_id},
        ),{"confirmacion":"PURGAR"})
        self.assertEqual(response.status_code,302)
        self.assertFalse(EventoBoda.objects.filter(pk=evento_id).exists())
        receipt=ExpedienteHistoricoEvento.objects.get(evento_id_snapshot=evento_id)
        self.assertIsNone(receipt.evento_id)

    def test_export_does_not_unlock_real_historical_purge(self):
        ContratoEvento.objects.create(
            evento=self.evento,version=1,estado="CANCELADO",
            monto_base=Decimal("1000.00"),snapshot_version=2,
            snapshot_comercial={"version":2,"totales":{"total_final":"1000.00"}},
        )
        self.client.get(reverse(
            "k9_evento_exportar_expediente",
            kwargs={"empresa_slug":self.empresa.slug,"evento_id":self.evento.id},
        ))
        self.client.post(reverse(
            "k9_evento_purgar",
            kwargs={"empresa_slug":self.empresa.slug,"evento_id":self.evento.id},
        ),{"confirmacion":"PURGAR"})
        self.assertTrue(EventoBoda.objects.filter(pk=self.evento.id).exists())
