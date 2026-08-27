from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from catalogo.models import ServicioCatalogo
from colaboracion.models import AjusteContractualServicio
from colaboracion.services import crear_propuesta_servicio, responder_propuesta_servicio
from eventos.services import generar_contrato_v2_desde_propuesta, materializar_servicios_contrato_v2
from eventos.workspace_commercial import aceptar_propuesta
from invitaciones.models import EventoBoda
from organizaciones.models import EmpresaSuscriptora, MembresiaEmpresa
from paquetes.models import PaqueteBoda, PaqueteServicio, PropuestaEvento
from presupuesto.services import obtener_resumen_financiero_evento
from proveedores.models import ServicioEvento


class D5PostContractChangesTests(TestCase):
    def setUp(self):
        User=get_user_model()
        self.empresa=EmpresaSuscriptora.objects.create(nombre_comercial="Empresa D5",slug="empresa-d5")
        self.admin=User.objects.create_user(username="admin-d5",password="test123")
        self.cliente=User.objects.create_user(username="cliente-d5",password="test123")
        MembresiaEmpresa.objects.create(empresa=self.empresa,usuario=self.admin,rol="ADMIN_EMPRESA")
        MembresiaEmpresa.objects.create(empresa=self.empresa,usuario=self.cliente,rol="CLIENTE")
        now=timezone.now()
        self.evento=EventoBoda.objects.create(
            empresa=self.empresa,nombre_evento="Evento D5",novio="A",novia="B",
            frase_portada="D5",mensaje_general="D5",fecha_misa=now,lugar_misa="X",
            fecha_fiesta=now,lugar_fiesta="Y",wedding_planner=self.admin,
        )
        self.evento.clientes.add(self.cliente)
        self.catalogo=ServicioCatalogo.objects.create(
            empresa=self.empresa,nombre="DJ D5",categoria="MUSICA",unidad="EVENTO"
        )
        self.paquete=PaqueteBoda.objects.create(
            empresa=self.empresa,nombre="Paquete D5",
            precio_adulto=Decimal("1000.00"),cargo_fijo=Decimal("5000.00"),
        )
        PaqueteServicio.objects.create(paquete=self.paquete,servicio_catalogo=self.catalogo,cantidad=1,orden=1)
        propuesta=PropuestaEvento.objects.create(
            empresa=self.empresa,evento=self.evento,paquete=self.paquete,
            adultos=10,estado="BORRADOR",created_by=self.admin,updated_by=self.admin,
        )
        aceptar_propuesta(propuesta,user=self.admin)
        propuesta.refresh_from_db()
        self.contrato=generar_contrato_v2_desde_propuesta(propuesta.id,user=self.admin)
        materializar_servicios_contrato_v2(self.contrato.id,user=self.admin)
        self.servicio=ServicioEvento.objects.get(evento=self.evento,servicio_catalogo_k9=self.catalogo)
        self.total_base=Decimal(self.contrato.snapshot_comercial["totales"]["total_final"])

    def aprobar(self,modalidad="ADICIONAL",cargo="2500.00"):
        p=crear_propuesta_servicio(
            self.servicio,user=self.admin,descripcion="Cambio D5",
            modalidad=modalidad,cargo_adicional_cliente=cargo,enviar=True,
        )
        return responder_propuesta_servicio(p,user=self.cliente,estado="APROBADA",comentario="Aceptado")

    def test_approved_additional_creates_append_only_adjustment(self):
        snapshot_original=dict(self.contrato.snapshot_comercial)
        aprobada=self.aprobar()
        ajuste=AjusteContractualServicio.objects.get(propuesta_origen=aprobada)
        self.assertEqual(ajuste.contrato_base_id,self.contrato.id)
        self.assertEqual(ajuste.servicio_evento_id,self.servicio.id)
        self.assertEqual(ajuste.monto_cliente,Decimal("2500.00"))
        self.contrato.refresh_from_db()
        self.assertEqual(self.contrato.snapshot_comercial,snapshot_original)

    def test_finance_adds_adjustment(self):
        self.aprobar()
        r=obtener_resumen_financiero_evento(self.evento)
        self.assertEqual(r["total_base_contrato"],self.total_base)
        self.assertEqual(r["total_ajustes_contractuales"],Decimal("2500.00"))
        self.assertEqual(r["total_contratado"],self.total_base+Decimal("2500.00"))

    def test_multiple_changes_accumulate(self):
        self.aprobar(cargo="2500")
        self.aprobar(modalidad="UPGRADE",cargo="1000")
        self.servicio.refresh_from_db()
        r=obtener_resumen_financiero_evento(self.evento)
        self.assertEqual(r["total_ajustes_contractuales"],Decimal("3500.00"))
        self.assertEqual(self.servicio.cargo_adicional_cliente,Decimal("3500.00"))

    def test_rejection_has_no_financial_effect(self):
        p=crear_propuesta_servicio(self.servicio,user=self.admin,modalidad="ADICIONAL",cargo_adicional_cliente="2500",enviar=True)
        responder_propuesta_servicio(p,user=self.cliente,estado="RECHAZADA")
        self.assertFalse(AjusteContractualServicio.objects.exists())
        self.assertEqual(obtener_resumen_financiero_evento(self.evento)["total_contratado"],self.total_base)

    def test_courtesy_zero_charge_is_historical(self):
        aprobada=self.aprobar(modalidad="CORTESIA",cargo="0")
        ajuste=AjusteContractualServicio.objects.get(propuesta_origen=aprobada)
        self.assertEqual(ajuste.tipo,"CORTESIA")
        self.assertEqual(ajuste.monto_cliente,Decimal("0.00"))
        self.assertEqual(obtener_resumen_financiero_evento(self.evento)["total_contratado"],self.total_base)

    def test_change_requires_current_contract(self):
        self.contrato.estado="CANCELADO"
        self.contrato.save(update_fields=["estado"])
        p=crear_propuesta_servicio(self.servicio,user=self.admin,modalidad="ADICIONAL",cargo_adicional_cliente="2500",enviar=True)
        with self.assertRaises(ValueError):
            responder_propuesta_servicio(p,user=self.cliente,estado="APROBADA")
        p.refresh_from_db()
        self.assertEqual(p.estado,"ENVIADA")
        self.assertFalse(AjusteContractualServicio.objects.exists())

    def test_adjustment_marks_service_as_historical_footprint(self):
        self.aprobar()
        self.assertTrue(self.servicio.ajustes_contractuales.filter(estado="VIGENTE").exists())
