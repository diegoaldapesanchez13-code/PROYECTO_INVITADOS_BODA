from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from invitaciones.models import EventoBoda
from itinerario.models import ActividadItinerario
from organizaciones.models import EmpresaSuscriptora, MembresiaEmpresa
from tareas.models import TareaEvento


class PlannerDashboardR3BTests(TestCase):
    def setUp(self):
        self.User = get_user_model()
        self.empresa = EmpresaSuscriptora.objects.create(
            nombre_comercial="Empresa R3B",
            slug="empresa-r3b",
        )
        self.otra = EmpresaSuscriptora.objects.create(
            nombre_comercial="Otra R3B",
            slug="otra-r3b",
        )
        self.planner = self.User.objects.create_user(
            username="planner-r3b",
            password="Pass-R3B-2026!",
        )
        MembresiaEmpresa.objects.create(
            empresa=self.empresa,
            usuario=self.planner,
            rol="WEDDING_PLANNER",
        )
        self.otro_planner = self.User.objects.create_user(
            username="otro-planner-r3b",
            password="Pass-R3B-2026!",
        )
        MembresiaEmpresa.objects.create(
            empresa=self.empresa,
            usuario=self.otro_planner,
            rol="WEDDING_PLANNER",
        )
        self.admin = self.User.objects.create_user(
            username="admin-r3b",
            password="Pass-R3B-2026!",
        )
        MembresiaEmpresa.objects.create(
            empresa=self.empresa,
            usuario=self.admin,
            rol="ADMIN_EMPRESA",
        )

    def _evento(self, nombre="Evento R3B", planner=None, **kwargs):
        return EventoBoda.objects.create(
            empresa=self.empresa,
            nombre_evento=nombre,
            wedding_planner=planner or self.planner,
            **kwargs,
        )

    def test_planner_canonical_url_uses_new_home(self):
        self.client.force_login(self.planner)
        response = self.client.get(
            reverse(
                "planner_dashboard_empresa",
                kwargs={"empresa_slug": self.empresa.slug},
            )
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Planner Workspace")
        self.assertContains(response, "planner_dashboard_r3.css")

    def test_legacy_wedding_planner_url_redirects_to_canonical(self):
        self.client.force_login(self.planner)
        response = self.client.get(
            reverse(
                "planner_dashboard_empresa_legacy",
                kwargs={"empresa_slug": self.empresa.slug},
            )
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response["Location"],
            reverse(
                "planner_dashboard_empresa",
                kwargs={"empresa_slug": self.empresa.slug},
            ),
        )

    def test_only_assigned_events_are_visible(self):
        self._evento(nombre="Asignado")
        self._evento(nombre="No asignado", planner=self.otro_planner)
        self.client.force_login(self.planner)
        response = self.client.get(
            reverse(
                "planner_dashboard_empresa",
                kwargs={"empresa_slug": self.empresa.slug},
            )
        )
        self.assertContains(response, "Asignado")
        self.assertNotContains(response, "No asignado")

    def test_admin_cannot_open_planner_home_as_planner(self):
        self.client.force_login(self.admin)
        response = self.client.get(
            reverse(
                "planner_dashboard_empresa",
                kwargs={"empresa_slug": self.empresa.slug},
            )
        )
        self.assertEqual(response.status_code, 403)

    def test_assigned_task_is_visible(self):
        evento = self._evento()
        TareaEvento.objects.create(
            evento=evento,
            titulo="Llamar proveedor",
            responsable=self.planner,
            fecha_limite=timezone.localdate(),
        )
        self.client.force_login(self.planner)
        response = self.client.get(
            reverse(
                "planner_dashboard_empresa",
                kwargs={"empresa_slug": self.empresa.slug},
            )
        )
        self.assertContains(response, "Llamar proveedor")
        self.assertContains(response, "Tareas de hoy")

    def test_other_planner_task_is_not_visible(self):
        evento = self._evento()
        TareaEvento.objects.create(
            evento=evento,
            titulo="Tarea ajena",
            responsable=self.otro_planner,
        )
        self.client.force_login(self.planner)
        response = self.client.get(
            reverse(
                "planner_dashboard_empresa",
                kwargs={"empresa_slug": self.empresa.slug},
            )
        )
        self.assertNotContains(response, "Tarea ajena")

    def test_upcoming_activity_is_visible(self):
        evento = self._evento()
        ActividadItinerario.objects.create(
            evento=evento,
            tipo="CITA",
            titulo="Visita a sede",
            fecha=timezone.localdate(),
            hora_inicio=timezone.datetime.strptime("10:00", "%H:%M").time(),
            responsable=self.planner,
        )
        self.client.force_login(self.planner)
        response = self.client.get(
            reverse(
                "planner_dashboard_empresa",
                kwargs={"empresa_slug": self.empresa.slug},
            )
        )
        self.assertContains(response, "Visita a sede")
        self.assertContains(response, "Agenda de hoy")

    def test_cross_tenant_slug_is_not_accessible(self):
        self.client.force_login(self.planner)
        response = self.client.get(
            reverse(
                "planner_dashboard_empresa",
                kwargs={"empresa_slug": self.otra.slug},
            )
        )
        self.assertEqual(response.status_code, 404)

    def test_canonical_planner_dashboard_is_read_only_entrypoint(self):
        self.client.force_login(self.planner)
        response = self.client.post(
            reverse(
                "planner_dashboard_empresa",
                kwargs={"empresa_slug": self.empresa.slug},
            ),
            {"accion": "accion-inexistente"},
        )
        self.assertEqual(response.status_code, 405)
