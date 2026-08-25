from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from invitaciones.models import EventoBoda
from organizaciones.models import EmpresaSuscriptora, MembresiaEmpresa
from tareas.models import TareaEvento


class EventWorkspaceR4ATests(TestCase):
    def setUp(self):
        self.User = get_user_model()
        self.empresa = EmpresaSuscriptora.objects.create(
            nombre_comercial="Empresa R4A",
            slug="empresa-r4a",
        )
        self.admin = self.User.objects.create_user(
            username="admin-r4a",
            password="Pass-R4A-2026!",
        )
        MembresiaEmpresa.objects.create(
            empresa=self.empresa,
            usuario=self.admin,
            rol="ADMIN_EMPRESA",
        )
        self.planner = self.User.objects.create_user(
            username="planner-r4a",
            password="Pass-R4A-2026!",
        )
        MembresiaEmpresa.objects.create(
            empresa=self.empresa,
            usuario=self.planner,
            rol="WEDDING_PLANNER",
        )

    def _evento(self, **kwargs):
        defaults = {
            "empresa": self.empresa,
            "nombre_evento": "Evento R4A",
            "wedding_planner": self.planner,
        }
        defaults.update(kwargs)
        return EventoBoda.objects.create(**defaults)

    def test_summary_uses_premium_workspace_shell(self):
        evento = self._evento()
        self.client.force_login(self.admin)
        response = self.client.get(
            reverse(
                "k9_evento_resumen",
                kwargs={"empresa_slug": self.empresa.slug, "evento_id": evento.id},
            )
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "workspace_r4.css")
        self.assertContains(response, "Estado del evento")
        self.assertContains(response, "Resumen operativo")

    def test_workspace_registry_exposes_full_future_structure(self):
        evento = self._evento()
        self.client.force_login(self.admin)
        response = self.client.get(
            reverse(
                "k9_evento_resumen",
                kwargs={"empresa_slug": self.empresa.slug, "evento_id": evento.id},
            )
        )
        for label in (
            "Resumen",
            "Datos",
            "Comercial",
            "Servicios",
            "Tareas",
            "Agenda",
            "Invitados",
            "Documentos",
            "Finanzas",
            "Invitación",
            "Actividad",
            "Configuración",
        ):
            self.assertContains(response, label)

    def test_only_unmigrated_tabs_are_disabled(self):
        """
        R4A registró la estructura completa del Workspace.
        R4B habilitó Comercial, R4C Servicios, R4D Tareas, R4E Agenda, R4F Invitados, R4G Documentos y R4H-A Finanzas.
        Los módulos que todavía no han migrado deben continuar deshabilitados
        y sin URLs rotas.
        """
        evento = self._evento()
        self.client.force_login(self.admin)
        response = self.client.get(
            reverse(
                "k9_evento_resumen",
                kwargs={"empresa_slug": self.empresa.slug, "evento_id": evento.id},
            )
        )
        nav = response.context["workspace_navigation"]

        commercial = next(tab for tab in nav["tabs"] if tab["key"] == "comercial")
        self.assertTrue(commercial["enabled"])
        self.assertEqual(
            commercial["url"],
            reverse(
                "k9_evento_comercial",
                kwargs={"empresa_slug": self.empresa.slug, "evento_id": evento.id},
            ),
        )

        services = next(tab for tab in nav["tabs"] if tab["key"] == "servicios")
        self.assertTrue(services["enabled"])
        self.assertEqual(
            services["url"],
            reverse(
                "k9_evento_servicios",
                kwargs={"empresa_slug": self.empresa.slug, "evento_id": evento.id},
            ),
        )

        tasks = next(tab for tab in nav["tabs"] if tab["key"] == "tareas")
        self.assertTrue(tasks["enabled"])
        self.assertEqual(
            tasks["url"],
            reverse(
                "k9_evento_tareas",
                kwargs={"empresa_slug": self.empresa.slug, "evento_id": evento.id},
            ),
        )

        agenda = next(tab for tab in nav["tabs"] if tab["key"] == "agenda")
        self.assertTrue(agenda["enabled"])
        self.assertEqual(
            agenda["url"],
            reverse(
                "k9_evento_agenda",
                kwargs={"empresa_slug": self.empresa.slug, "evento_id": evento.id},
            ),
        )

        guests = next(tab for tab in nav["tabs"] if tab["key"] == "invitados")
        self.assertTrue(guests["enabled"])
        self.assertEqual(
            guests["url"],
            reverse(
                "k9_evento_invitados",
                kwargs={"empresa_slug": self.empresa.slug, "evento_id": evento.id},
            ),
        )

        documents = next(tab for tab in nav["tabs"] if tab["key"] == "documentos")
        self.assertTrue(documents["enabled"])
        self.assertEqual(
            documents["url"],
            reverse(
                "k9_evento_documentos",
                kwargs={"empresa_slug": self.empresa.slug, "evento_id": evento.id},
            ),
        )

        finance = next(tab for tab in nav["tabs"] if tab["key"] == "finanzas")
        self.assertTrue(finance["enabled"])
        self.assertEqual(
            finance["url"],
            reverse(
                "k9_evento_finanzas",
                kwargs={"empresa_slug": self.empresa.slug, "evento_id": evento.id},
            ),
        )

    def test_summary_progress_reflects_base_data(self):
        evento = self._evento(
            fecha_inicio=timezone.now(),
        )
        self.client.force_login(self.admin)
        response = self.client.get(
            reverse(
                "k9_evento_resumen",
                kwargs={"empresa_slug": self.empresa.slug, "evento_id": evento.id},
            )
        )
        self.assertGreater(response.context["workspace_progress"], 0)
        self.assertLessEqual(response.context["workspace_progress"], 100)

    def test_overdue_task_appears_as_alert(self):
        evento = self._evento()
        TareaEvento.objects.create(
            evento=evento,
            titulo="Tarea vencida R4A",
            fecha_limite=timezone.localdate() - timezone.timedelta(days=1),
        )
        self.client.force_login(self.admin)
        response = self.client.get(
            reverse(
                "k9_evento_resumen",
                kwargs={"empresa_slug": self.empresa.slug, "evento_id": evento.id},
            )
        )
        self.assertContains(response, "Tarea vencida R4A")
        self.assertContains(response, "tarea(s) vencida(s)")

    def test_planner_can_use_same_workspace_for_assigned_event(self):
        evento = self._evento()
        self.client.force_login(self.planner)
        response = self.client.get(
            reverse(
                "k9_evento_resumen",
                kwargs={"empresa_slug": self.empresa.slug, "evento_id": evento.id},
            )
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Evento R4A")

    def test_unassigned_planner_cannot_open_workspace(self):
        other = self.User.objects.create_user(
            username="other-r4a",
            password="Pass-R4A-2026!",
        )
        MembresiaEmpresa.objects.create(
            empresa=self.empresa,
            usuario=other,
            rol="WEDDING_PLANNER",
        )
        evento = self._evento()
        self.client.force_login(other)
        response = self.client.get(
            reverse(
                "k9_evento_resumen",
                kwargs={"empresa_slug": self.empresa.slug, "evento_id": evento.id},
            )
        )
        self.assertEqual(response.status_code, 403)

    def test_return_context_survives_premium_tabs(self):
        evento = self._evento()
        dashboard = reverse(
            "empresa_dashboard",
            kwargs={"empresa_slug": self.empresa.slug},
        )
        self.client.force_login(self.admin)
        response = self.client.get(
            reverse(
                "k9_evento_resumen",
                kwargs={"empresa_slug": self.empresa.slug, "evento_id": evento.id},
            ),
            {"return_to": dashboard},
        )
        self.assertContains(response, "return_to=")
        self.assertEqual(response.context["return_to"], dashboard)
