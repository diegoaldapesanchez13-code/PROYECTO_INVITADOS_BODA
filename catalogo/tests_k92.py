from datetime import timedelta
from pathlib import Path

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from organizaciones.models import EmpresaSuscriptora, MembresiaEmpresa
from suscripciones.models import PlanSuscripcion, SuscripcionEmpresa

from .models import ServicioCatalogo, ServicioCatalogoArchivo


def archivo(nombre, contenido=b"test", content_type="application/octet-stream"):
    return SimpleUploadedFile(nombre, contenido, content_type=content_type)


@override_settings(
    MEDIA_ROOT="media/test/k92_catalogo/public",
    PRIVATE_MEDIA_ROOT="media/test/k92_catalogo/private",
)
class ServicioCatalogoK92Tests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.empresa_a = EmpresaSuscriptora.objects.create(nombre_comercial="Empresa A K92", slug="empresa-a-k92")
        self.empresa_b = EmpresaSuscriptora.objects.create(nombre_comercial="Empresa B K92", slug="empresa-b-k92")
        self.admin_a = User.objects.create_user(username="admin-a-k92", password="test123")
        self.admin_b = User.objects.create_user(username="admin-b-k92", password="test123")
        self.dirtec = User.objects.create_superuser(username="dirtec-k92", email="dirtec@example.com", password="test123")
        self.planner_a = User.objects.create_user(username="planner-a-k92", password="test123")
        self.cliente_a = User.objects.create_user(username="cliente-a-k92", password="test123")
        self.proveedor_a = User.objects.create_user(username="proveedor-a-k92", password="test123")
        MembresiaEmpresa.objects.create(empresa=self.empresa_a, usuario=self.admin_a, rol="ADMIN_EMPRESA")
        MembresiaEmpresa.objects.create(empresa=self.empresa_b, usuario=self.admin_b, rol="ADMIN_EMPRESA")
        MembresiaEmpresa.objects.create(empresa=self.empresa_a, usuario=self.planner_a, rol="WEDDING_PLANNER")
        MembresiaEmpresa.objects.create(empresa=self.empresa_a, usuario=self.cliente_a, rol="CLIENTE")
        MembresiaEmpresa.objects.create(empresa=self.empresa_a, usuario=self.proveedor_a, rol="PROVEEDOR")

    def url(self, name, empresa=None, *args):
        empresa = empresa or self.empresa_a
        return reverse(name, args=[empresa.slug, *args])

    def crear_servicio(self, empresa=None, nombre="DJ de lujo", **kwargs):
        empresa = empresa or self.empresa_a
        datos = {
            "empresa": empresa,
            "nombre": nombre,
            "categoria": "MUSICA",
            "unidad": "EVENTO",
            "descripcion": "Servicio descriptivo sin precio.",
        }
        datos.update(kwargs)
        return ServicioCatalogo.objects.create(**datos)

    def assert_fuera_de_media_root(self, path):
        archivo_path = Path(path).resolve()
        media_root = Path(settings.MEDIA_ROOT).resolve()
        private_root = Path(settings.PRIVATE_MEDIA_ROOT).resolve()
        self.assertNotEqual(archivo_path, media_root)
        self.assertNotIn(media_root, archivo_path.parents)
        self.assertTrue(archivo_path == private_root or private_root in archivo_path.parents)

    def test_servicio_catalogo_creacion(self):
        servicio = self.crear_servicio()
        self.assertEqual(servicio.empresa, self.empresa_a)
        self.assertEqual(servicio.categoria, "MUSICA")
        self.assertTrue(servicio.activo)

    def test_servicio_catalogo_empresa_obligatoria(self):
        servicio = ServicioCatalogo(nombre="Sin tenant", categoria="OTRO", unidad="EVENTO")
        with self.assertRaises(ValidationError):
            servicio.full_clean()

    def test_servicio_catalogo_inactivo_se_conserva(self):
        servicio = self.crear_servicio(activo=False)
        self.assertFalse(servicio.activo)
        self.assertTrue(ServicioCatalogo.objects.filter(pk=servicio.pk).exists())

    def test_mismo_nombre_permitido_en_empresas_distintas(self):
        self.crear_servicio(self.empresa_a, nombre="Camara 360")
        servicio_b = ServicioCatalogo(empresa=self.empresa_b, nombre="Camara 360", categoria="OTRO", unidad="EVENTO")
        servicio_b.full_clean()
        servicio_b.save()
        self.assertEqual(ServicioCatalogo.objects.filter(nombre="Camara 360").count(), 2)

    def test_nombre_duplicado_misma_empresa_se_rechaza(self):
        self.crear_servicio(self.empresa_a, nombre="Mesa de postres")
        duplicado = ServicioCatalogo(
            empresa=self.empresa_a,
            nombre="mesa de postres",
            categoria="BANQUETE",
            unidad="EVENTO",
        )
        with self.assertRaises(ValidationError):
            duplicado.full_clean()

    def test_nombre_duplicado_con_espacios_se_rechaza(self):
        self.crear_servicio(self.empresa_a, nombre="DJ de lujo")
        duplicado = ServicioCatalogo(
            empresa=self.empresa_a,
            nombre="  DJ DE LUJO  ",
            categoria="MUSICA",
            unidad="EVENTO",
        )
        with self.assertRaises(ValidationError):
            duplicado.full_clean()

    def test_nombre_se_guarda_sin_espacios_externos(self):
        servicio = self.crear_servicio(nombre="  Valet parking  ")
        self.assertEqual(servicio.nombre, "Valet parking")

    def test_editar_mismo_registro_no_dispara_duplicado(self):
        servicio = self.crear_servicio(nombre="Carpa")
        servicio.descripcion = "Actualizacion sin cambiar nombre."
        servicio.full_clean()
        servicio.save()
        self.assertEqual(ServicioCatalogo.objects.filter(empresa=self.empresa_a, nombre="Carpa").count(), 1)

    def test_empresa_solo_lista_su_catalogo(self):
        self.crear_servicio(self.empresa_a, nombre="DJ A")
        self.crear_servicio(self.empresa_b, nombre="DJ B")
        self.client.force_login(self.admin_a)
        response = self.client.get(self.url("catalogo_servicio_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "DJ A")
        self.assertNotContains(response, "DJ B")

    def test_dirtec_navega_a_dashboard_dirtec(self):
        self.crear_servicio(self.empresa_a, nombre="Servicio DIRTEC")
        self.client.force_login(self.dirtec)
        response = self.client.get(self.url("catalogo_servicio_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse("dirtec_dashboard"))

    def test_empresa_no_detalla_servicio_otro_tenant(self):
        servicio_b = self.crear_servicio(self.empresa_b, nombre="Servicio B")
        self.client.force_login(self.admin_a)
        response = self.client.get(self.url("catalogo_servicio_detail", self.empresa_a, servicio_b.id))
        self.assertEqual(response.status_code, 404)

    def test_empresa_no_edita_servicio_otro_tenant(self):
        servicio_b = self.crear_servicio(self.empresa_b, nombre="Servicio B")
        self.client.force_login(self.admin_a)
        response = self.client.get(self.url("catalogo_servicio_update", self.empresa_a, servicio_b.id))
        self.assertEqual(response.status_code, 404)

    def test_empresa_no_desactiva_servicio_otro_tenant(self):
        servicio_b = self.crear_servicio(self.empresa_b, nombre="Servicio B")
        self.client.force_login(self.admin_a)
        response = self.client.post(self.url("catalogo_servicio_toggle", self.empresa_a, servicio_b.id))
        self.assertEqual(response.status_code, 404)
        servicio_b.refresh_from_db()
        self.assertTrue(servicio_b.activo)

    def test_planner_ve_catalogo_empresa_autorizada(self):
        self.crear_servicio(nombre="Decoracion floral")
        self.client.force_login(self.planner_a)
        response = self.client.get(self.url("catalogo_servicio_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Decoracion floral")
        self.assertContains(response, reverse("planner_dashboard_empresa", args=[self.empresa_a.slug]))

    def test_planner_no_ve_catalogo_otro_tenant(self):
        self.client.force_login(self.planner_a)
        response = self.client.get(self.url("catalogo_servicio_list", self.empresa_b))
        self.assertEqual(response.status_code, 404)

    def test_planner_no_crea_servicio_catalogo(self):
        self.client.force_login(self.planner_a)
        response = self.client.post(
            self.url("catalogo_servicio_create"),
            {
                "nombre": "Servicio planner",
                "categoria": "OTRO",
                "unidad": "EVENTO",
                "activo": "on",
            },
        )
        self.assertEqual(response.status_code, 403)
        self.assertFalse(ServicioCatalogo.objects.filter(nombre="Servicio planner").exists())

    def test_planner_no_edita_servicio_catalogo(self):
        servicio = self.crear_servicio(nombre="Audio")
        self.client.force_login(self.planner_a)
        response = self.client.post(
            self.url("catalogo_servicio_update", self.empresa_a, servicio.id),
            {
                "nombre": "Audio editado",
                "categoria": "AUDIO_ILUMINACION",
                "unidad": "EVENTO",
                "activo": "on",
            },
        )
        self.assertEqual(response.status_code, 403)
        servicio.refresh_from_db()
        self.assertEqual(servicio.nombre, "Audio")

    def test_planner_no_cambia_estado_servicio_catalogo(self):
        servicio = self.crear_servicio(nombre="Decoracion aerea")
        self.client.force_login(self.planner_a)
        response = self.client.post(self.url("catalogo_servicio_toggle", self.empresa_a, servicio.id))
        self.assertEqual(response.status_code, 403)
        servicio.refresh_from_db()
        self.assertTrue(servicio.activo)

    def test_planner_no_agrega_archivo_servicio_catalogo(self):
        servicio = self.crear_servicio(nombre="Mesa lounge")
        self.client.force_login(self.planner_a)
        response = self.client.post(
            self.url("catalogo_archivo_create", self.empresa_a, servicio.id),
            {
                "tipo": "PDF",
                "titulo": "Ficha",
                "orden": "1",
                "archivo": archivo("ficha.pdf", b"%PDF-1.4 test", "application/pdf"),
            },
        )
        self.assertEqual(response.status_code, 403)
        self.assertFalse(servicio.archivos.exists())

    def test_cliente_no_administra_catalogo(self):
        self.client.force_login(self.cliente_a)
        response = self.client.get(self.url("catalogo_servicio_create"))
        self.assertEqual(response.status_code, 403)

    def test_proveedor_no_administra_catalogo(self):
        self.client.force_login(self.proveedor_a)
        response = self.client.get(self.url("catalogo_servicio_create"))
        self.assertEqual(response.status_code, 403)

    def test_imagen_valida(self):
        self.client.force_login(self.admin_a)
        response = self.client.post(
            self.url("catalogo_servicio_create"),
            {
                "nombre": "Letras Hollywood",
                "categoria": "DECORACION",
                "unidad": "UNIDAD",
                "activo": "on",
                "imagen_principal": archivo("letras.jpg", b"fake-image", "image/jpeg"),
            },
        )
        self.assertEqual(response.status_code, 302)
        servicio = ServicioCatalogo.objects.get(nombre="Letras Hollywood")
        self.assertTrue(servicio.imagen_principal.name.endswith(".jpg"))
        self.assert_fuera_de_media_root(servicio.imagen_principal.path)

    def test_imagen_catalogo_no_tiene_url_media_publica(self):
        self.client.force_login(self.admin_a)
        response = self.client.post(
            self.url("catalogo_servicio_create"),
            {
                "nombre": "Carpa premium",
                "categoria": "DECORACION",
                "unidad": "EVENTO",
                "activo": "on",
                "imagen_principal": archivo("carpa.jpg", b"fake-image", "image/jpeg"),
            },
        )
        self.assertEqual(response.status_code, 302)
        servicio = ServicioCatalogo.objects.get(nombre="Carpa premium")
        self.assert_fuera_de_media_root(servicio.imagen_principal.path)
        with self.assertRaises(ValueError):
            _ = servicio.imagen_principal.url
        media_response = self.client.get(f"{settings.MEDIA_URL}{servicio.imagen_principal.name}")
        self.assertEqual(media_response.status_code, 404)

    def test_pdf_valido(self):
        servicio = self.crear_servicio()
        self.client.force_login(self.admin_a)
        response = self.client.post(
            self.url("catalogo_archivo_create", self.empresa_a, servicio.id),
            {
                "tipo": "PDF",
                "titulo": "Ficha comercial",
                "orden": "1",
                "archivo": archivo("ficha.pdf", b"%PDF-1.4 test", "application/pdf"),
            },
        )
        self.assertEqual(response.status_code, 302)
        adjunto = servicio.archivos.get(tipo="PDF")
        self.assert_fuera_de_media_root(adjunto.archivo.path)

    def test_archivo_catalogo_no_tiene_url_media_publica(self):
        servicio = self.crear_servicio()
        adjunto = ServicioCatalogoArchivo.objects.create(
            servicio=servicio,
            tipo="PDF",
            titulo="Ficha privada",
            archivo=archivo("ficha-privada.pdf", b"%PDF-1.4 test", "application/pdf"),
        )
        self.assert_fuera_de_media_root(adjunto.archivo.path)
        with self.assertRaises(ValueError):
            _ = adjunto.archivo.url
        media_response = self.client.get(f"{settings.MEDIA_URL}{adjunto.archivo.name}")
        self.assertEqual(media_response.status_code, 404)

    def test_extension_no_permitida_rechazada(self):
        servicio = self.crear_servicio()
        self.client.force_login(self.admin_a)
        response = self.client.post(
            self.url("catalogo_archivo_create", self.empresa_a, servicio.id),
            {
                "tipo": "IMAGEN",
                "titulo": "Archivo peligroso",
                "orden": "1",
                "archivo": archivo("script.exe", b"bad", "application/octet-stream"),
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertFalse(ServicioCatalogoArchivo.objects.filter(servicio=servicio).exists())

    def test_exe_renombrado_como_imagen_pasa_por_extension(self):
        self.client.force_login(self.admin_a)
        response = self.client.post(
            self.url("catalogo_servicio_create"),
            {
                "nombre": "Foto referencia",
                "categoria": "DECORACION",
                "unidad": "EVENTO",
                "activo": "on",
                "imagen_principal": archivo("referencia.jpg", b"MZ fake exe", "image/jpeg"),
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(ServicioCatalogo.objects.filter(nombre="Foto referencia").exists())

    def test_archivo_catalogo_autorizado_mismo_tenant(self):
        servicio = self.crear_servicio()
        adjunto = ServicioCatalogoArchivo.objects.create(
            servicio=servicio,
            tipo="PDF",
            titulo="Ficha interna",
            archivo=archivo("ficha-interna.pdf", b"%PDF-1.4 test", "application/pdf"),
        )
        self.client.force_login(self.admin_a)
        response = self.client.get(self.url("catalogo_archivo_download", self.empresa_a, servicio.id, adjunto.id))
        self.assertEqual(response.status_code, 200)

    def test_imagen_catalogo_autorizada_mismo_tenant(self):
        servicio = self.crear_servicio(
            nombre="Imagen privada",
            imagen_principal=archivo("imagen-privada.jpg", b"fake-image", "image/jpeg"),
        )
        self.client.force_login(self.admin_a)
        response = self.client.get(self.url("catalogo_servicio_imagen", self.empresa_a, servicio.id))
        self.assertEqual(response.status_code, 200)

    def test_planner_mismo_tenant_descarga_archivo_catalogo(self):
        servicio = self.crear_servicio()
        adjunto = ServicioCatalogoArchivo.objects.create(
            servicio=servicio,
            tipo="PDF",
            titulo="Ficha planner",
            archivo=archivo("ficha-planner.pdf", b"%PDF-1.4 test", "application/pdf"),
        )
        self.client.force_login(self.planner_a)
        response = self.client.get(self.url("catalogo_archivo_download", self.empresa_a, servicio.id, adjunto.id))
        self.assertEqual(response.status_code, 200)

    def test_archivo_catalogo_rechaza_otro_tenant(self):
        servicio = self.crear_servicio(self.empresa_a)
        adjunto = ServicioCatalogoArchivo.objects.create(
            servicio=servicio,
            tipo="PDF",
            titulo="Ficha interna",
            archivo=archivo("ficha-interna.pdf", b"%PDF-1.4 test", "application/pdf"),
        )
        self.client.force_login(self.admin_b)
        response = self.client.get(self.url("catalogo_archivo_download", self.empresa_a, servicio.id, adjunto.id))
        self.assertEqual(response.status_code, 404)

    def test_planner_otro_tenant_no_descarga_archivo_catalogo(self):
        servicio_b = self.crear_servicio(self.empresa_b)
        adjunto = ServicioCatalogoArchivo.objects.create(
            servicio=servicio_b,
            tipo="PDF",
            titulo="Ficha B",
            archivo=archivo("ficha-b.pdf", b"%PDF-1.4 test", "application/pdf"),
        )
        self.client.force_login(self.planner_a)
        response = self.client.get(self.url("catalogo_archivo_download", self.empresa_b, servicio_b.id, adjunto.id))
        self.assertEqual(response.status_code, 404)

    def test_cliente_no_descarga_archivo_catalogo(self):
        servicio = self.crear_servicio()
        adjunto = ServicioCatalogoArchivo.objects.create(
            servicio=servicio,
            tipo="PDF",
            titulo="Ficha cliente",
            archivo=archivo("ficha-cliente.pdf", b"%PDF-1.4 test", "application/pdf"),
        )
        self.client.force_login(self.cliente_a)
        response = self.client.get(self.url("catalogo_archivo_download", self.empresa_a, servicio.id, adjunto.id))
        self.assertEqual(response.status_code, 403)

    def test_proveedor_no_descarga_archivo_catalogo(self):
        servicio = self.crear_servicio()
        adjunto = ServicioCatalogoArchivo.objects.create(
            servicio=servicio,
            tipo="PDF",
            titulo="Ficha proveedor",
            archivo=archivo("ficha-proveedor.pdf", b"%PDF-1.4 test", "application/pdf"),
        )
        self.client.force_login(self.proveedor_a)
        response = self.client.get(self.url("catalogo_archivo_download", self.empresa_a, servicio.id, adjunto.id))
        self.assertEqual(response.status_code, 403)

    def test_empresa_suspendida_no_accede_catalogo(self):
        plan = PlanSuscripcion.objects.create(nombre="Plan suspendido K92")
        SuscripcionEmpresa.objects.create(
            empresa=self.empresa_a,
            plan=plan,
            fecha_vencimiento=timezone.localdate() + timedelta(days=30),
            estado="SUSPENDIDA",
        )
        self.client.force_login(self.admin_a)
        response = self.client.get(self.url("catalogo_servicio_list"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/suscripcion/estado/", response["Location"])

    def test_empresa_suspendida_no_escribe_catalogo(self):
        plan = PlanSuscripcion.objects.create(nombre="Plan suspendido escritura K92")
        SuscripcionEmpresa.objects.create(
            empresa=self.empresa_a,
            plan=plan,
            fecha_vencimiento=timezone.localdate() + timedelta(days=30),
            estado="SUSPENDIDA",
        )
        self.client.force_login(self.admin_a)
        response = self.client.post(
            self.url("catalogo_servicio_create"),
            {
                "nombre": "Bloqueado",
                "categoria": "OTRO",
                "unidad": "EVENTO",
                "activo": "on",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn("/suscripcion/estado/", response["Location"])
        self.assertFalse(ServicioCatalogo.objects.filter(nombre="Bloqueado").exists())

    def test_planner_empresa_suspendida_no_accede_catalogo(self):
        plan = PlanSuscripcion.objects.create(nombre="Plan suspendido planner K92")
        SuscripcionEmpresa.objects.create(
            empresa=self.empresa_a,
            plan=plan,
            fecha_vencimiento=timezone.localdate() + timedelta(days=30),
            estado="SUSPENDIDA",
        )
        self.client.force_login(self.planner_a)
        response = self.client.get(self.url("catalogo_servicio_list"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/suscripcion/estado/", response["Location"])

    def test_crear_servicio_asigna_empresa_desde_contexto(self):
        self.client.force_login(self.admin_a)
        response = self.client.post(
            self.url("catalogo_servicio_create"),
            {
                "empresa": str(self.empresa_b.id),
                "nombre": "Valet parking",
                "categoria": "LOGISTICA",
                "unidad": "EVENTO",
                "activo": "on",
            },
        )
        self.assertEqual(response.status_code, 302)
        servicio = ServicioCatalogo.objects.get(nombre="Valet parking")
        self.assertEqual(servicio.empresa, self.empresa_a)

    def test_post_no_puede_forzar_empresa_ajena(self):
        self.client.force_login(self.admin_a)
        response = self.client.post(
            self.url("catalogo_servicio_create"),
            {
                "empresa": str(self.empresa_b.id),
                "nombre": "Planta de luz",
                "categoria": "AUDIO_ILUMINACION",
                "unidad": "UNIDAD",
                "activo": "on",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertFalse(ServicioCatalogo.objects.filter(empresa=self.empresa_b, nombre="Planta de luz").exists())

    def test_editar_preserva_tenant(self):
        servicio = self.crear_servicio(nombre="Mesa de postres")
        self.client.force_login(self.admin_a)
        response = self.client.post(
            self.url("catalogo_servicio_update", self.empresa_a, servicio.id),
            {
                "empresa": str(self.empresa_b.id),
                "nombre": "Mesa de postres premium",
                "categoria": "BANQUETE",
                "unidad": "MESA",
                "activo": "on",
            },
        )
        self.assertEqual(response.status_code, 302)
        servicio.refresh_from_db()
        self.assertEqual(servicio.empresa, self.empresa_a)
        self.assertEqual(servicio.nombre, "Mesa de postres premium")

    def test_desactivar_no_elimina_registro(self):
        servicio = self.crear_servicio(nombre="Coctel de bienvenida")
        self.client.force_login(self.admin_a)
        response = self.client.post(self.url("catalogo_servicio_toggle", self.empresa_a, servicio.id))
        self.assertEqual(response.status_code, 302)
        servicio.refresh_from_db()
        self.assertFalse(servicio.activo)
        self.assertTrue(ServicioCatalogo.objects.filter(pk=servicio.pk).exists())
