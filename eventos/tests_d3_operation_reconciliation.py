from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from catalogo.models import ServicioCatalogo
from colaboracion.models import ConversacionServicio
from eventos.services import generar_contrato_v2_desde_propuesta, materializar_servicios_contrato_v2
from eventos.workspace_commercial import aceptar_propuesta, crear_revision_desde_contrato
from invitaciones.models import EventoBoda
from organizaciones.models import EmpresaSuscriptora, MembresiaEmpresa
from paquetes.models import PaqueteBoda, PaqueteServicio, PropuestaEvento, PropuestaLinea
from proveedores.models import Proveedor, ServicioEvento


class D3ContractOperationReconciliationTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.empresa = EmpresaSuscriptora.objects.create(nombre_comercial="Empresa D3", slug="empresa-d3")
        self.admin = User.objects.create_user(username="admin-d3", password="test123")
        MembresiaEmpresa.objects.create(empresa=self.empresa, usuario=self.admin, rol="ADMIN_EMPRESA")
        now = timezone.now()
        self.evento = EventoBoda.objects.create(
            empresa=self.empresa, nombre_evento="Evento D3", novio="A", novia="B",
            frase_portada="D3", mensaje_general="D3", fecha_misa=now,
            lugar_misa="Ceremonia", fecha_fiesta=now, lugar_fiesta="Recepcion",
            wedding_planner=self.admin,
        )
        self.catalogo = ServicioCatalogo.objects.create(
            empresa=self.empresa, nombre="DJ D3", categoria="MUSICA", unidad="EVENTO"
        )
        self.extra_catalogo = ServicioCatalogo.objects.create(
            empresa=self.empresa, nombre="Foto D3", categoria="FOTO_VIDEO", unidad="EVENTO"
        )
        self.paquete = PaqueteBoda.objects.create(
            empresa=self.empresa, nombre="Paquete D3",
            precio_adulto=Decimal("1000.00"), cargo_fijo=Decimal("5000.00"),
        )
        PaqueteServicio.objects.create(
            paquete=self.paquete, servicio_catalogo=self.catalogo, cantidad=1, orden=1
        )
        self.propuesta = PropuestaEvento.objects.create(
            empresa=self.empresa, evento=self.evento, paquete=self.paquete,
            adultos=10, estado="BORRADOR", created_by=self.admin, updated_by=self.admin,
        )
        self.extra = PropuestaLinea.objects.create(
            propuesta=self.propuesta, tipo="ADICIONAL", servicio_catalogo=self.extra_catalogo,
            nombre="Foto D3", modo_precio="FIJO", tarifa=Decimal("3000.00"), cantidad=1,
        )
        aceptar_propuesta(self.propuesta, user=self.admin)
        self.propuesta.refresh_from_db()
        self.contrato_v1 = generar_contrato_v2_desde_propuesta(self.propuesta.id, user=self.admin)
        materializar_servicios_contrato_v2(self.contrato_v1.id, user=self.admin)

    def revision(self):
        return crear_revision_desde_contrato(self.contrato_v1, user=self.admin)

    def accept_contract(self, propuesta):
        aceptar_propuesta(propuesta, user=self.admin)
        propuesta.refresh_from_db()
        return generar_contrato_v2_desde_propuesta(propuesta.id, user=self.admin)

    def test_unchanged_revision_reuses_service_rows(self):
        ids_v1 = set(ServicioEvento.objects.filter(evento=self.evento).values_list("id", flat=True))
        nueva = self.revision()
        contrato_v2 = self.accept_contract(nueva)
        result = materializar_servicios_contrato_v2(contrato_v2.id, user=self.admin)

        ids_v2 = set(ServicioEvento.objects.filter(evento=self.evento, estado_comercial="CONTRATADO").values_list("id", flat=True))
        self.assertEqual(ids_v1, ids_v2)
        self.assertGreaterEqual(result["reutilizados"], 1)
        self.assertFalse(
            ServicioEvento.objects.filter(evento=self.evento, contrato_origen=self.contrato_v1, estado_comercial="CONTRATADO").exists()
        )

    def test_provider_and_chat_survive_contract_revision(self):
        servicio = ServicioEvento.objects.get(evento=self.evento, servicio_catalogo_k9=self.extra_catalogo)
        proveedor = Proveedor.objects.create(empresa=self.empresa, nombre_comercial="Proveedor D3")
        servicio.proveedor = proveedor
        servicio.save(update_fields=["proveedor", "fecha_actualizacion"])
        conversacion = ConversacionServicio.objects.create(
            servicio_evento=servicio, canal="INTERNO", creada_por=self.admin
        )

        nueva = self.revision()
        contrato_v2 = self.accept_contract(nueva)
        materializar_servicios_contrato_v2(contrato_v2.id, user=self.admin)

        servicio.refresh_from_db()
        conversacion.refresh_from_db()
        self.assertEqual(servicio.proveedor_id, proveedor.id)
        self.assertEqual(servicio.contrato_origen_id, contrato_v2.id)
        self.assertEqual(conversacion.servicio_evento_id, servicio.id)
        self.assertTrue((servicio.snapshot_linea or {}).get("historial_contractual"))

    def test_new_revision_line_creates_only_one_new_service(self):
        before = ServicioEvento.objects.filter(evento=self.evento).count()
        nueva = self.revision()
        PropuestaLinea.objects.create(
            propuesta=nueva, tipo="CORTESIA", nombre="Letras D3",
            modo_precio="FIJO", tarifa=Decimal("0.00"), valor_informativo=Decimal("2000.00"), cantidad=1,
        )
        contrato_v2 = self.accept_contract(nueva)
        result = materializar_servicios_contrato_v2(contrato_v2.id, user=self.admin)

        self.assertEqual(ServicioEvento.objects.filter(evento=self.evento).count(), before + 1)
        self.assertEqual(result["creados"], 1)

    def test_removed_pristine_line_is_cancelled_not_deleted(self):
        servicio_extra = ServicioEvento.objects.get(evento=self.evento, servicio_catalogo_k9=self.extra_catalogo)
        nueva = self.revision()
        nueva.lineas.filter(tipo="ADICIONAL").delete()
        contrato_v2 = self.accept_contract(nueva)
        result = materializar_servicios_contrato_v2(contrato_v2.id, user=self.admin)

        servicio_extra.refresh_from_db()
        self.assertEqual(servicio_extra.estado_operativo, "CANCELADO")
        self.assertEqual(servicio_extra.estado_comercial, "CANCELADO")
        self.assertEqual(servicio_extra.contrato_origen_id, self.contrato_v1.id)
        self.assertEqual(result["retirados"], 1)

    def test_removed_operational_line_requires_explicit_resolution(self):
        servicio_extra = ServicioEvento.objects.get(evento=self.evento, servicio_catalogo_k9=self.extra_catalogo)
        proveedor = Proveedor.objects.create(empresa=self.empresa, nombre_comercial="Proveedor bloqueo D3")
        servicio_extra.proveedor = proveedor
        servicio_extra.save(update_fields=["proveedor", "fecha_actualizacion"])

        nueva = self.revision()
        nueva.lineas.filter(tipo="ADICIONAL").delete()
        contrato_v2 = self.accept_contract(nueva)

        with self.assertRaises(ValidationError):
            materializar_servicios_contrato_v2(contrato_v2.id, user=self.admin)

        servicio_extra.refresh_from_db()
        self.assertEqual(servicio_extra.contrato_origen_id, self.contrato_v1.id)
        self.assertNotEqual(servicio_extra.estado_operativo, "CANCELADO")

    def test_materialization_is_idempotent_after_reconciliation(self):
        nueva = self.revision()
        contrato_v2 = self.accept_contract(nueva)
        first = materializar_servicios_contrato_v2(contrato_v2.id, user=self.admin)
        count = ServicioEvento.objects.filter(evento=self.evento).count()
        second = materializar_servicios_contrato_v2(contrato_v2.id, user=self.admin)

        self.assertEqual(ServicioEvento.objects.filter(evento=self.evento).count(), count)
        self.assertEqual(set(first["servicio_evento_ids"]), set(second["servicio_evento_ids"]))
        self.assertEqual(second["creados"], 0)
