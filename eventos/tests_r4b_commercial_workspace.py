from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from eventos.models import ContratoEvento
from invitaciones.models import EventoBoda
from organizaciones.models import EmpresaSuscriptora, MembresiaEmpresa
from paquetes.models import PaqueteBoda, PropuestaEvento


class CommercialWorkspaceR4BTests(TestCase):
    def setUp(self):
        self.User = get_user_model()
        self.empresa = EmpresaSuscriptora.objects.create(
            nombre_comercial="Empresa R4B",
            slug="empresa-r4b",
        )
        self.otra = EmpresaSuscriptora.objects.create(
            nombre_comercial="Otra R4B",
            slug="otra-r4b",
        )
        self.admin = self.User.objects.create_user(
            username="admin-r4b",
            password="Pass-R4B-2026!",
        )
        MembresiaEmpresa.objects.create(
            empresa=self.empresa,
            usuario=self.admin,
            rol="ADMIN_EMPRESA",
        )
        self.planner = self.User.objects.create_user(
            username="planner-r4b",
            password="Pass-R4B-2026!",
        )
        MembresiaEmpresa.objects.create(
            empresa=self.empresa,
            usuario=self.planner,
            rol="WEDDING_PLANNER",
        )
        self.evento = EventoBoda.objects.create(
            empresa=self.empresa,
            nombre_evento="Evento R4B",
            wedding_planner=self.planner,
        )
        self.paquete = PaqueteBoda.objects.create(
            empresa=self.empresa,
            nombre="Paquete Base R4B",
            precio_adulto="1000.00",
            precio_nino="500.00",
            cargo_fijo="10000.00",
        )

    def url(self):
        return reverse(
            "k9_evento_comercial",
            kwargs={"empresa_slug": self.empresa.slug, "evento_id": self.evento.id},
        )

    def crear_propuesta(self, estado="BORRADOR"):
        return PropuestaEvento.objects.create(
            empresa=self.empresa,
            evento=self.evento,
            paquete=self.paquete,
            adultos=10,
            ninos=2,
            estado=estado,
            created_by=self.admin,
            updated_by=self.admin,
        )

    def test_commercial_tab_is_enabled(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse(
            "k9_evento_resumen",
            kwargs={"empresa_slug": self.empresa.slug, "evento_id": self.evento.id},
        ))
        nav = response.context["workspace_navigation"]
        commercial = next(item for item in nav["tabs"] if item["key"] == "comercial")
        self.assertTrue(commercial["enabled"])
        self.assertEqual(commercial["url"], self.url())

    def test_commercial_page_uses_workspace_shell(self):
        self.client.force_login(self.admin)
        response = self.client.get(self.url())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Propuesta y contrato")
        self.assertContains(response, "workspace_commercial_r4.css")

    def test_create_proposal_stays_in_commercial_context(self):
        self.client.force_login(self.admin)
        response = self.client.post(
            self.url(),
            {
                "accion": "guardar_propuesta",
                "propuesta_id": "",
                "paquete": self.paquete.id,
                "sede": "",
                "adultos": "20",
                "ninos": "3",
                "descuento": "0",
                "estado": "BORRADOR",
                "notas_comerciales": "",
            },
        )
        self.assertEqual(response.status_code, 302)
        propuesta = PropuestaEvento.objects.get(evento=self.evento)
        self.assertIn(f"propuesta={propuesta.id}", response["Location"])
        self.assertEqual(propuesta.total, 31500)

    def test_user_cannot_set_contracted_state_manually(self):
        propuesta = self.crear_propuesta()
        self.client.force_login(self.admin)
        response = self.client.post(
            self.url() + f"?propuesta={propuesta.id}",
            {
                "accion": "guardar_propuesta",
                "propuesta_id": propuesta.id,
                "paquete": self.paquete.id,
                "sede": "",
                "adultos": "10",
                "ninos": "2",
                "descuento": "0",
                "estado": "CONTRATADO",
                "notas_comerciales": "",
            },
        )
        propuesta.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertNotEqual(propuesta.estado, "CONTRATADO")

    def test_accepted_proposal_generates_frozen_contract(self):
        propuesta = self.crear_propuesta(estado="ACEPTADO")
        self.client.force_login(self.admin)
        response = self.client.post(
            self.url() + f"?propuesta={propuesta.id}",
            {
                "accion": "generar_contrato",
                "propuesta_id": propuesta.id,
            },
        )
        self.assertEqual(response.status_code, 302)
        propuesta.refresh_from_db()
        contrato = ContratoEvento.objects.get(propuesta_origen=propuesta)
        self.assertEqual(propuesta.estado, "CONTRATADO")
        self.assertEqual(contrato.estado, "CONTRATADO")
        self.assertEqual(contrato.snapshot_version, 2)

    def test_contract_revision_creates_new_editable_proposal(self):
        propuesta = self.crear_propuesta(estado="ACEPTADO")
        self.client.force_login(self.admin)
        self.client.post(
            self.url() + f"?propuesta={propuesta.id}",
            {"accion": "generar_contrato", "propuesta_id": propuesta.id},
        )
        contrato = ContratoEvento.objects.get(propuesta_origen=propuesta)

        response = self.client.post(
            self.url(),
            {
                "accion": "crear_revision",
                "contrato_id": contrato.id,
                "propuesta_id": propuesta.id,
            },
        )
        self.assertEqual(response.status_code, 302)
        nueva = PropuestaEvento.objects.exclude(pk=propuesta.id).get(evento=self.evento)
        self.assertEqual(nueva.estado, "EN_REVISION")
        self.assertEqual(nueva.paquete, propuesta.paquete)

    def test_new_contract_supersedes_previous_version(self):
        propuesta = self.crear_propuesta(estado="ACEPTADO")
        self.client.force_login(self.admin)
        self.client.post(
            self.url(),
            {"accion": "generar_contrato", "propuesta_id": propuesta.id},
        )
        contrato_v1 = ContratoEvento.objects.get(propuesta_origen=propuesta)

        self.client.post(
            self.url(),
            {"accion": "crear_revision", "contrato_id": contrato_v1.id},
        )
        nueva = PropuestaEvento.objects.exclude(pk=propuesta.id).get(evento=self.evento)
        nueva.estado = "ACEPTADO"
        nueva.save(update_fields=["estado"])

        self.client.post(
            self.url() + f"?propuesta={nueva.id}",
            {"accion": "generar_contrato", "propuesta_id": nueva.id},
        )

        contrato_v1.refresh_from_db()
        contrato_v2 = ContratoEvento.objects.get(propuesta_origen=nueva)
        self.assertEqual(contrato_v1.estado, "REEMPLAZADO")
        self.assertEqual(contrato_v2.version, 2)
        self.assertEqual(contrato_v2.estado, "CONTRATADO")

    def test_only_draft_without_contract_can_be_hard_deleted(self):
        propuesta = self.crear_propuesta(estado="BORRADOR")
        self.client.force_login(self.admin)
        self.client.post(
            self.url() + f"?propuesta={propuesta.id}",
            {"accion": "eliminar_propuesta_error", "propuesta_id": propuesta.id},
        )
        self.assertFalse(PropuestaEvento.objects.filter(pk=propuesta.id).exists())

    def test_contracted_proposal_cannot_be_hard_deleted(self):
        propuesta = self.crear_propuesta(estado="ACEPTADO")
        self.client.force_login(self.admin)
        self.client.post(
            self.url(),
            {"accion": "generar_contrato", "propuesta_id": propuesta.id},
        )
        response = self.client.post(
            self.url() + f"?propuesta={propuesta.id}",
            {"accion": "eliminar_propuesta_error", "propuesta_id": propuesta.id},
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(PropuestaEvento.objects.filter(pk=propuesta.id).exists())

    def test_planner_assigned_can_view_commercial_workspace(self):
        self.client.force_login(self.planner)
        response = self.client.get(self.url())
        self.assertEqual(response.status_code, 200)

    def test_cross_tenant_event_not_reachable(self):
        outsider = self.User.objects.create_user(
            username="outsider-r4b",
            password="Pass-R4B-2026!",
        )
        MembresiaEmpresa.objects.create(
            empresa=self.otra,
            usuario=outsider,
            rol="ADMIN_EMPRESA",
        )
        self.client.force_login(outsider)
        response = self.client.get(self.url())
        self.assertEqual(response.status_code, 404)
