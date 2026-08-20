from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from eventos.models import ParticipanteEvento
from invitaciones.models import EventoBoda
from itinerario.models import ActividadItinerario, ParticipanteActividad
from organizaciones.models import EmpresaSuscriptora, MembresiaEmpresa
from proveedores.models import Proveedor


class AgendaWorkspaceR4ETests(TestCase):
    def setUp(self):
        self.User = get_user_model()
        self.empresa = EmpresaSuscriptora.objects.create(
            nombre_comercial="Empresa R4E", slug="empresa-r4e",
        )
        self.admin = self.User.objects.create_user(
            username="admin-r4e", password="Pass-R4E-2026!",
        )
        MembresiaEmpresa.objects.create(
            empresa=self.empresa, usuario=self.admin, rol="ADMIN_EMPRESA",
        )
        self.planner = self.User.objects.create_user(
            username="planner-r4e", password="Pass-R4E-2026!",
        )
        MembresiaEmpresa.objects.create(
            empresa=self.empresa, usuario=self.planner, rol="WEDDING_PLANNER",
        )
        self.evento = EventoBoda.objects.create(
            empresa=self.empresa,
            nombre_evento="Evento R4E",
            wedding_planner=self.planner,
        )
        ParticipanteEvento.objects.update_or_create(
            evento=self.evento,
            usuario=self.planner,
            rol="PLANNER",
            defaults={"activo": True},
        )

    def url(self):
        return reverse(
            "k9_evento_agenda",
            kwargs={"empresa_slug": self.empresa.slug, "evento_id": self.evento.id},
        )

    def actividad(self, **kwargs):
        data = {
            "evento": self.evento,
            "tipo": "ACTIVIDAD",
            "titulo": "Actividad R4E",
            "fecha": timezone.localdate(),
            "hora_inicio": timezone.datetime.strptime("10:00", "%H:%M").time(),
        }
        data.update(kwargs)
        return ActividadItinerario.objects.create(**data)

    def test_agenda_tab_enabled(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse(
            "k9_evento_resumen",
            kwargs={"empresa_slug": self.empresa.slug, "evento_id": self.evento.id},
        ))
        tab = next(x for x in response.context["workspace_navigation"]["tabs"] if x["key"] == "agenda")
        self.assertTrue(tab["enabled"])
        self.assertEqual(tab["url"], self.url())

    def test_agenda_page_uses_workspace_shell(self):
        self.client.force_login(self.admin)
        response = self.client.get(self.url())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Agenda")
        self.assertContains(response, "workspace_agenda_r4.css")

    def test_create_minimal_activity(self):
        self.client.force_login(self.admin)
        response = self.client.post(self.url(), {
            "accion": "guardar",
            "tipo": "ACTIVIDAD",
            "titulo": "Montaje temprano",
            "categoria": "MONTAJE",
            "fecha": timezone.localdate().isoformat(),
            "hora_inicio": "08:00",
            "hora_fin": "",
            "ubicacion": "",
            "responsable": "",
            "proveedor": "",
            "servicio_evento": "",
            "prioridad": "MEDIA",
            "estado": "PENDIENTE",
            "orden": "0",
            "descripcion": "",
            "notas": "",
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(ActividadItinerario.objects.filter(evento=self.evento, titulo="Montaje temprano").exists())

    def test_cita_autocreates_event_participants(self):
        self.client.force_login(self.admin)
        response = self.client.post(self.url(), {
            "accion": "guardar",
            "tipo": "CITA",
            "titulo": "Visita técnica",
            "categoria": "PROVEEDORES",
            "fecha": timezone.localdate().isoformat(),
            "hora_inicio": "11:00",
            "hora_fin": "",
            "ubicacion": "",
            "responsable": self.planner.id,
            "proveedor": "",
            "servicio_evento": "",
            "prioridad": "ALTA",
            "estado": "PENDIENTE",
            "orden": "0",
            "descripcion": "",
            "notas": "",
        })
        self.assertEqual(response.status_code, 302)
        actividad = ActividadItinerario.objects.get(titulo="Visita técnica")
        self.assertTrue(actividad.participantes.filter(usuario=self.planner).exists())

    def test_provider_cross_tenant_rejected(self):
        otra = EmpresaSuscriptora.objects.create(nombre_comercial="Otra R4E", slug="otra-r4e")
        proveedor = Proveedor.objects.create(empresa=otra, nombre_comercial="Cross", activo=True)
        self.client.force_login(self.admin)
        response = self.client.post(self.url(), {
            "accion": "guardar",
            "tipo": "ACTIVIDAD",
            "titulo": "Cross provider",
            "categoria": "OTRO",
            "fecha": timezone.localdate().isoformat(),
            "hora_inicio": "12:00",
            "proveedor": proveedor.id,
            "prioridad": "MEDIA",
            "estado": "PENDIENTE",
            "orden": "0",
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(ActividadItinerario.objects.filter(titulo="Cross provider").exists())

    def test_complete_activity(self):
        actividad = self.actividad()
        self.client.force_login(self.admin)
        response = self.client.post(self.url(), {
            "accion": "completar",
            "actividad_id": actividad.id,
        })
        self.assertEqual(response.status_code, 302)
        actividad.refresh_from_db()
        self.assertEqual(actividad.estado, "COMPLETADA")

    def test_cancel_and_archive_preserve_activity(self):
        actividad = self.actividad()
        self.client.force_login(self.admin)
        self.client.post(self.url(), {"accion": "cancelar", "actividad_id": actividad.id})
        actividad.refresh_from_db()
        self.assertEqual(actividad.estado, "CANCELADA")
        self.client.post(self.url(), {"accion": "archivar", "actividad_id": actividad.id})
        actividad.refresh_from_db()
        self.assertIsNotNone(actividad.archivado_en)
        self.assertTrue(ActividadItinerario.objects.filter(pk=actividad.id).exists())

    def test_fresh_activity_can_be_deleted_as_error(self):
        actividad = self.actividad(titulo="Error R4E")
        activity_id = actividad.id
        self.client.force_login(self.admin)
        response = self.client.post(self.url(), {
            "accion": "eliminar_error",
            "actividad_id": activity_id,
            "confirmacion": "ELIMINAR",
        })
        self.assertEqual(response.status_code, 302)
        self.assertFalse(ActividadItinerario.objects.filter(pk=activity_id).exists())

    def test_activity_with_participant_response_cannot_be_deleted(self):
        actividad = self.actividad(tipo="CITA", titulo="Cita respondida")
        participante = ParticipanteActividad.objects.create(
            actividad=actividad,
            usuario=self.planner,
            rol="PLANNER",
            requerido=True,
        )
        participante.registrar_respuesta("CONFIRMADO")
        self.client.force_login(self.admin)
        self.client.post(self.url(), {
            "accion": "eliminar_error",
            "actividad_id": actividad.id,
            "confirmacion": "ELIMINAR",
        })
        self.assertTrue(ActividadItinerario.objects.filter(pk=actividad.id).exists())

    def test_admin_can_purge_archived_activity_without_responses(self):
        actividad = self.actividad(
            titulo="Archivada R4E",
            estado="COMPLETADA",
            archivado_en=timezone.now(),
            archivado_por=self.admin,
        )
        activity_id = actividad.id
        self.client.force_login(self.admin)
        self.client.post(self.url()+"?vista=archivadas", {
            "accion": "purgar",
            "actividad_id": activity_id,
            "confirmacion": "PURGAR",
            "vista": "archivadas",
        })
        self.assertFalse(ActividadItinerario.objects.filter(pk=activity_id).exists())

    def test_planner_cannot_purge_archived_activity(self):
        actividad = self.actividad(
            titulo="Archivada planner R4E",
            estado="CANCELADA",
            archivado_en=timezone.now(),
            archivado_por=self.admin,
        )
        self.client.force_login(self.planner)
        response = self.client.post(self.url()+"?vista=archivadas", {
            "accion": "purgar",
            "actividad_id": actividad.id,
            "confirmacion": "PURGAR",
        })
        self.assertEqual(response.status_code, 403)
        self.assertTrue(ActividadItinerario.objects.filter(pk=actividad.id).exists())

    def test_assigned_planner_can_create_activity(self):
        self.client.force_login(self.planner)
        response = self.client.post(self.url(), {
            "accion": "guardar",
            "tipo": "HITO",
            "titulo": "Ceremonia",
            "categoria": "CEREMONIA",
            "fecha": timezone.localdate().isoformat(),
            "hora_inicio": "16:00",
            "prioridad": "ALTA",
            "estado": "PENDIENTE",
            "orden": "0",
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(ActividadItinerario.objects.filter(titulo="Ceremonia").exists())
