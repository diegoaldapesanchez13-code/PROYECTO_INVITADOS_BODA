from copy import deepcopy
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from catalogo.models import ProveedorServicioCatalogo, ServicioCatalogo
from eventos.models import ContratoEvento
from invitaciones.models import EventoBoda
from organizaciones.models import EmpresaSuscriptora, MembresiaEmpresa
from proveedores.models import Proveedor, ServicioEvento


class ServicesWorkspaceR4CTests(TestCase):
    def setUp(self):
        self.User = get_user_model()
        self.empresa = EmpresaSuscriptora.objects.create(
            nombre_comercial="Empresa R4C",
            slug="empresa-r4c",
        )
        self.otra = EmpresaSuscriptora.objects.create(
            nombre_comercial="Otra R4C",
            slug="otra-r4c",
        )
        self.admin = self.User.objects.create_user(
            username="admin-r4c",
            password="Pass-R4C-2026!",
        )
        MembresiaEmpresa.objects.create(
            empresa=self.empresa,
            usuario=self.admin,
            rol="ADMIN_EMPRESA",
        )
        self.planner = self.User.objects.create_user(
            username="planner-r4c",
            password="Pass-R4C-2026!",
        )
        MembresiaEmpresa.objects.create(
            empresa=self.empresa,
            usuario=self.planner,
            rol="WEDDING_PLANNER",
        )
        self.evento = EventoBoda.objects.create(
            empresa=self.empresa,
            nombre_evento="Evento R4C",
            wedding_planner=self.planner,
        )
        self.catalogo = ServicioCatalogo.objects.create(
            empresa=self.empresa,
            nombre="Fotografía R4C",
            categoria="FOTOGRAFIA_VIDEO",
            activo=True,
        )
        self.proveedor = Proveedor.objects.create(
            empresa=self.empresa,
            nombre_comercial="Foto Pro R4C",
            activo=True,
        )
        self.otro_proveedor = Proveedor.objects.create(
            empresa=self.empresa,
            nombre_comercial="DJ Incompatible R4C",
            activo=True,
        )
        ProveedorServicioCatalogo.objects.create(
            proveedor=self.proveedor,
            servicio_catalogo=self.catalogo,
            activo=True,
        )

    def url(self):
        return reverse(
            "k9_evento_servicios",
            kwargs={"empresa_slug": self.empresa.slug, "evento_id": self.evento.id},
        )

    def test_services_tab_is_enabled(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse(
            "k9_evento_resumen",
            kwargs={"empresa_slug": self.empresa.slug, "evento_id": self.evento.id},
        ))
        tab = next(
            item for item in response.context["workspace_navigation"]["tabs"]
            if item["key"] == "servicios"
        )
        self.assertTrue(tab["enabled"])
        self.assertEqual(tab["url"], self.url())

    def test_services_page_uses_workspace_shell(self):
        self.client.force_login(self.admin)
        response = self.client.get(self.url())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Servicios y proveedores")
        self.assertContains(response, "workspace_services_r4.css")

    def test_create_minimal_operational_service_without_provider_or_cost(self):
        self.client.force_login(self.admin)
        response = self.client.post(
            self.url(),
            {
                "accion": "guardar",
                "nombre_servicio": "Valet parking",
                "servicio_catalogo_k9": "",
                "prestacion_tipo": "POR_DEFINIR",
                "proveedor": "",
                "fecha_servicio": "",
                "hora_inicio": "",
                "hora_fin": "",
                "lugar": "",
                "estado_operativo": "PENDIENTE",
                "descripcion": "",
                "notas_internas": "",
            },
        )
        self.assertEqual(response.status_code, 302)
        servicio = ServicioEvento.objects.get(evento=self.evento, nombre_servicio="Valet parking")
        self.assertEqual(servicio.origen, "MANUAL")
        self.assertEqual(servicio.modalidad, "ADICIONAL")
        self.assertIsNone(servicio.proveedor)
        self.assertEqual(servicio.cargo_adicional_cliente, Decimal("0.00"))
        self.assertEqual(servicio.costo_proveedor, Decimal("0.00"))

    def test_assign_compatible_provider_from_catalog(self):
        servicio = ServicioEvento.objects.create(
            evento=self.evento,
            servicio_catalogo_k9=self.catalogo,
            nombre_servicio=self.catalogo.nombre,
            origen="CATALOGO",
        )
        self.client.force_login(self.admin)
        response = self.client.post(
            self.url() + f"?servicio={servicio.id}",
            {
                "accion": "guardar",
                "servicio_id": servicio.id,
                "servicio_catalogo_k9": self.catalogo.id,
                "nombre_servicio": self.catalogo.nombre,
                "prestacion_tipo": "PROVEEDOR",
                "proveedor": self.proveedor.id,
                "fecha_servicio": "",
                "hora_inicio": "",
                "hora_fin": "",
                "lugar": "",
                "estado_operativo": "PENDIENTE",
                "descripcion": "",
                "notas_internas": "",
            },
        )
        self.assertEqual(response.status_code, 302)
        servicio.refresh_from_db()
        self.assertEqual(servicio.proveedor, self.proveedor)
        self.assertEqual(servicio.prestacion_tipo, "PROVEEDOR")

    def test_incompatible_provider_is_rejected_for_catalog_service(self):
        servicio = ServicioEvento.objects.create(
            evento=self.evento,
            servicio_catalogo_k9=self.catalogo,
            nombre_servicio=self.catalogo.nombre,
            origen="CATALOGO",
        )
        self.client.force_login(self.admin)
        response = self.client.post(
            self.url() + f"?servicio={servicio.id}",
            {
                "accion": "guardar",
                "servicio_id": servicio.id,
                "servicio_catalogo_k9": self.catalogo.id,
                "nombre_servicio": self.catalogo.nombre,
                "prestacion_tipo": "PROVEEDOR",
                "proveedor": self.otro_proveedor.id,
                "fecha_servicio": "",
                "hora_inicio": "",
                "hora_fin": "",
                "lugar": "",
                "estado_operativo": "PENDIENTE",
                "descripcion": "",
                "notas_internas": "",
            },
        )
        self.assertEqual(response.status_code, 200)
        servicio.refresh_from_db()
        self.assertIsNone(servicio.proveedor)

    def test_cross_tenant_provider_cannot_be_assigned(self):
        cross = Proveedor.objects.create(
            empresa=self.otra,
            nombre_comercial="Proveedor Otro Tenant",
            activo=True,
        )
        servicio = ServicioEvento.objects.create(
            evento=self.evento,
            nombre_servicio="Audio manual",
        )
        self.client.force_login(self.admin)
        response = self.client.post(
            self.url() + f"?servicio={servicio.id}",
            {
                "accion": "guardar",
                "servicio_id": servicio.id,
                "servicio_catalogo_k9": "",
                "nombre_servicio": "Audio manual",
                "prestacion_tipo": "PROVEEDOR",
                "proveedor": cross.id,
                "fecha_servicio": "",
                "hora_inicio": "",
                "hora_fin": "",
                "lugar": "",
                "estado_operativo": "PENDIENTE",
                "descripcion": "",
                "notas_internas": "",
            },
        )
        self.assertEqual(response.status_code, 200)
        servicio.refresh_from_db()
        self.assertIsNone(servicio.proveedor)

    def test_operational_service_does_not_modify_contract_snapshot(self):
        contrato = ContratoEvento.objects.create(
            evento=self.evento,
            version=1,
            estado="CONTRATADO",
            snapshot_version=2,
            snapshot_comercial={"version": 2, "totales": {"total_final": "100000.00"}},
        )
        original = deepcopy(contrato.snapshot_comercial)

        self.client.force_login(self.admin)
        self.client.post(
            self.url(),
            {
                "accion": "guardar",
                "nombre_servicio": "Servicio interno post contrato",
                "servicio_catalogo_k9": "",
                "prestacion_tipo": "EMPRESA",
                "proveedor": "",
                "fecha_servicio": "",
                "hora_inicio": "",
                "hora_fin": "",
                "lugar": "",
                "estado_operativo": "PENDIENTE",
                "descripcion": "",
                "notas_internas": "",
            },
        )
        contrato.refresh_from_db()
        self.assertEqual(contrato.snapshot_comercial, original)

    def test_contract_service_identity_stays_frozen_when_provider_changes(self):
        contrato = ContratoEvento.objects.create(
            evento=self.evento,
            version=1,
            estado="CONTRATADO",
            snapshot_version=2,
            snapshot_comercial={"version": 2},
        )
        servicio = ServicioEvento.objects.create(
            evento=self.evento,
            contrato_origen=contrato,
            linea_origen_key="incluido:test",
            snapshot_linea={"nombre": "Fotografía contractual"},
            servicio_catalogo_k9=self.catalogo,
            nombre_servicio="Fotografía contractual",
            prestacion_tipo="POR_DEFINIR",
            origen="PAQUETE",
            modalidad="INCLUIDO",
        )
        snapshot_before = deepcopy(servicio.snapshot_linea)

        self.client.force_login(self.admin)
        response = self.client.post(
            self.url() + f"?servicio={servicio.id}",
            {
                "accion": "guardar",
                "servicio_id": servicio.id,
                "servicio_catalogo_k9": self.catalogo.id,
                "nombre_servicio": "Fotografía contractual",
                "prestacion_tipo": "PROVEEDOR",
                "proveedor": self.proveedor.id,
                "fecha_servicio": "",
                "hora_inicio": "",
                "hora_fin": "",
                "lugar": "",
                "estado_operativo": "PROGRAMADO",
                "descripcion": "",
                "notas_internas": "",
            },
        )
        self.assertEqual(response.status_code, 302)
        servicio.refresh_from_db()
        self.assertEqual(servicio.proveedor, self.proveedor)
        self.assertEqual(servicio.snapshot_linea, snapshot_before)
        self.assertEqual(servicio.nombre_servicio, "Fotografía contractual")

    def test_cancel_and_archive_preserve_service(self):
        servicio = ServicioEvento.objects.create(
            evento=self.evento,
            nombre_servicio="Servicio cancelable",
        )
        self.client.force_login(self.admin)
        self.client.post(
            self.url() + f"?servicio={servicio.id}",
            {"accion": "cancelar", "servicio_id": servicio.id},
        )
        servicio.refresh_from_db()
        self.assertEqual(servicio.estado_operativo, "CANCELADO")

        self.client.post(
            self.url() + f"?servicio={servicio.id}",
            {"accion": "archivar", "servicio_id": servicio.id},
        )
        servicio.refresh_from_db()
        self.assertIsNotNone(servicio.archivado_en)
        self.assertTrue(ServicioEvento.objects.filter(pk=servicio.id).exists())

    def test_fresh_manual_service_can_be_deleted_as_error(self):
        servicio = ServicioEvento.objects.create(
            evento=self.evento,
            nombre_servicio="Captura incorrecta",
            origen="MANUAL",
            estado="SOLICITADO",
            estado_comercial="BORRADOR",
            estado_operativo="PENDIENTE",
        )
        servicio_id = servicio.id
        self.client.force_login(self.admin)
        response = self.client.post(
            self.url() + f"?servicio={servicio.id}",
            {
                "accion": "eliminar_error",
                "servicio_id": servicio.id,
                "confirmacion": "ELIMINAR",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertFalse(ServicioEvento.objects.filter(pk=servicio_id).exists())

    def test_contractual_service_cannot_be_hard_deleted(self):
        contrato = ContratoEvento.objects.create(
            evento=self.evento,
            version=1,
            estado="CONTRATADO",
            snapshot_version=2,
            snapshot_comercial={"version": 2},
        )
        servicio = ServicioEvento.objects.create(
            evento=self.evento,
            contrato_origen=contrato,
            linea_origen_key="x",
            snapshot_linea={"nombre": "Contrato"},
            nombre_servicio="Servicio contractual",
        )
        self.client.force_login(self.admin)
        self.client.post(
            self.url() + f"?servicio={servicio.id}",
            {
                "accion": "eliminar_error",
                "servicio_id": servicio.id,
                "confirmacion": "ELIMINAR",
            },
        )
        self.assertTrue(ServicioEvento.objects.filter(pk=servicio.id).exists())

    def test_admin_can_purge_archived_service_without_protected_history(self):
        servicio = ServicioEvento.objects.create(
            evento=self.evento,
            nombre_servicio="Archivado vacío",
            origen="MANUAL",
            estado_operativo="CANCELADO",
            estado_comercial="CANCELADO",
            estado="CANCELADO",
            archivado_en=timezone.now(),
            archivado_por=self.admin,
        )
        servicio_id = servicio.id
        self.client.force_login(self.admin)
        self.client.post(
            self.url() + f"?servicio={servicio.id}&vista=archivados",
            {
                "accion": "purgar",
                "servicio_id": servicio.id,
                "confirmacion": "PURGAR",
                "vista": "archivados",
            },
        )
        self.assertFalse(ServicioEvento.objects.filter(pk=servicio_id).exists())

    def test_planner_cannot_purge_archived_service(self):
        servicio = ServicioEvento.objects.create(
            evento=self.evento,
            nombre_servicio="Archivado planner",
            origen="MANUAL",
            estado_operativo="CANCELADO",
            estado_comercial="CANCELADO",
            estado="CANCELADO",
            archivado_en=timezone.now(),
            archivado_por=self.admin,
        )
        self.client.force_login(self.planner)
        response = self.client.post(
            self.url() + f"?servicio={servicio.id}&vista=archivados",
            {
                "accion": "purgar",
                "servicio_id": servicio.id,
                "confirmacion": "PURGAR",
            },
        )
        self.assertEqual(response.status_code, 403)
        self.assertTrue(ServicioEvento.objects.filter(pk=servicio.id).exists())
