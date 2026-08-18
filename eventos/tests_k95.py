import json
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from catalogo.models import ServicioCatalogo
from organizaciones.models import EmpresaSuscriptora, MembresiaEmpresa, SedeEvento
from paquetes.models import PaqueteBoda, PaqueteEvento, PaqueteServicio, PropuestaEvento, PropuestaLinea, ServicioPaquete
from paquetes.services import capturar_snapshot_paquete
from presupuesto.models import GastoEvento, PagoClienteEvento, PagoEvento
from proveedores.models import Proveedor, ServicioEvento

from .models import ContratoEvento
from .services import generar_contrato_v2_desde_propuesta, leer_contrato_publico, leer_contrato_v1_paquete_evento


def crear_evento(empresa, *, planner=None, cliente=None, nombre="Evento K95"):
    ahora = timezone.now()
    from invitaciones.models import EventoBoda

    evento = EventoBoda.objects.create(
        empresa=empresa,
        nombre_evento=nombre,
        novio='Cliente',
        novia='Principal',
        frase_portada='Celebracion',
        mensaje_general='Mensaje del evento.',
        fecha_misa=ahora,
        lugar_misa='Ceremonia',
        fecha_fiesta=ahora,
        lugar_fiesta='Recepcion',
        wedding_planner=planner,
    )
    if cliente:
        evento.clientes.add(cliente)
    return evento


class ContratoV2K95Tests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.empresa_a = EmpresaSuscriptora.objects.create(nombre_comercial="Empresa A K95", slug="empresa-a-k95")
        self.empresa_b = EmpresaSuscriptora.objects.create(nombre_comercial="Empresa B K95", slug="empresa-b-k95")
        self.admin_a = User.objects.create_user(username="admin-a-k95", password="test123")
        self.admin_b = User.objects.create_user(username="admin-b-k95", password="test123")
        self.planner_a = User.objects.create_user(username="planner-a-k95", password="test123")
        self.planner_b = User.objects.create_user(username="planner-b-k95", password="test123")
        self.cliente_a = User.objects.create_user(username="cliente-a-k95", password="test123")
        self.cliente_b = User.objects.create_user(username="cliente-b-k95", password="test123")
        self.proveedor_user = User.objects.create_user(username="proveedor-a-k95", password="test123")
        self.dirtec = User.objects.create_superuser(username="dirtec-k95", email="dirtec@example.com", password="test123")
        MembresiaEmpresa.objects.create(empresa=self.empresa_a, usuario=self.admin_a, rol="ADMIN_EMPRESA")
        MembresiaEmpresa.objects.create(empresa=self.empresa_b, usuario=self.admin_b, rol="ADMIN_EMPRESA")
        MembresiaEmpresa.objects.create(empresa=self.empresa_a, usuario=self.planner_a, rol="WEDDING_PLANNER")
        MembresiaEmpresa.objects.create(empresa=self.empresa_b, usuario=self.planner_b, rol="WEDDING_PLANNER")
        MembresiaEmpresa.objects.create(empresa=self.empresa_a, usuario=self.cliente_a, rol="CLIENTE")
        MembresiaEmpresa.objects.create(empresa=self.empresa_b, usuario=self.cliente_b, rol="CLIENTE")
        MembresiaEmpresa.objects.create(empresa=self.empresa_a, usuario=self.proveedor_user, rol="PROVEEDOR")
        self.proveedor = Proveedor.objects.create(
            empresa=self.empresa_a,
            usuario=self.proveedor_user,
            nombre_comercial="Proveedor K95",
        )
        self.sede = SedeEvento.objects.create(
            empresa=self.empresa_a,
            nombre="Salon K95",
            direccion="Direccion K95",
            precio_base=Decimal("10000.00"),
        )
        self.evento = crear_evento(self.empresa_a, planner=self.planner_a, cliente=self.cliente_a)
        self.evento_b = crear_evento(self.empresa_b, planner=self.planner_b, cliente=self.cliente_b, nombre="Evento B K95")
        self.servicio_dj = ServicioCatalogo.objects.create(empresa=self.empresa_a, nombre="DJ", categoria="MUSICA", unidad="EVENTO")
        self.servicio_alcohol = ServicioCatalogo.objects.create(empresa=self.empresa_a, nombre="Alcohol", categoria="BEBIDAS", unidad="PERSONA")
        self.paquete = PaqueteBoda.objects.create(
            empresa=self.empresa_a,
            nombre="Paquete 2",
            descripcion="Paquete comercial",
            precio_adulto=Decimal("1000.00"),
            precio_nino=Decimal("500.00"),
            cargo_fijo=Decimal("2500.00"),
            duracion_evento=6,
            capacidad_minima_recomendada=200,
            capacidad_maxima_recomendada=350,
        )
        PaqueteServicio.objects.create(
            paquete=self.paquete,
            servicio_catalogo=self.servicio_dj,
            cantidad=1,
            orden=1,
            notas="Incluye cabina",
        )
        self.propuesta = self.crear_propuesta()

    def crear_propuesta(self, *, estado="ACEPTADO"):
        propuesta = PropuestaEvento.objects.create(
            empresa=self.empresa_a,
            evento=self.evento,
            sede=self.sede,
            paquete=self.paquete,
            adultos=250,
            ninos=40,
            descuento=Decimal("5000.00"),
            estado=estado,
            notas_comerciales="Condiciones comerciales visibles.",
        )
        PropuestaLinea.objects.create(
            propuesta=propuesta,
            tipo="ADICIONAL",
            servicio_catalogo=self.servicio_alcohol,
            nombre="Alcohol",
            modo_precio="POR_PERSONA",
            tarifa=Decimal("450.00"),
            cantidad=1,
        )
        PropuestaLinea.objects.create(
            propuesta=propuesta,
            tipo="CORTESIA",
            nombre="Letras Hollywood",
            modo_precio="FIJO",
            tarifa=Decimal("8000.00"),
            valor_informativo=Decimal("8000.00"),
        )
        return propuesta

    def generar(self, propuesta=None):
        return generar_contrato_v2_desde_propuesta((propuesta or self.propuesta).id, user=self.admin_a)

    def contrato_url(self, contrato, empresa=None):
        empresa = empresa or self.empresa_a
        return reverse("eventos_contrato_detail", args=[empresa.slug, contrato.id])

    def test_generar_contrato_desde_aceptado(self):
        contrato = self.generar()
        self.assertEqual(contrato.estado, "CONTRATADO")
        self.assertEqual(ContratoEvento.objects.count(), 1)

    def test_no_generar_desde_borrador(self):
        propuesta = self.crear_propuesta(estado="BORRADOR")
        with self.assertRaises(ValidationError):
            self.generar(propuesta)

    def test_no_generar_desde_propuesta(self):
        propuesta = self.crear_propuesta(estado="PROPUESTA")
        with self.assertRaises(ValidationError):
            self.generar(propuesta)

    def test_no_generar_desde_en_revision(self):
        propuesta = self.crear_propuesta(estado="EN_REVISION")
        with self.assertRaises(ValidationError):
            self.generar(propuesta)

    def test_propuesta_cambia_a_contratado_solo_despues_de_exito(self):
        propuesta = self.crear_propuesta(estado="BORRADOR")
        with self.assertRaises(ValidationError):
            self.generar(propuesta)
        propuesta.refresh_from_db()
        self.assertEqual(propuesta.estado, "BORRADOR")
        self.generar(self.propuesta)
        self.propuesta.refresh_from_db()
        self.assertEqual(self.propuesta.estado, "CONTRATADO")

    def test_segunda_generacion_es_idempotente(self):
        contrato = self.generar()
        segundo = self.generar()
        self.assertEqual(contrato.id, segundo.id)
        self.assertEqual(ContratoEvento.objects.count(), 1)

    def test_snapshot_version_es_2(self):
        contrato = self.generar()
        self.assertEqual(contrato.snapshot_version, 2)
        self.assertEqual(contrato.snapshot_comercial["version"], 2)

    def test_snapshot_guarda_adultos(self):
        contrato = self.generar()
        self.assertEqual(contrato.snapshot_comercial["cantidades"]["adultos"], 250)

    def test_snapshot_guarda_ninos(self):
        contrato = self.generar()
        self.assertEqual(contrato.snapshot_comercial["cantidades"]["ninos"], 40)

    def test_snapshot_guarda_paquete(self):
        contrato = self.generar()
        self.assertEqual(contrato.snapshot_comercial["paquete"]["nombre"], "Paquete 2")

    def test_snapshot_guarda_incluidos(self):
        contrato = self.generar()
        self.assertEqual(contrato.snapshot_comercial["incluidos"][0]["nombre"], "DJ")

    def test_snapshot_guarda_adicionales(self):
        contrato = self.generar()
        self.assertEqual(contrato.snapshot_comercial["adicionales"][0]["nombre"], "Alcohol")

    def test_snapshot_guarda_cortesias(self):
        contrato = self.generar()
        self.assertEqual(contrato.snapshot_comercial["cortesias"][0]["nombre"], "Letras Hollywood")

    def test_cortesia_cargo_cliente_cero(self):
        contrato = self.generar()
        self.assertEqual(contrato.snapshot_comercial["cortesias"][0]["cargo_cliente"], "0.00")

    def test_snapshot_guarda_descuento(self):
        contrato = self.generar()
        self.assertEqual(contrato.snapshot_comercial["descuentos"]["monto"], "5000.00")

    def test_snapshot_guarda_total(self):
        contrato = self.generar()
        self.assertEqual(contrato.snapshot_comercial["totales"]["total_final"], "398000.00")

    def test_total_recalcula_server_side(self):
        self.propuesta.total = Decimal("1.00")
        self.propuesta.subtotal = Decimal("1.00")
        self.propuesta.save(update_fields=["total", "subtotal", "updated_at"])
        contrato = self.generar()
        self.assertEqual(contrato.snapshot_comercial["totales"]["total_final"], "398000.00")

    def test_modificacion_posterior_paquete_no_cambia_contrato(self):
        contrato = self.generar()
        original = contrato.snapshot_comercial["paquete"]["nombre"]
        self.paquete.nombre = "Paquete cambiado"
        self.paquete.precio_adulto = Decimal("9999.00")
        self.paquete.save(update_fields=["nombre", "precio_adulto"])
        contrato.refresh_from_db()
        self.assertEqual(contrato.snapshot_comercial["paquete"]["nombre"], original)

    def test_modificacion_posterior_catalogo_no_cambia_contrato(self):
        contrato = self.generar()
        self.servicio_dj.nombre = "DJ cambiado"
        self.servicio_dj.save(update_fields=["nombre"])
        contrato.refresh_from_db()
        self.assertEqual(contrato.snapshot_comercial["incluidos"][0]["nombre"], "DJ")

    def test_modificacion_posterior_propuesta_no_cambia_contrato(self):
        contrato = self.generar()
        self.propuesta.adultos = 10
        self.propuesta.save(update_fields=["adultos", "updated_at"])
        contrato.refresh_from_db()
        self.assertEqual(contrato.snapshot_comercial["cantidades"]["adultos"], 250)

    def test_cambio_proveedor_no_afecta_snapshot(self):
        contrato = self.generar()
        self.proveedor.nombre_comercial = "Proveedor cambiado"
        self.proveedor.save(update_fields=["nombre_comercial"])
        contrato.refresh_from_db()
        self.assertNotIn("Proveedor cambiado", json.dumps(contrato.snapshot_comercial))

    def test_snapshot_no_contiene_costo_proveedor(self):
        contrato = self.generar()
        self.assertNotIn("costo", json.dumps(contrato.snapshot_comercial).lower())

    def test_snapshot_no_contiene_margen(self):
        contrato = self.generar()
        self.assertNotIn("margen", json.dumps(contrato.snapshot_comercial).lower())

    def test_cliente_autorizado_ve_contrato(self):
        contrato = self.generar()
        self.client.force_login(self.cliente_a)
        response = self.client.get(self.contrato_url(contrato))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Total contratado")

    def test_cliente_ajeno_no_ve_contrato(self):
        contrato = self.generar()
        self.client.force_login(self.cliente_b)
        response = self.client.get(self.contrato_url(contrato))
        self.assertEqual(response.status_code, 404)

    def test_cliente_no_ve_campos_internos(self):
        contrato = self.generar()
        self.client.force_login(self.cliente_a)
        response = self.client.get(self.contrato_url(contrato))
        html = response.content.decode().lower()
        self.assertNotIn("costo proveedor", html)
        self.assertNotIn("margen", html)
        self.assertNotIn("pago proveedor", html)

    def test_planner_asignado_ve_contrato(self):
        contrato = self.generar()
        self.client.force_login(self.planner_a)
        response = self.client.get(self.contrato_url(contrato))
        self.assertEqual(response.status_code, 200)

    def test_planner_no_asignado_no_ve_contrato(self):
        contrato = self.generar()
        otro = get_user_model().objects.create_user(username="planner-otro-k95", password="test123")
        MembresiaEmpresa.objects.create(empresa=self.empresa_a, usuario=otro, rol="WEDDING_PLANNER")
        self.client.force_login(otro)
        response = self.client.get(self.contrato_url(contrato))
        self.assertEqual(response.status_code, 403)

    def test_empresa_mismo_tenant_ve(self):
        contrato = self.generar()
        self.client.force_login(self.admin_a)
        response = self.client.get(self.contrato_url(contrato))
        self.assertEqual(response.status_code, 200)

    def test_empresa_otro_tenant_no_ve(self):
        contrato = self.generar()
        self.client.force_login(self.admin_b)
        response = self.client.get(self.contrato_url(contrato))
        self.assertEqual(response.status_code, 404)

    def test_proveedor_no_ve_contrato_completo(self):
        contrato = self.generar()
        self.client.force_login(self.proveedor_user)
        response = self.client.get(self.contrato_url(contrato))
        self.assertEqual(response.status_code, 403)

    def test_dirtec_autorizado_ve(self):
        contrato = self.generar()
        self.client.force_login(self.dirtec)
        response = self.client.get(self.contrato_url(contrato))
        self.assertEqual(response.status_code, 200)

    def test_snapshot_v1_sigue_legible(self):
        servicio_legacy = ServicioPaquete.objects.create(
            paquete=self.paquete,
            tipo_servicio="DJ",
            descripcion="DJ legacy",
            cantidad=1,
            precio_incluido=Decimal("1000.00"),
        )
        paquete_evento = PaqueteEvento.objects.create(
            evento=self.evento,
            paquete=self.paquete,
            precio_acordado=Decimal("52000.00"),
            descuento=Decimal("2000.00"),
            estado="CONTRATADO",
        )
        capturar_snapshot_paquete(paquete_evento)
        paquete_evento.refresh_from_db()
        data = leer_contrato_v1_paquete_evento(paquete_evento)
        self.assertEqual(data["version"], 1)
        self.assertEqual(data["incluidos"][0]["nombre"], servicio_legacy.descripcion)

    def test_k8_snapshot_materializacion_sigue_funcionando(self):
        ServicioPaquete.objects.create(
            paquete=self.paquete,
            tipo_servicio="DJ",
            descripcion="DJ legacy",
            cantidad=1,
            precio_incluido=Decimal("1000.00"),
        )
        paquete_evento = PaqueteEvento.objects.create(
            evento=self.evento,
            paquete=self.paquete,
            precio_acordado=Decimal("52000.00"),
            descuento=Decimal("2000.00"),
            estado="CONTRATADO",
        )
        snapshot = capturar_snapshot_paquete(paquete_evento)
        self.assertEqual(snapshot["nombre"], "Paquete 2")

    def test_no_crea_servicio_evento(self):
        self.generar()
        self.assertEqual(ServicioEvento.objects.count(), 0)

    def test_no_crea_gastos(self):
        self.generar()
        self.assertEqual(GastoEvento.objects.count(), 0)

    def test_no_crea_pagos(self):
        self.generar()
        self.assertEqual(PagoEvento.objects.count(), 0)
        self.assertEqual(PagoClienteEvento.objects.count(), 0)

    def test_post_url_manipulada_no_cruza_tenant(self):
        self.client.force_login(self.admin_b)
        response = self.client.post(reverse("eventos_contrato_generar", args=[self.empresa_b.slug, self.propuesta.id]))
        self.assertEqual(response.status_code, 404)

    def test_reader_publico_no_expone_metadata_interna(self):
        contrato = self.generar()
        data = leer_contrato_publico(contrato)
        self.assertNotIn("metadata", data)
