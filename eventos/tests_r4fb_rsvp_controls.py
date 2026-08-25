import json

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from invitaciones.models import DisenoInvitacion, EventoBoda, Grupoinvitacion, Invitado
from invitaciones.rsvp_control import evaluar_rsvp
from invitaciones.rsvp_models import (
    RsvpConfiguracionEvento,
    RsvpExcepcionGrupo,
)
from organizaciones.models import EmpresaSuscriptora, MembresiaEmpresa


class RsvpControlsR4FBTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.empresa = EmpresaSuscriptora.objects.create(
            nombre_comercial="Empresa R4FB",
            slug="empresa-r4fb",
        )
        self.admin = User.objects.create_user(
            username="admin-r4fb",
            password="Pass-R4FB-2026!",
        )
        MembresiaEmpresa.objects.create(
            empresa=self.empresa,
            usuario=self.admin,
            rol="ADMIN_EMPRESA",
        )
        self.planner = User.objects.create_user(
            username="planner-r4fb",
            password="Pass-R4FB-2026!",
        )
        MembresiaEmpresa.objects.create(
            empresa=self.empresa,
            usuario=self.planner,
            rol="WEDDING_PLANNER",
        )
        self.evento = EventoBoda.objects.create(
            empresa=self.empresa,
            nombre_evento="Evento R4FB",
            wedding_planner=self.planner,
        )
        self.grupo = Grupoinvitacion.objects.create(
            evento=self.evento,
            nombre_grupo="Familia R4FB",
            tipo="FAMILIAR",
            cantidad_maxima=1,
        )
        self.invitado = Invitado.objects.create(
            grupo=self.grupo,
            nombre="Invitado R4FB",
            orden=1,
        )

    def api_url(self):
        return reverse(
            "builder_public_rsvp_api",
            args=[self.grupo.codigo],
        )

    def workspace_url(self):
        return reverse(
            "k9_evento_invitados",
            kwargs={
                "empresa_slug": self.empresa.slug,
                "evento_id": self.evento.id,
            },
        )

    def post_rsvp(self, attending=True):
        return self.client.post(
            self.api_url(),
            data=json.dumps({
                "guestId": self.invitado.id,
                "attending": attending,
            }),
            content_type="application/json",
        )

    def test_default_is_open_for_backward_compatibility(self):
        decision = evaluar_rsvp(self.grupo)
        self.assertTrue(decision.permitido)
        self.assertEqual(decision.phase, "OPEN")

    def test_global_closed_blocks_public_post(self):
        RsvpConfiguracionEvento.objects.create(
            evento=self.evento,
            estado="CERRADO",
        )
        response = self.post_rsvp(True)
        self.assertEqual(response.status_code, 403)
        self.invitado.refresh_from_db()
        self.assertIsNone(self.invitado.asistira)

    def test_deadline_blocks_public_post(self):
        RsvpConfiguracionEvento.objects.create(
            evento=self.evento,
            estado="ABIERTO",
            fecha_limite=timezone.now() - timezone.timedelta(minutes=1),
        )
        response = self.post_rsvp(True)
        self.assertEqual(response.status_code, 403)

    def test_reminder_phase_does_not_block_rsvp(self):
        RsvpConfiguracionEvento.objects.create(
            evento=self.evento,
            estado="ABIERTO",
            recordatorio_desde=timezone.now() - timezone.timedelta(days=1),
            fecha_limite=timezone.now() + timezone.timedelta(days=2),
            mostrar_recordatorio=True,
        )
        decision = evaluar_rsvp(self.grupo)
        self.assertTrue(decision.permitido)
        self.assertEqual(decision.phase, "REMINDER")
        response = self.post_rsvp(True)
        self.assertEqual(response.status_code, 200)

    def test_group_enabled_override_reopens_closed_event(self):
        RsvpConfiguracionEvento.objects.create(
            evento=self.evento,
            estado="CERRADO",
        )
        RsvpExcepcionGrupo.objects.create(
            grupo=self.grupo,
            modo="HABILITADA",
        )
        response = self.post_rsvp(True)
        self.assertEqual(response.status_code, 200)
        self.invitado.refresh_from_db()
        self.assertIs(self.invitado.asistira, True)

    def test_group_blocked_override_blocks_open_event(self):
        RsvpConfiguracionEvento.objects.create(
            evento=self.evento,
            estado="ABIERTO",
        )
        RsvpExcepcionGrupo.objects.create(
            grupo=self.grupo,
            modo="BLOQUEADA",
        )
        response = self.post_rsvp(True)
        self.assertEqual(response.status_code, 403)

    def test_public_get_exposes_rsvp_control(self):
        RsvpConfiguracionEvento.objects.create(
            evento=self.evento,
            estado="CERRADO",
        )
        response = self.client.get(self.api_url())
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertFalse(payload["data"]["rsvpControl"]["allowed"])
        self.assertEqual(payload["data"]["rsvpControl"]["phase"], "CLOSED")

    def test_public_invitation_marks_closed_rsvp_as_unavailable(self):
        document = {
            "schemaVersion": 3,
            "page": {"name": "RSVP public test"},
            "sections": [],
            "nodes": [],
        }
        DisenoInvitacion.objects.create(
            evento=self.evento,
            documento_builder_borrador=document,
            documento_builder_publicado=document,
            estado="PUBLICADO",
        )
        RsvpConfiguracionEvento.objects.create(
            evento=self.evento,
            estado="CERRADO",
        )
        response = self.client.get(
            reverse("ver_invitacion", args=[self.grupo.codigo])
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'data-rsvp-allowed="0"')
        self.assertContains(response, "invitaciones/public/rsvp_state.css")
        self.assertNotContains(response, "dirtec-rsvp-dialog")
        self.assertNotContains(response, "rsvp_control.js")

    def test_admin_can_save_global_controls_from_workspace(self):
        self.client.force_login(self.admin)
        response = self.client.post(
            self.workspace_url(),
            {
                "accion": "guardar_rsvp_config",
                "estado": "CERRADO",
                "fecha_limite": "",
                "recordatorio_desde": "",
                "mensaje_abierto": "Abierto",
                "mensaje_recordatorio": "Recuerda",
                "mensaje_cerrado": "Cerrado",
            },
        )
        self.assertEqual(response.status_code, 302)
        config = RsvpConfiguracionEvento.objects.get(evento=self.evento)
        self.assertEqual(config.estado, "CERRADO")
        self.assertEqual(config.actualizado_por, self.admin)

    def test_assigned_planner_can_reopen_one_invitation(self):
        RsvpConfiguracionEvento.objects.create(
            evento=self.evento,
            estado="CERRADO",
        )
        self.client.force_login(self.planner)
        response = self.client.post(
            self.workspace_url() + f"?grupo={self.grupo.id}",
            {
                "accion": "guardar_rsvp_excepcion",
                "grupo_id": self.grupo.id,
                "modo": "HABILITADA",
                "motivo": "Confirmación tardía autorizada",
            },
        )
        self.assertEqual(response.status_code, 302)
        exception = RsvpExcepcionGrupo.objects.get(grupo=self.grupo)
        self.assertEqual(exception.modo, "HABILITADA")
        self.assertEqual(exception.actualizado_por, self.planner)
        self.assertTrue(evaluar_rsvp(self.grupo).permitido)

    def test_reminder_must_be_before_deadline(self):
        self.client.force_login(self.admin)
        now = timezone.localtime(timezone.now())
        later = now + timezone.timedelta(days=2)
        response = self.client.post(
            self.workspace_url(),
            {
                "accion": "guardar_rsvp_config",
                "estado": "ABIERTO",
                "fecha_limite": now.strftime("%Y-%m-%dT%H:%M"),
                "recordatorio_desde": later.strftime("%Y-%m-%dT%H:%M"),
                "mostrar_recordatorio": "on",
                "mensaje_abierto": "A",
                "mensaje_recordatorio": "B",
                "mensaje_cerrado": "C",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(
            RsvpConfiguracionEvento.objects.filter(evento=self.evento).exists()
        )
