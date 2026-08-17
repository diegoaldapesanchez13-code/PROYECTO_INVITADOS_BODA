from decimal import Decimal
from pathlib import Path

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from catalogo.models import ServicioCatalogo
from invitaciones.models import EventoBoda
from organizaciones.models import EmpresaSuscriptora, MembresiaEmpresa, SedeEvento
from proveedores.models import Proveedor

from .models import PaqueteBoda, PaqueteEvento, PaqueteMediaComercial, PaqueteServicio, PropuestaEvento, PropuestaLinea, ServicioPaquete
from .services import actualizar_totales_propuesta, calcular_propuesta, capturar_snapshot_paquete


def archivo(nombre, contenido=b"test", content_type="application/octet-stream"):
    return SimpleUploadedFile(nombre, contenido, content_type=content_type)


def crear_evento(empresa, *, planner=None, cliente=None, nombre="Evento K94"):
    ahora = timezone.now()
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


@override_settings(
    MEDIA_ROOT="media/test/k94_paquetes/public",
    PRIVATE_MEDIA_ROOT="media/test/k94_paquetes/private",
)
class PropuestaComercialK94Tests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.empresa_a = EmpresaSuscriptora.objects.create(nombre_comercial="Empresa A K94", slug="empresa-a-k94")
        self.empresa_b = EmpresaSuscriptora.objects.create(nombre_comercial="Empresa B K94", slug="empresa-b-k94")
        self.admin_a = User.objects.create_user(username="admin-a-k94", password="test123")
        self.admin_b = User.objects.create_user(username="admin-b-k94", password="test123")
        self.planner_a = User.objects.create_user(username="planner-a-k94", password="test123")
        self.planner_b = User.objects.create_user(username="planner-b-k94", password="test123")
        self.cliente_a = User.objects.create_user(username="cliente-a-k94", password="test123")
        self.proveedor_user = User.objects.create_user(username="proveedor-a-k94", password="test123")
        self.dirtec = User.objects.create_superuser(username="dirtec-k94", email="dirtec@example.com", password="test123")
        MembresiaEmpresa.objects.create(empresa=self.empresa_a, usuario=self.admin_a, rol="ADMIN_EMPRESA")
        MembresiaEmpresa.objects.create(empresa=self.empresa_b, usuario=self.admin_b, rol="ADMIN_EMPRESA")
        MembresiaEmpresa.objects.create(empresa=self.empresa_a, usuario=self.planner_a, rol="WEDDING_PLANNER")
        MembresiaEmpresa.objects.create(empresa=self.empresa_b, usuario=self.planner_b, rol="WEDDING_PLANNER")
        MembresiaEmpresa.objects.create(empresa=self.empresa_a, usuario=self.cliente_a, rol="CLIENTE")
        MembresiaEmpresa.objects.create(empresa=self.empresa_a, usuario=self.proveedor_user, rol="PROVEEDOR")
        self.proveedor = Proveedor.objects.create(
            empresa=self.empresa_a,
            usuario=self.proveedor_user,
            nombre_comercial="Proveedor K94",
        )
        self.sede_a = SedeEvento.objects.create(empresa=self.empresa_a, nombre="Salon A", capacidad_minima=100, capacidad_maxima=350)
        self.sede_b = SedeEvento.objects.create(empresa=self.empresa_b, nombre="Salon B")
        self.evento_a = crear_evento(self.empresa_a, planner=self.planner_a, cliente=self.cliente_a, nombre="Evento A K94")
        self.evento_b = crear_evento(self.empresa_b, planner=self.planner_b, nombre="Evento B K94")
        self.paquete = PaqueteBoda.objects.create(
            empresa=self.empresa_a,
            nombre="Paquete 2",
            descripcion="Paquete comercial K9",
            precio_base=Decimal("99999.00"),
            precio_adulto=Decimal("1000.00"),
            precio_nino=Decimal("500.00"),
            cargo_fijo=Decimal("2500.00"),
            capacidad_minima_recomendada=200,
            capacidad_maxima_recomendada=350,
        )
        self.paquete_b = PaqueteBoda.objects.create(
            empresa=self.empresa_b,
            nombre="Paquete B",
            precio_adulto=Decimal("1.00"),
        )
        self.servicio = ServicioCatalogo.objects.create(
            empresa=self.empresa_a,
            nombre="Alcohol",
            categoria="BEBIDAS",
            unidad="PERSONA",
        )
        self.servicio_inactivo = ServicioCatalogo.objects.create(
            empresa=self.empresa_a,
            nombre="Servicio inactivo",
            categoria="OTRO",
            unidad="EVENTO",
            activo=False,
        )

    def url(self, name, empresa=None, *args):
        empresa = empresa or self.empresa_a
        return reverse(name, args=[empresa.slug, *args])

    def crear_propuesta(self, **kwargs):
        datos = {
            "empresa": self.empresa_a,
            "evento": self.evento_a,
            "sede": self.sede_a,
            "paquete": self.paquete,
            "adultos": 200,
            "ninos": 50,
            "descuento": Decimal("0.00"),
        }
        datos.update(kwargs)
        return PropuestaEvento.objects.create(**datos)

    def assert_fuera_de_media_root(self, path):
        archivo_path = Path(path).resolve()
        media_root = Path(settings.MEDIA_ROOT).resolve()
        private_root = Path(settings.PRIVATE_MEDIA_ROOT).resolve()
        self.assertNotIn(media_root, archivo_path.parents)
        self.assertTrue(archivo_path == private_root or private_root in archivo_path.parents)

    def test_base_adulto(self):
        propuesta = self.crear_propuesta(adultos=3, ninos=0)
        dto = calcular_propuesta(propuesta)
        self.assertEqual(dto["subtotal_base"], Decimal("5500.00"))

    def test_base_nino(self):
        propuesta = self.crear_propuesta(adultos=0, ninos=2)
        dto = calcular_propuesta(propuesta)
        self.assertEqual(dto["subtotal_base"], Decimal("3500.00"))

    def test_cargo_fijo(self):
        propuesta = self.crear_propuesta(adultos=0, ninos=0)
        dto = calcular_propuesta(propuesta)
        self.assertEqual(dto["subtotal_base"], Decimal("2500.00"))

    def test_combinacion_adulto_nino_fijo(self):
        propuesta = self.crear_propuesta(adultos=10, ninos=4)
        dto = calcular_propuesta(propuesta)
        self.assertEqual(dto["subtotal_base"], Decimal("14500.00"))

    def test_paquete_sin_tarifa_nino_genera_advertencia(self):
        self.paquete.precio_nino = None
        self.paquete.save(update_fields=["precio_nino"])
        propuesta = self.crear_propuesta(ninos=10)
        dto = calcular_propuesta(propuesta)
        self.assertIn("Tarifa de ninos no configurada; ninos no suman al subtotal base.", dto["advertencias"])

    def test_capacidad_minima_genera_advertencia(self):
        propuesta = self.crear_propuesta(adultos=50, ninos=10)
        dto = calcular_propuesta(propuesta)
        self.assertTrue(any("debajo de lo recomendado" in item for item in dto["advertencias"]))

    def test_capacidad_maxima_genera_advertencia(self):
        propuesta = self.crear_propuesta(adultos=370, ninos=0)
        dto = calcular_propuesta(propuesta)
        self.assertTrue(any("encima de lo recomendado" in item for item in dto["advertencias"]))

    def test_capacidad_no_bloquea_guardado(self):
        propuesta = self.crear_propuesta(adultos=370, ninos=0)
        dto = actualizar_totales_propuesta(propuesta)
        propuesta.refresh_from_db()
        self.assertEqual(propuesta.total, dto["total"])
        self.assertTrue(PropuestaEvento.objects.filter(pk=propuesta.pk).exists())

    def test_adicional_fijo(self):
        propuesta = self.crear_propuesta(adultos=0, ninos=0)
        PropuestaLinea.objects.create(propuesta=propuesta, tipo="ADICIONAL", nombre="Banda", modo_precio="FIJO", tarifa=1000)
        dto = actualizar_totales_propuesta(propuesta)
        self.assertEqual(dto["lineas_adicionales"][0]["subtotal"], "1000.00")

    def test_adicional_por_adulto(self):
        propuesta = self.crear_propuesta(adultos=4, ninos=0)
        PropuestaLinea.objects.create(propuesta=propuesta, tipo="ADICIONAL", nombre="Coctel", modo_precio="POR_ADULTO", tarifa=100)
        dto = actualizar_totales_propuesta(propuesta)
        self.assertEqual(dto["lineas_adicionales"][0]["subtotal"], "400.00")

    def test_adicional_por_nino(self):
        propuesta = self.crear_propuesta(adultos=0, ninos=3)
        PropuestaLinea.objects.create(propuesta=propuesta, tipo="ADICIONAL", nombre="Menu infantil", modo_precio="POR_NINO", tarifa=80)
        dto = actualizar_totales_propuesta(propuesta)
        self.assertEqual(dto["lineas_adicionales"][0]["subtotal"], "240.00")

    def test_adicional_por_persona(self):
        propuesta = self.crear_propuesta(adultos=4, ninos=3)
        PropuestaLinea.objects.create(propuesta=propuesta, tipo="ADICIONAL", nombre="Alcohol", modo_precio="POR_PERSONA", tarifa=450)
        dto = actualizar_totales_propuesta(propuesta)
        self.assertEqual(dto["lineas_adicionales"][0]["subtotal"], "3150.00")

    def test_adicional_por_unidad(self):
        propuesta = self.crear_propuesta()
        PropuestaLinea.objects.create(propuesta=propuesta, tipo="ADICIONAL", nombre="Mesa de postres", modo_precio="POR_UNIDAD", tarifa=1200, cantidad=2)
        dto = actualizar_totales_propuesta(propuesta)
        self.assertEqual(dto["lineas_adicionales"][0]["subtotal"], "2400.00")

    def test_adicional_manual(self):
        propuesta = self.crear_propuesta()
        PropuestaLinea.objects.create(propuesta=propuesta, tipo="ADICIONAL", nombre="Show especial", modo_precio="MANUAL", tarifa=9000, cantidad=1)
        dto = actualizar_totales_propuesta(propuesta)
        self.assertEqual(dto["lineas_adicionales"][0]["origen"], "MANUAL")
        self.assertEqual(dto["lineas_adicionales"][0]["subtotal"], "9000.00")

    def test_adicional_manual_sin_catalogo(self):
        propuesta = self.crear_propuesta()
        linea = PropuestaLinea.objects.create(
            propuesta=propuesta,
            tipo="ADICIONAL",
            nombre="Servicio solicitado por cliente",
            modo_precio="FIJO",
            tarifa=1500,
        )
        self.assertIsNone(linea.servicio_catalogo_id)

    def test_cortesia_cobra_cero(self):
        propuesta = self.crear_propuesta()
        PropuestaLinea.objects.create(
            propuesta=propuesta,
            tipo="CORTESIA",
            nombre="Letras Hollywood",
            modo_precio="FIJO",
            tarifa=5000,
            valor_informativo=5000,
        )
        dto = actualizar_totales_propuesta(propuesta)
        self.assertEqual(dto["lineas_cortesia"][0]["subtotal"], "0.00")

    def test_cortesia_sigue_visible(self):
        propuesta = self.crear_propuesta()
        PropuestaLinea.objects.create(propuesta=propuesta, tipo="CORTESIA", nombre="Camara 360", tarifa=3000)
        dto = calcular_propuesta(propuesta)
        self.assertEqual(dto["lineas_cortesia"][0]["nombre"], "Camara 360")

    def test_descuento_correcto(self):
        propuesta = self.crear_propuesta(adultos=1, ninos=0, descuento=Decimal("500.00"))
        dto = calcular_propuesta(propuesta)
        self.assertEqual(dto["total"], Decimal("3000.00"))

    def test_descuento_no_deja_total_negativo(self):
        propuesta = self.crear_propuesta(adultos=0, ninos=0, descuento=Decimal("99999.00"))
        dto = calcular_propuesta(propuesta)
        self.assertEqual(dto["total"], Decimal("0.00"))
        self.assertTrue(any("total se ajusto a cero" in item for item in dto["advertencias"]))

    def test_decimal_sin_error_float(self):
        self.paquete.precio_adulto = Decimal("0.10")
        self.paquete.precio_nino = Decimal("0.20")
        self.paquete.cargo_fijo = Decimal("0.30")
        self.paquete.save(update_fields=["precio_adulto", "precio_nino", "cargo_fijo"])
        propuesta = self.crear_propuesta(adultos=3, ninos=2)
        dto = calcular_propuesta(propuesta)
        self.assertEqual(dto["subtotal_base"], Decimal("1.00"))

    def test_dto_contiene_desglose_normalizado(self):
        propuesta = self.crear_propuesta()
        dto = calcular_propuesta(propuesta)
        for key in [
            "evento_id",
            "empresa_id",
            "sede",
            "adultos",
            "ninos",
            "paquete",
            "subtotal_base",
            "lineas_incluidas",
            "lineas_adicionales",
            "lineas_cortesia",
            "descuento",
            "subtotal",
            "total",
            "advertencias",
            "version_calculo",
        ]:
            self.assertIn(key, dto)

    def test_empresa_a_no_ve_propuesta_b(self):
        propuesta_b = PropuestaEvento.objects.create(
            empresa=self.empresa_b,
            evento=self.evento_b,
            sede=self.sede_b,
            paquete=self.paquete_b,
            adultos=1,
        )
        self.client.force_login(self.admin_a)
        response = self.client.get(self.url("paquetes_propuesta_editor", self.empresa_a, self.evento_b.id, propuesta_b.id))
        self.assertEqual(response.status_code, 404)

    def test_empresa_a_no_usa_paquete_b(self):
        self.client.force_login(self.admin_a)
        response = self.client.post(
            self.url("paquetes_propuesta_nueva", self.empresa_a, self.evento_a.id),
            {
                "accion": "guardar_propuesta",
                "sede": self.sede_a.id,
                "adultos": "100",
                "ninos": "0",
                "paquete": self.paquete_b.id,
                "descuento": "0",
                "estado": "BORRADOR",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(PropuestaEvento.objects.filter(evento=self.evento_a, paquete=self.paquete_b).exists())

    def test_planner_no_usa_evento_no_asignado(self):
        evento = crear_evento(self.empresa_a, nombre="Evento sin planner K94")
        self.client.force_login(self.planner_a)
        response = self.client.get(self.url("paquetes_propuesta_nueva", self.empresa_a, evento.id))
        self.assertEqual(response.status_code, 403)

    def test_cliente_no_administra(self):
        self.client.force_login(self.cliente_a)
        response = self.client.get(self.url("paquetes_propuesta_nueva", self.empresa_a, self.evento_a.id))
        self.assertEqual(response.status_code, 403)

    def test_proveedor_no_administra(self):
        self.client.force_login(self.proveedor_user)
        response = self.client.get(self.url("paquetes_propuesta_nueva", self.empresa_a, self.evento_a.id))
        self.assertEqual(response.status_code, 403)

    def test_post_no_fuerza_tenant(self):
        self.client.force_login(self.admin_a)
        response = self.client.post(
            self.url("paquetes_propuesta_nueva", self.empresa_a, self.evento_a.id),
            {
                "accion": "guardar_propuesta",
                "empresa": self.empresa_b.id,
                "empresa_id": self.empresa_b.id,
                "sede": self.sede_a.id,
                "adultos": "100",
                "ninos": "0",
                "paquete": self.paquete.id,
                "descuento": "0",
                "estado": "BORRADOR",
            },
        )
        self.assertEqual(response.status_code, 302)
        propuesta = PropuestaEvento.objects.get(evento=self.evento_a)
        self.assertEqual(propuesta.empresa, self.empresa_a)

    def test_paquete_inactivo_no_seleccionable_para_nueva_propuesta(self):
        self.paquete.activo = False
        self.paquete.save(update_fields=["activo"])
        self.client.force_login(self.admin_a)
        response = self.client.post(
            self.url("paquetes_propuesta_nueva", self.empresa_a, self.evento_a.id),
            {
                "accion": "guardar_propuesta",
                "sede": self.sede_a.id,
                "adultos": "100",
                "ninos": "0",
                "paquete": self.paquete.id,
                "descuento": "0",
                "estado": "BORRADOR",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(PropuestaEvento.objects.filter(evento=self.evento_a).exists())

    def test_servicio_catalogo_inactivo_no_se_agrega_como_nueva_linea(self):
        propuesta = self.crear_propuesta()
        self.client.force_login(self.admin_a)
        response = self.client.post(
            self.url("paquetes_propuesta_editor", self.empresa_a, self.evento_a.id, propuesta.id),
            {
                "accion": "agregar_linea",
                "tipo": "ADICIONAL",
                "servicio_catalogo": self.servicio_inactivo.id,
                "nombre": "",
                "modo_precio": "FIJO",
                "tarifa": "100",
                "cantidad": "1",
                "valor_informativo": "0",
                "orden": "0",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(PropuestaLinea.objects.filter(propuesta=propuesta).exists())

    def test_modificar_paquete_maestro_no_corrompe_desglose_persistido(self):
        propuesta = self.crear_propuesta()
        actualizar_totales_propuesta(propuesta)
        propuesta.refresh_from_db()
        total_guardado = propuesta.desglose_calculado["total"]
        self.paquete.precio_adulto = Decimal("9999.00")
        self.paquete.save(update_fields=["precio_adulto"])
        propuesta.refresh_from_db()
        self.assertEqual(propuesta.desglose_calculado["total"], total_guardado)

    def test_legacy_paqueteboda_sigue_funcionando(self):
        legacy = PaqueteBoda.objects.create(
            empresa=self.empresa_a,
            nombre="Legacy",
            precio_base=Decimal("50000.00"),
            numero_personas_incluidas=100,
        )
        self.assertEqual(legacy.precio_base, Decimal("50000.00"))
        self.assertIsNone(legacy.precio_adulto)

    def test_legacy_serviciopaquete_sigue_funcionando(self):
        legacy = ServicioPaquete.objects.create(
            paquete=self.paquete,
            tipo_servicio="DJ",
            descripcion="DJ legacy",
            cantidad=1,
            precio_incluido=Decimal("1000.00"),
        )
        propuesta = self.crear_propuesta()
        dto = calcular_propuesta(propuesta)
        self.assertTrue(any(item["clave_origen"] == f"legacy:{legacy.id}" for item in dto["lineas_incluidas"]))

    def test_k8_snapshot_sigue_pasando(self):
        ServicioPaquete.objects.create(
            paquete=self.paquete,
            tipo_servicio="DJ",
            descripcion="DJ legacy",
            cantidad=1,
            precio_incluido=Decimal("1000.00"),
        )
        paquete_evento = PaqueteEvento.objects.create(
            evento=self.evento_a,
            paquete=self.paquete,
            precio_acordado=Decimal("52000.00"),
            descuento=Decimal("2000.00"),
            estado="CONTRATADO",
        )
        snapshot = capturar_snapshot_paquete(paquete_evento)
        self.assertEqual(snapshot["nombre"], "Paquete 2")
        self.assertEqual(snapshot["total"], "50000.00")

    def test_paquete_servicio_rechaza_cross_tenant(self):
        servicio_b = ServicioCatalogo.objects.create(empresa=self.empresa_b, nombre="Servicio B", categoria="OTRO", unidad="EVENTO")
        relacion = PaqueteServicio(paquete=self.paquete, servicio_catalogo=servicio_b)
        with self.assertRaises(ValidationError):
            relacion.full_clean()

    def test_media_privada_paquete_fuera_de_media_root(self):
        self.client.force_login(self.admin_a)
        response = self.client.post(
            self.url("paquetes_paquete_create"),
            {
                "nombre": "Con media",
                "descripcion": "",
                "precio_base": "0",
                "numero_personas_incluidas": "0",
                "precio_adulto": "100",
                "precio_nino": "",
                "cargo_fijo": "0",
                "capacidad_minima_recomendada": "",
                "capacidad_maxima_recomendada": "",
                "duracion_evento": "",
                "activo": "on",
                "portada": archivo("portada.jpg", b"fake", "image/jpeg"),
                "pdf_comercial": archivo("ficha.pdf", b"%PDF-1.4 test", "application/pdf"),
            },
        )
        self.assertEqual(response.status_code, 302)
        paquete = PaqueteBoda.objects.get(nombre="Con media")
        self.assert_fuera_de_media_root(paquete.portada.path)
        self.assert_fuera_de_media_root(paquete.pdf_comercial.path)
        with self.assertRaises(ValueError):
            _ = paquete.portada.url

    def test_media_privada_paquete_descarga_autorizada_y_cross_tenant_no(self):
        paquete = PaqueteBoda.objects.create(
            empresa=self.empresa_a,
            nombre="Media privada",
            portada=archivo("privada.jpg", b"fake", "image/jpeg"),
        )
        self.client.force_login(self.admin_a)
        response = self.client.get(self.url("paquetes_paquete_portada", self.empresa_a, paquete.id))
        self.assertEqual(response.status_code, 200)
        self.client.force_login(self.admin_b)
        response = self.client.get(self.url("paquetes_paquete_portada", self.empresa_a, paquete.id))
        self.assertEqual(response.status_code, 404)
