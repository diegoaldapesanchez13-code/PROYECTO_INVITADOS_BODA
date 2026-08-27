from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from eventos.models import ContratoEvento
from eventos.selectors import (
    contrato_es_materializable,
    contrato_es_vigente,
    contrato_vigente,
)
from eventos.services import generar_contrato_v2_desde_propuesta
from eventos.workspace_commercial import (
    aceptar_propuesta,
    cancelar_contrato,
    crear_revision_desde_contrato,
)
from invitaciones.models import EventoBoda
from organizaciones.models import EmpresaSuscriptora, MembresiaEmpresa
from paquetes.models import PaqueteBoda, PropuestaEvento
from presupuesto.services import contrato_financiero_evento


class D2ContractLifecycleTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.empresa = EmpresaSuscriptora.objects.create(
            nombre_comercial="Empresa D2",
            slug="empresa-d2-contract",
        )
        self.admin = User.objects.create_user(username="admin-d2-contract", password="test123")
        MembresiaEmpresa.objects.create(
            empresa=self.empresa,
            usuario=self.admin,
            rol="ADMIN_EMPRESA",
        )
        now = timezone.now()
        self.evento = EventoBoda.objects.create(
            empresa=self.empresa,
            nombre_evento="Evento D2",
            novio="Cliente",
            novia="Principal",
            frase_portada="D2",
            mensaje_general="D2",
            fecha_misa=now,
            lugar_misa="Ceremonia",
            fecha_fiesta=now,
            lugar_fiesta="Recepcion",
            wedding_planner=self.admin,
        )
        self.paquete = PaqueteBoda.objects.create(
            empresa=self.empresa,
            nombre="Paquete D2",
            precio_adulto=Decimal("1000.00"),
            cargo_fijo=Decimal("5000.00"),
        )

    def propuesta_aceptada(self, adultos=10):
        propuesta = PropuestaEvento.objects.create(
            empresa=self.empresa,
            evento=self.evento,
            paquete=self.paquete,
            adultos=adultos,
            estado="BORRADOR",
            created_by=self.admin,
            updated_by=self.admin,
        )
        aceptar_propuesta(propuesta, user=self.admin)
        propuesta.refresh_from_db()
        return propuesta

    def test_contratado_is_canonical_current_contract(self):
        propuesta = self.propuesta_aceptada()
        contrato = generar_contrato_v2_desde_propuesta(propuesta.id, user=self.admin)
        self.assertEqual(contrato_vigente(self.evento).id, contrato.id)
        self.assertTrue(contrato_es_vigente(contrato))
        self.assertTrue(contrato_es_materializable(contrato))

    def test_legacy_firmado_is_current_when_no_k9_contract_exists(self):
        contrato = ContratoEvento.objects.create(
            evento=self.evento,
            version=1,
            estado="FIRMADO",
            monto_base=Decimal("12345.00"),
            snapshot_version=1,
        )
        self.assertEqual(contrato_vigente(self.evento).id, contrato.id)
        self.assertTrue(contrato_es_vigente(contrato))
        self.assertFalse(contrato_es_materializable(contrato))

    def test_finance_uses_same_current_contract_selector(self):
        firmado = ContratoEvento.objects.create(
            evento=self.evento,
            version=1,
            estado="FIRMADO",
            monto_base=Decimal("100.00"),
            snapshot_version=1,
        )
        propuesta = self.propuesta_aceptada(adultos=20)
        contratado = generar_contrato_v2_desde_propuesta(propuesta.id, user=self.admin)
        firmado.refresh_from_db()

        self.assertEqual(firmado.estado, "REEMPLAZADO")
        self.assertEqual(contrato_vigente(self.evento).id, contratado.id)
        financiero = contrato_financiero_evento(self.evento)
        self.assertEqual(financiero["contrato"].id, contratado.id)

    def test_new_contract_supersedes_previous_active_even_if_firmado(self):
        firmado = ContratoEvento.objects.create(
            evento=self.evento,
            version=1,
            estado="FIRMADO",
            monto_base=Decimal("100.00"),
        )
        propuesta = self.propuesta_aceptada()
        nuevo = generar_contrato_v2_desde_propuesta(propuesta.id, user=self.admin)
        firmado.refresh_from_db()

        self.assertEqual(firmado.estado, "REEMPLAZADO")
        self.assertEqual(contrato_vigente(self.evento).id, nuevo.id)

    def test_old_active_version_cannot_start_revision(self):
        viejo = ContratoEvento.objects.create(
            evento=self.evento,
            version=1,
            estado="FIRMADO",
            monto_base=Decimal("100.00"),
        )
        propuesta = self.propuesta_aceptada()
        generar_contrato_v2_desde_propuesta(propuesta.id, user=self.admin)
        viejo.refresh_from_db()

        with self.assertRaises(ValidationError):
            crear_revision_desde_contrato(viejo, user=self.admin)

    def test_cancel_current_contract_removes_current_contract(self):
        propuesta = self.propuesta_aceptada()
        contrato = generar_contrato_v2_desde_propuesta(propuesta.id, user=self.admin)
        cancelar_contrato(contrato, motivo="Prueba D2", user=self.admin)
        contrato.refresh_from_db()

        self.assertEqual(contrato.estado, "CANCELADO")
        self.assertIsNone(contrato_vigente(self.evento))
        financiero = contrato_financiero_evento(self.evento)
        self.assertIsNone(financiero["contrato"])
        self.assertEqual(financiero["total_contratado"], Decimal("0.00"))

    def test_workspace_does_not_present_cancelled_contract_as_current(self):
        propuesta = self.propuesta_aceptada()
        contrato = generar_contrato_v2_desde_propuesta(propuesta.id, user=self.admin)
        cancelar_contrato(contrato, motivo="Prueba D2", user=self.admin)

        self.client.force_login(self.admin)
        response = self.client.get(
            reverse(
                "k9_evento_comercial",
                kwargs={"empresa_slug": self.empresa.slug, "evento_id": self.evento.id},
            )
        )
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.context["contrato_actual"])

    def test_cancelled_or_replaced_contract_cannot_be_current(self):
        c1 = ContratoEvento.objects.create(
            evento=self.evento,
            version=1,
            estado="CANCELADO",
            monto_base=Decimal("100.00"),
        )
        c2 = ContratoEvento.objects.create(
            evento=self.evento,
            version=2,
            estado="REEMPLAZADO",
            monto_base=Decimal("200.00"),
        )
        self.assertIsNone(contrato_vigente(self.evento))
        self.assertFalse(contrato_es_vigente(c1))
        self.assertFalse(contrato_es_vigente(c2))
