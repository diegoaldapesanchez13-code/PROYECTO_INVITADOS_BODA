from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from invitaciones.models import EventoBoda
from organizaciones.models import EmpresaSuscriptora, MembresiaEmpresa
from proveedores.models import Proveedor, ServicioCatalogoProveedor, ServicioEvento

from .models import ProveedorServicioCatalogo, ServicioCatalogo
from .services import proveedores_disponibles_para_servicio, servicios_disponibles_para_proveedor


class ProveedorServicioCatalogoK93Tests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.empresa_a = EmpresaSuscriptora.objects.create(nombre_comercial="Empresa A K93", slug="empresa-a-k93")
        self.empresa_b = EmpresaSuscriptora.objects.create(nombre_comercial="Empresa B K93", slug="empresa-b-k93")
        self.admin_a = User.objects.create_user(username="admin-a-k93", password="test123")
        self.admin_b = User.objects.create_user(username="admin-b-k93", password="test123")
        self.planner_a = User.objects.create_user(username="planner-a-k93", password="test123")
        self.cliente_a = User.objects.create_user(username="cliente-a-k93", password="test123")
        self.proveedor_user_a = User.objects.create_user(username="proveedor-a-k93", password="test123")
        self.dirtec = User.objects.create_superuser(username="dirtec-k93", email="dirtec-k93@example.com", password="test123")
        MembresiaEmpresa.objects.create(empresa=self.empresa_a, usuario=self.admin_a, rol="ADMIN_EMPRESA")
        MembresiaEmpresa.objects.create(empresa=self.empresa_b, usuario=self.admin_b, rol="ADMIN_EMPRESA")
        MembresiaEmpresa.objects.create(empresa=self.empresa_a, usuario=self.planner_a, rol="WEDDING_PLANNER")
        MembresiaEmpresa.objects.create(empresa=self.empresa_a, usuario=self.cliente_a, rol="CLIENTE")
        self.proveedor_a = Proveedor.objects.create(
            empresa=self.empresa_a,
            usuario=self.proveedor_user_a,
            nombre_comercial="Proveedor A K93",
            tipo_proveedor="DJ",
        )
        self.proveedor_a2 = Proveedor.objects.create(
            empresa=self.empresa_a,
            nombre_comercial="Proveedor A2 K93",
            tipo_proveedor="BANQUETE",
        )
        self.proveedor_b = Proveedor.objects.create(
            empresa=self.empresa_b,
            nombre_comercial="Proveedor B K93",
            tipo_proveedor="DECORACION",
        )
        self.servicio_a = ServicioCatalogo.objects.create(
            empresa=self.empresa_a,
            nombre="DJ de lujo",
            categoria="MUSICA",
            unidad="EVENTO",
        )
        self.servicio_a2 = ServicioCatalogo.objects.create(
            empresa=self.empresa_a,
            nombre="Banquete 2",
            categoria="BANQUETE",
            unidad="PERSONA",
        )
        self.servicio_b = ServicioCatalogo.objects.create(
            empresa=self.empresa_b,
            nombre="Decoracion B",
            categoria="DECORACION",
            unidad="EVENTO",
        )

    def url(self, name, empresa=None, proveedor=None, *args):
        empresa = empresa or self.empresa_a
        proveedor = proveedor or self.proveedor_a
        return reverse(name, args=[empresa.slug, proveedor.id, *args])

    def crear_relacion(self, proveedor=None, servicio=None, **kwargs):
        return ProveedorServicioCatalogo.objects.create(
            proveedor=proveedor or self.proveedor_a,
            servicio_catalogo=servicio or self.servicio_a,
            **kwargs,
        )

    def test_relacion_proveedor_servicio_valida(self):
        relacion = self.crear_relacion(notas="Puede operar montaje nocturno.")
        self.assertEqual(relacion.proveedor, self.proveedor_a)
        self.assertEqual(relacion.servicio_catalogo, self.servicio_a)
        self.assertTrue(relacion.activo)

    def test_relacion_duplicada_rechazada(self):
        self.crear_relacion()
        with self.assertRaises(ValidationError):
            self.crear_relacion()

    def test_relacion_cross_tenant_rechazada(self):
        with self.assertRaises(ValidationError):
            self.crear_relacion(proveedor=self.proveedor_a, servicio=self.servicio_b)

    def test_proveedor_sin_empresa_rechazado(self):
        proveedor_legacy = Proveedor.objects.create(nombre_comercial="Proveedor legacy sin tenant")
        with self.assertRaises(ValidationError):
            self.crear_relacion(proveedor=proveedor_legacy, servicio=self.servicio_a)

    def test_relacion_inactiva_se_conserva(self):
        relacion = self.crear_relacion(activo=False)
        self.assertFalse(relacion.activo)
        self.assertTrue(ProveedorServicioCatalogo.objects.filter(pk=relacion.pk).exists())

    def test_proveedor_ofrece_multiples_servicios(self):
        self.crear_relacion(servicio=self.servicio_a)
        self.crear_relacion(servicio=self.servicio_a2)
        self.assertEqual(self.proveedor_a.servicios_catalogo_k9.count(), 2)

    def test_servicio_tiene_multiples_proveedores(self):
        self.crear_relacion(proveedor=self.proveedor_a, servicio=self.servicio_a)
        self.crear_relacion(proveedor=self.proveedor_a2, servicio=self.servicio_a)
        self.assertEqual(self.servicio_a.proveedores_servicio_catalogo.count(), 2)

    def test_empresa_gestiona_servicios_de_proveedor(self):
        self.client.force_login(self.admin_a)
        response = self.client.post(
            self.url("catalogo_proveedor_servicios"),
            {"servicios": [str(self.servicio_a.id), str(self.servicio_a2.id)], "notas": "Preferente"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.proveedor_a.servicios_catalogo_k9.filter(activo=True).count(), 2)

    def test_empresa_solo_ve_relaciones_propias(self):
        self.crear_relacion()
        ProveedorServicioCatalogo.objects.create(proveedor=self.proveedor_b, servicio_catalogo=self.servicio_b)
        self.client.force_login(self.admin_a)
        response = self.client.get(self.url("catalogo_proveedor_servicios"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "DJ de lujo")
        self.assertNotContains(response, "Decoracion B")

    def test_post_manipulado_cross_tenant_falla(self):
        self.client.force_login(self.admin_a)
        response = self.client.post(
            self.url("catalogo_proveedor_servicios"),
            {"servicios": [str(self.servicio_b.id)], "notas": "Ataque"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(ProveedorServicioCatalogo.objects.filter(proveedor=self.proveedor_a, servicio_catalogo=self.servicio_b).exists())

    def test_empresa_a_manipula_proveedor_id_b_falla(self):
        self.client.force_login(self.admin_a)
        response = self.client.post(
            self.url("catalogo_proveedor_servicios", self.empresa_a, self.proveedor_b),
            {"servicios": [str(self.servicio_a.id)], "notas": "Ataque proveedor"},
        )
        self.assertEqual(response.status_code, 404)
        self.assertFalse(ProveedorServicioCatalogo.objects.filter(proveedor=self.proveedor_b, servicio_catalogo=self.servicio_a).exists())

    def test_empresa_b_no_ve_relaciones_de_empresa_a(self):
        self.crear_relacion()
        self.client.force_login(self.admin_b)
        response = self.client.get(self.url("catalogo_proveedor_servicios", self.empresa_a, self.proveedor_a))
        self.assertEqual(response.status_code, 404)

    def test_planner_mismo_tenant_lee(self):
        self.crear_relacion()
        self.client.force_login(self.planner_a)
        response = self.client.get(self.url("catalogo_proveedor_servicios"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "DJ de lujo")
        self.assertNotContains(response, "Asociar servicios")

    def test_planner_no_gestiona(self):
        self.client.force_login(self.planner_a)
        response = self.client.post(
            self.url("catalogo_proveedor_servicios"),
            {"servicios": [str(self.servicio_a.id)]},
        )
        self.assertEqual(response.status_code, 403)
        self.assertFalse(ProveedorServicioCatalogo.objects.exists())

    def test_planner_no_cambia_estado_relacion(self):
        relacion = self.crear_relacion()
        self.client.force_login(self.planner_a)
        response = self.client.post(self.url("catalogo_proveedor_servicio_toggle", self.empresa_a, self.proveedor_a, relacion.id))
        self.assertEqual(response.status_code, 403)
        relacion.refresh_from_db()
        self.assertTrue(relacion.activo)

    def test_planner_otro_tenant_falla(self):
        self.client.force_login(self.planner_a)
        response = self.client.get(self.url("catalogo_proveedor_servicios", self.empresa_b, self.proveedor_b))
        self.assertEqual(response.status_code, 404)

    def test_cliente_no_administra(self):
        self.client.force_login(self.cliente_a)
        response = self.client.get(self.url("catalogo_proveedor_servicios"))
        self.assertEqual(response.status_code, 403)

    def test_cliente_post_manual_no_administra(self):
        self.client.force_login(self.cliente_a)
        response = self.client.post(
            self.url("catalogo_proveedor_servicios"),
            {"servicios": [str(self.servicio_a.id)]},
        )
        self.assertEqual(response.status_code, 403)
        self.assertFalse(ProveedorServicioCatalogo.objects.exists())

    def test_proveedor_no_administra(self):
        self.client.force_login(self.proveedor_user_a)
        response = self.client.get(self.url("catalogo_proveedor_servicios"))
        self.assertEqual(response.status_code, 403)

    def test_proveedor_post_manual_no_administra(self):
        self.client.force_login(self.proveedor_user_a)
        response = self.client.post(
            self.url("catalogo_proveedor_servicios"),
            {"servicios": [str(self.servicio_a.id)]},
        )
        self.assertEqual(response.status_code, 403)
        self.assertFalse(ProveedorServicioCatalogo.objects.exists())

    def test_dirtec_autorizado(self):
        self.crear_relacion()
        self.client.force_login(self.dirtec)
        response = self.client.get(self.url("catalogo_proveedor_servicios"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "DJ de lujo")

    def test_desactivar_relacion_no_elimina(self):
        relacion = self.crear_relacion()
        self.client.force_login(self.admin_a)
        response = self.client.post(self.url("catalogo_proveedor_servicio_toggle", self.empresa_a, self.proveedor_a, relacion.id))
        self.assertEqual(response.status_code, 302)
        relacion.refresh_from_db()
        self.assertFalse(relacion.activo)
        self.assertTrue(ProveedorServicioCatalogo.objects.filter(pk=relacion.pk).exists())

    def test_agregar_servicio_desactivado_reactiva_relacion_existente(self):
        relacion = self.crear_relacion(activo=False, notas="Anterior")
        self.client.force_login(self.admin_a)
        response = self.client.post(
            self.url("catalogo_proveedor_servicios"),
            {"servicios": [str(self.servicio_a.id)], "notas": "Reactivado"},
        )
        self.assertEqual(response.status_code, 302)
        relacion.refresh_from_db()
        self.assertTrue(relacion.activo)
        self.assertEqual(relacion.notas, "Reactivado")
        self.assertEqual(
            ProveedorServicioCatalogo.objects.filter(
                proveedor=self.proveedor_a,
                servicio_catalogo=self.servicio_a,
            ).count(),
            1,
        )

    def test_helper_solo_proveedores_activos_y_relaciones_activas(self):
        self.crear_relacion(proveedor=self.proveedor_a, servicio=self.servicio_a)
        self.crear_relacion(proveedor=self.proveedor_a2, servicio=self.servicio_a, activo=False)
        proveedor_inactivo = Proveedor.objects.create(
            empresa=self.empresa_a,
            nombre_comercial="Proveedor inactivo K93",
            activo=False,
        )
        self.crear_relacion(proveedor=proveedor_inactivo, servicio=self.servicio_a)
        relaciones = proveedores_disponibles_para_servicio(self.servicio_a)
        self.assertEqual(list(relaciones.values_list("proveedor_id", flat=True)), [self.proveedor_a.id])

    def test_helper_solo_servicios_activos_y_mismo_tenant(self):
        self.crear_relacion(proveedor=self.proveedor_a, servicio=self.servicio_a)
        servicio_inactivo = ServicioCatalogo.objects.create(
            empresa=self.empresa_a,
            nombre="Servicio inactivo",
            categoria="OTRO",
            unidad="EVENTO",
            activo=False,
        )
        self.crear_relacion(proveedor=self.proveedor_a, servicio=servicio_inactivo)
        servicios = servicios_disponibles_para_proveedor(self.proveedor_a)
        self.assertEqual(list(servicios), [self.servicio_a])

    def test_servicio_detalle_muestra_proveedores_autorizados(self):
        self.crear_relacion()
        self.client.force_login(self.planner_a)
        response = self.client.get(reverse("catalogo_servicio_detail", args=[self.empresa_a.slug, self.servicio_a.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Proveedor A K93")

    def test_servicio_catalogo_proveedor_legacy_sigue_funcionando(self):
        legacy = ServicioCatalogoProveedor.objects.create(
            empresa=self.empresa_a,
            proveedor=self.proveedor_a,
            nombre="Legacy decoracion",
            descripcion="Con costo de referencia",
            categoria="DECORACION",
            costo_referencia=100,
            precio_referencia_cliente=150,
        )
        self.assertEqual(legacy.costo_referencia, 100)
        self.assertEqual(legacy.precio_referencia_cliente, 150)

    def test_tipo_proveedor_legacy_sigue_funcionando(self):
        self.assertEqual(self.proveedor_a.tipo_proveedor, "DJ")
        self.assertEqual(self.proveedor_a.get_tipo_proveedor_display(), "DJ")

    def test_servicio_evento_actual_no_se_rompe(self):
        now = timezone.now()
        evento = EventoBoda.objects.create(
            empresa=self.empresa_a,
            nombre_evento="Evento K93",
            novio="A",
            novia="B",
            frase_portada="x",
            mensaje_general="x",
            fecha_misa=now,
            lugar_misa="x",
            fecha_fiesta=now,
            lugar_fiesta="x",
        )
        legacy = ServicioCatalogoProveedor.objects.create(
            empresa=self.empresa_a,
            proveedor=self.proveedor_a,
            nombre="Legacy DJ",
        )
        servicio_evento = ServicioEvento(
            evento=evento,
            proveedor=self.proveedor_a,
            servicio_catalogo=legacy,
            nombre_servicio="DJ evento",
            origen="CATALOGO",
        )
        servicio_evento.full_clean()
