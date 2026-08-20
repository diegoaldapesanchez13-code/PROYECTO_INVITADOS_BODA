from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from invitaciones.models import EventoBoda
from organizaciones.models import EmpresaSuscriptora, MembresiaEmpresa
from tareas.models import TareaEvento


class TasksWorkspaceR4DTests(TestCase):
    def setUp(self):
        self.User = get_user_model()
        self.empresa = EmpresaSuscriptora.objects.create(
            nombre_comercial="Empresa R4D", slug="empresa-r4d",
        )
        self.admin = self.User.objects.create_user(
            username="admin-r4d", password="Pass-R4D-2026!",
        )
        MembresiaEmpresa.objects.create(
            empresa=self.empresa, usuario=self.admin, rol="ADMIN_EMPRESA",
        )
        self.planner = self.User.objects.create_user(
            username="planner-r4d", password="Pass-R4D-2026!",
        )
        MembresiaEmpresa.objects.create(
            empresa=self.empresa, usuario=self.planner, rol="WEDDING_PLANNER",
        )
        self.evento = EventoBoda.objects.create(
            empresa=self.empresa,
            nombre_evento="Evento R4D",
            wedding_planner=self.planner,
        )

    def url(self):
        return reverse(
            "k9_evento_tareas",
            kwargs={"empresa_slug": self.empresa.slug, "evento_id": self.evento.id},
        )

    def test_tasks_tab_enabled(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse(
            "k9_evento_resumen",
            kwargs={"empresa_slug": self.empresa.slug, "evento_id": self.evento.id},
        ))
        tab = next(x for x in response.context["workspace_navigation"]["tabs"] if x["key"] == "tareas")
        self.assertTrue(tab["enabled"])
        self.assertEqual(tab["url"], self.url())

    def test_tasks_page_uses_workspace_shell(self):
        self.client.force_login(self.admin)
        response = self.client.get(self.url())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Tareas")
        self.assertContains(response, "workspace_tasks_r4.css")
        self.assertContains(response, "workspace_tasks_r4.js")

    def test_create_minimal_task_without_responsible_or_date(self):
        self.client.force_login(self.admin)
        response = self.client.post(self.url(), {
            "accion": "guardar",
            "titulo": "Confirmar acceso",
            "responsable": "",
            "servicio_evento": "",
            "prioridad": "MEDIA",
            "categoria": "GENERAL",
            "fecha_inicio": "",
            "fecha_limite": "",
            "hora_inicio": "",
            "hora_fin": "",
            "estado": "PENDIENTE",
            "porcentaje_avance": "0",
            "descripcion": "",
            "notas": "",
        })
        self.assertEqual(response.status_code, 302)
        tarea = TareaEvento.objects.get(evento=self.evento, titulo="Confirmar acceso")
        self.assertIsNone(tarea.responsable)
        self.assertIsNone(tarea.fecha_limite)

    def test_responsible_cross_tenant_rejected_by_form_queryset(self):
        otra = EmpresaSuscriptora.objects.create(nombre_comercial="Otra", slug="otra-r4d")
        outsider = self.User.objects.create_user(username="out-r4d", password="x")
        MembresiaEmpresa.objects.create(empresa=otra, usuario=outsider, rol="WEDDING_PLANNER")
        self.client.force_login(self.admin)
        response = self.client.post(self.url(), {
            "accion": "guardar",
            "titulo": "Tarea",
            "responsable": outsider.id,
            "servicio_evento": "",
            "prioridad": "MEDIA",
            "categoria": "GENERAL",
            "estado": "PENDIENTE",
            "porcentaje_avance": "0",
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(TareaEvento.objects.filter(evento=self.evento, titulo="Tarea").exists())

    def test_kanban_move_changes_state(self):
        tarea = TareaEvento.objects.create(evento=self.evento, titulo="Mover")
        self.client.force_login(self.admin)
        response = self.client.post(self.url(), {
            "accion": "mover_estado",
            "tarea_id": tarea.id,
            "estado": "EN_PROCESO",
        })
        self.assertEqual(response.status_code, 302)
        tarea.refresh_from_db()
        self.assertEqual(tarea.estado, "EN_PROCESO")

    def test_complete_sets_progress_to_100(self):
        tarea = TareaEvento.objects.create(evento=self.evento, titulo="Completar", porcentaje_avance=30)
        self.client.force_login(self.admin)
        self.client.post(self.url(), {
            "accion": "mover_estado",
            "tarea_id": tarea.id,
            "estado": "COMPLETADA",
        })
        tarea.refresh_from_db()
        self.assertEqual(tarea.estado, "COMPLETADA")
        self.assertEqual(tarea.porcentaje_avance, 100)

    def test_cancel_then_archive_preserves_task(self):
        tarea = TareaEvento.objects.create(evento=self.evento, titulo="Cancelar")
        self.client.force_login(self.admin)
        self.client.post(self.url(), {"accion": "cancelar", "tarea_id": tarea.id})
        tarea.refresh_from_db()
        self.assertEqual(tarea.estado, "CANCELADA")
        self.client.post(self.url(), {"accion": "archivar", "tarea_id": tarea.id})
        tarea.refresh_from_db()
        self.assertIsNotNone(tarea.archivado_en)
        self.assertTrue(TareaEvento.objects.filter(pk=tarea.id).exists())

    def test_fresh_task_can_be_deleted_as_error(self):
        tarea = TareaEvento.objects.create(evento=self.evento, titulo="Error")
        task_id = tarea.id
        self.client.force_login(self.admin)
        response = self.client.post(self.url(), {
            "accion": "eliminar_error",
            "tarea_id": task_id,
            "confirmacion": "ELIMINAR",
        })
        self.assertEqual(response.status_code, 302)
        self.assertFalse(TareaEvento.objects.filter(pk=task_id).exists())

    def test_started_task_cannot_be_deleted_as_error(self):
        tarea = TareaEvento.objects.create(evento=self.evento, titulo="Con historial", estado="EN_PROCESO")
        self.client.force_login(self.admin)
        self.client.post(self.url(), {
            "accion": "eliminar_error",
            "tarea_id": tarea.id,
            "confirmacion": "ELIMINAR",
        })
        self.assertTrue(TareaEvento.objects.filter(pk=tarea.id).exists())

    def test_admin_can_purge_archived_task_without_evidence(self):
        tarea = TareaEvento.objects.create(
            evento=self.evento,
            titulo="Archivada",
            estado="COMPLETADA",
            archivado_en=timezone.now(),
            archivado_por=self.admin,
        )
        task_id = tarea.id
        self.client.force_login(self.admin)
        self.client.post(self.url()+"?vista=archivadas", {
            "accion": "purgar",
            "tarea_id": task_id,
            "confirmacion": "PURGAR",
            "vista": "archivadas",
        })
        self.assertFalse(TareaEvento.objects.filter(pk=task_id).exists())

    def test_planner_cannot_purge_archived_task(self):
        tarea = TareaEvento.objects.create(
            evento=self.evento,
            titulo="Archivada planner",
            estado="CANCELADA",
            archivado_en=timezone.now(),
            archivado_por=self.admin,
        )
        self.client.force_login(self.planner)
        response = self.client.post(self.url()+"?vista=archivadas", {
            "accion": "purgar",
            "tarea_id": tarea.id,
            "confirmacion": "PURGAR",
        })
        self.assertEqual(response.status_code, 403)
        self.assertTrue(TareaEvento.objects.filter(pk=tarea.id).exists())

    def test_assigned_planner_can_manage_tasks(self):
        self.client.force_login(self.planner)
        response = self.client.post(self.url(), {
            "accion": "guardar",
            "titulo": "Tarea planner",
            "responsable": self.planner.id,
            "servicio_evento": "",
            "prioridad": "ALTA",
            "categoria": "GENERAL",
            "estado": "PENDIENTE",
            "porcentaje_avance": "0",
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(TareaEvento.objects.filter(evento=self.evento, titulo="Tarea planner").exists())
