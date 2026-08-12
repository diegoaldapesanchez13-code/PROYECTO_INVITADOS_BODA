from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from invitaciones.models import EventoBoda
from organizaciones.models import EmpresaSuscriptora, MembresiaEmpresa


class PlannerWorkspaceK5Tests(TestCase):
    """Contrato actualizado: K.8.7.2 sustituye el Planner Workspace K5 legacy."""

    def setUp(self):
        User = get_user_model()
        self.empresa = EmpresaSuscriptora.objects.create(
            nombre_comercial="Casa K5",
            slug="casa-k5",
        )
        self.planner = User.objects.create_user(
            username="planner_k5",
            password="test123",
            first_name="Ana",
        )
        MembresiaEmpresa.objects.create(
            empresa=self.empresa,
            usuario=self.planner,
            rol="WEDDING_PLANNER",
        )
        self.evento = EventoBoda.objects.create(
            empresa=self.empresa,
            wedding_planner=self.planner,
            novio="A",
            novia="B",
            frase_portada="Test",
            mensaje_general="Test",
            fecha_misa=timezone.now() + timedelta(days=5),
            lugar_misa="Ceremonia",
            fecha_fiesta=timezone.now() + timedelta(days=5),
            lugar_fiesta="Recepcion",
        )
        self.client.force_login(self.planner)

    def test_planner_usa_bandeja_v3(self):
        response = self.client.get(reverse("dashboard_planner"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Bandeja de trabajo")
        self.assertContains(response, "Trabajo")
        self.assertContains(response, "Mis eventos")
        self.assertContains(response, "Agenda")

    def test_company_context_is_locked_and_not_selectable(self):
        response = self.client.get(reverse("dashboard_planner"))
        self.assertContains(response, self.empresa.nombre_comercial)
        self.assertContains(response, "Solo tus eventos asignados")
        self.assertNotContains(response, '<select name="empresa_id"')

    def test_event_card_opens_event_centric_workspace(self):
        response = self.client.get(reverse("dashboard_planner"))
        self.assertContains(response, "Abrir evento")
        self.assertContains(response, "Servicios")
        self.assertContains(response, "Agenda")
        self.assertContains(response, "Tareas")

    def test_planner_no_tiene_crud_paralelo_de_proveedor_servicio(self):
        response = self.client.get(reverse("dashboard_planner"))
        self.assertNotContains(response, 'value="asignar_proveedor_evento"')
        self.assertNotContains(response, 'value="actualizar_servicio_evento"')
        self.assertNotContains(response, "Guardar servicio")
        self.assertNotContains(response, "Asignar proveedor")
