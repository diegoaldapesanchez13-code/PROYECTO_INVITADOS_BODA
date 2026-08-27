from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from catalogo.models import ServicioCatalogo
from eventos.models import ContratoEvento
from eventos.services import generar_contrato_v2_desde_propuesta
from eventos.workspace_commercial import aceptar_propuesta, reabrir_propuesta
from invitaciones.models import EventoBoda
from organizaciones.models import EmpresaSuscriptora, MembresiaEmpresa, SedeEvento
from paquetes.models import PaqueteBoda, PaqueteServicio, PropuestaEvento, PropuestaLinea
from paquetes.services import propuesta_tiene_snapshot_aceptacion


class D1ProposalIntegrityTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.empresa = EmpresaSuscriptora.objects.create(
            nombre_comercial="Empresa D1",
            slug="empresa-d1-integrity",
        )
        self.admin = User.objects.create_user(username="admin-d1-integrity", password="test123")
        MembresiaEmpresa.objects.create(
            empresa=self.empresa,
            usuario=self.admin,
            rol="ADMIN_EMPRESA",
        )
        self.sede = SedeEvento.objects.create(empresa=self.empresa, nombre="Salon D1")
        ahora = timezone.now()
        self.evento = EventoBoda.objects.create(
            empresa=self.empresa,
            nombre_evento="Evento D1",
            novio="Cliente",
            novia="Principal",
            frase_portada="Celebracion",
            mensaje_general="Evento",
            fecha_misa=ahora,
            lugar_misa="Ceremonia",
            fecha_fiesta=ahora,
            lugar_fiesta="Recepcion",
            wedding_planner=self.admin,
        )
        self.paquete = PaqueteBoda.objects.create(
            empresa=self.empresa,
            nombre="Premium D1",
            precio_adulto=Decimal("1000.00"),
            precio_nino=Decimal("500.00"),
            cargo_fijo=Decimal("10000.00"),
        )
        self.catalogo = ServicioCatalogo.objects.create(
            empresa=self.empresa,
            nombre="DJ Original",
            categoria="MUSICA",
            unidad="EVENTO",
        )
        self.incluido = PaqueteServicio.objects.create(
            paquete=self.paquete,
            servicio_catalogo=self.catalogo,
            cantidad=1,
        )
        self.propuesta = PropuestaEvento.objects.create(
            empresa=self.empresa,
            evento=self.evento,
            sede=self.sede,
            paquete=self.paquete,
            adultos=10,
            ninos=2,
            descuento=Decimal("1000.00"),
            estado="BORRADOR",
            notas_comerciales="Condiciones originales",
            created_by=self.admin,
            updated_by=self.admin,
        )
        PropuestaLinea.objects.create(
            propuesta=self.propuesta,
            tipo="ADICIONAL",
            servicio_catalogo=self.catalogo,
            nombre="DJ adicional",
            modo_precio="FIJO",
            tarifa=Decimal("2500.00"),
            cantidad=1,
        )

    def test_acceptance_creates_explicit_frozen_snapshot(self):
        aceptar_propuesta(self.propuesta, user=self.admin)
        self.propuesta.refresh_from_db()
        self.assertEqual(self.propuesta.estado, "ACEPTADO")
        self.assertTrue(propuesta_tiene_snapshot_aceptacion(self.propuesta))
        self.assertIsNotNone(self.propuesta.aceptado_en)
        self.assertEqual(self.propuesta.aceptado_por_id, self.admin.id)
        self.assertEqual(
            self.propuesta.snapshot_aceptacion["metadata"]["fuente"],
            "PROPUESTA_ACEPTADA_D1",
        )

    def test_accepted_proposal_rejects_direct_commercial_mutation_on_validation(self):
        aceptar_propuesta(self.propuesta, user=self.admin)
        self.propuesta.refresh_from_db()
        self.propuesta.adultos = 99
        with self.assertRaises(ValidationError):
            self.propuesta.full_clean()

    def test_contract_uses_acceptance_snapshot_after_master_changes(self):
        aceptar_propuesta(self.propuesta, user=self.admin)
        self.propuesta.refresh_from_db()
        accepted = self.propuesta.snapshot_aceptacion
        accepted_total = accepted["totales"]["total_final"]
        accepted_package_name = accepted["paquete"]["nombre"]
        accepted_included_name = accepted["incluidos"][0]["nombre"]

        self.paquete.nombre = "Premium MODIFICADO"
        self.paquete.precio_adulto = Decimal("9000.00")
        self.paquete.cargo_fijo = Decimal("90000.00")
        self.paquete.save()

        self.catalogo.nombre = "DJ MODIFICADO"
        self.catalogo.save(update_fields=["nombre"])

        contrato = generar_contrato_v2_desde_propuesta(self.propuesta.id, user=self.admin)

        self.assertEqual(contrato.snapshot_comercial["totales"]["total_final"], accepted_total)
        self.assertEqual(contrato.snapshot_comercial["paquete"]["nombre"], accepted_package_name)
        self.assertEqual(contrato.snapshot_comercial["incluidos"][0]["nombre"], accepted_included_name)
        self.assertEqual(str(contrato.monto_base), accepted_total)

    def test_reopen_acceptance_without_contract(self):
        aceptar_propuesta(self.propuesta, user=self.admin)
        self.propuesta.refresh_from_db()
        reabrir_propuesta(self.propuesta, user=self.admin)
        self.propuesta.refresh_from_db()
        self.assertEqual(self.propuesta.estado, "EN_REVISION")
        self.assertEqual(self.propuesta.snapshot_aceptacion, {})
        self.assertEqual(self.propuesta.snapshot_aceptacion_version, 0)
        self.assertIsNone(self.propuesta.aceptado_en)
        self.assertIsNone(self.propuesta.aceptado_por_id)

    def test_reopen_is_blocked_once_contract_exists(self):
        aceptar_propuesta(self.propuesta, user=self.admin)
        self.propuesta.refresh_from_db()
        generar_contrato_v2_desde_propuesta(self.propuesta.id, user=self.admin)
        self.propuesta.refresh_from_db()
        self.assertEqual(self.propuesta.estado, "CONTRATADO")
        with self.assertRaises(ValidationError):
            reabrir_propuesta(self.propuesta, user=self.admin)

    def test_legacy_accepted_without_snapshot_cannot_generate_new_contract(self):
        legacy = PropuestaEvento.objects.create(
            empresa=self.empresa,
            evento=self.evento,
            sede=self.sede,
            paquete=self.paquete,
            adultos=1,
            estado="ACEPTADO",
        )
        with self.assertRaises(ValidationError):
            generar_contrato_v2_desde_propuesta(legacy.id, user=self.admin)
