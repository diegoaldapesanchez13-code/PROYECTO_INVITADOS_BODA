from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from invitaciones.guest_domain import asegurar_roster_grupo
from invitaciones.models import EventoBoda, Grupoinvitacion, Invitado
from organizaciones.models import EmpresaSuscriptora, MembresiaEmpresa

from eventos.workspace_guests_capacity import resumen_cupo_evento


class GuestsWorkspaceR4FATests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.empresa = EmpresaSuscriptora.objects.create(
            nombre_comercial="Empresa R4FA",
            slug="empresa-r4fa",
        )
        self.otra = EmpresaSuscriptora.objects.create(
            nombre_comercial="Otra R4FA",
            slug="otra-r4fa",
        )
        self.admin = User.objects.create_user(
            username="admin-r4fa",
            password="Pass-R4FA-2026!",
        )
        MembresiaEmpresa.objects.create(
            empresa=self.empresa,
            usuario=self.admin,
            rol="ADMIN_EMPRESA",
        )
        self.planner = User.objects.create_user(
            username="planner-r4fa",
            password="Pass-R4FA-2026!",
        )
        MembresiaEmpresa.objects.create(
            empresa=self.empresa,
            usuario=self.planner,
            rol="WEDDING_PLANNER",
        )
        self.evento = EventoBoda.objects.create(
            empresa=self.empresa,
            nombre_evento="Evento R4FA",
            wedding_planner=self.planner,
            capacidad_contratada=4,
        )

    def url(self):
        return reverse(
            "k9_evento_invitados",
            kwargs={
                "empresa_slug": self.empresa.slug,
                "evento_id": self.evento.id,
            },
        )

    def grupo(self, nombre="Familia R4FA", tipo="FAMILIAR"):
        grupo = Grupoinvitacion.objects.create(
            evento=self.evento,
            nombre_grupo=nombre,
            tipo=tipo,
            cantidad_maxima=1,
        )
        if tipo == "FAMILIAR":
            Invitado.objects.create(
                grupo=grupo,
                nombre="Persona R4FA",
                orden=1,
            )
        else:
            asegurar_roster_grupo(grupo)
        return grupo

    def test_guest_tab_enabled(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse(
            "k9_evento_resumen",
            kwargs={
                "empresa_slug": self.empresa.slug,
                "evento_id": self.evento.id,
            },
        ))
        tab = next(
            x for x in response.context["workspace_navigation"]["tabs"]
            if x["key"] == "invitados"
        )
        self.assertTrue(tab["enabled"])
        self.assertEqual(tab["url"], self.url())

    def test_guest_page_uses_workspace_shell(self):
        self.client.force_login(self.admin)
        response = self.client.get(self.url())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Invitados")
        self.assertContains(response, "workspace_guests_r4.css")
        self.assertContains(response, "Cupo real")

    def test_declined_guest_releases_capacity_but_remains_in_roster(self):
        grupo = self.grupo()
        invitado = grupo.invitados.first()
        invitado.asistira = False
        invitado.save(update_fields=["asistira"])

        cupo = resumen_cupo_evento(self.evento)
        self.assertEqual(cupo.emitidos, 1)
        self.assertEqual(cupo.no_asisten, 1)
        self.assertEqual(cupo.reservados, 0)
        self.assertEqual(cupo.disponibles, 4)
        self.assertTrue(Invitado.objects.filter(pk=invitado.id).exists())

    def test_create_minimal_personal_invitation(self):
        self.client.force_login(self.admin)
        response = self.client.post(self.url(), {
            "accion": "guardar_grupo",
            "nombre_grupo": "Diego prueba",
            "tipo": "PERSONAL",
            "telefono_contacto": "",
            "correo_contacto": "",
            "cantidad_extra_permitida": "0",
        })
        self.assertEqual(response.status_code, 302)
        grupo = Grupoinvitacion.objects.get(nombre_grupo="Diego prueba")
        self.assertEqual(grupo.invitados.count(), 1)

    def test_create_family_invitation_from_lines(self):
        self.client.force_login(self.admin)
        response = self.client.post(self.url(), {
            "accion": "guardar_grupo",
            "nombre_grupo": "Familia Demo",
            "tipo": "FAMILIAR",
            "integrantes": "Ana\nLuis",
            "telefono_contacto": "",
            "correo_contacto": "",
            "cantidad_extra_permitida": "0",
        })
        self.assertEqual(response.status_code, 302)
        grupo = Grupoinvitacion.objects.get(nombre_grupo="Familia Demo")
        self.assertEqual(grupo.invitados.count(), 2)

    def test_declined_seat_can_be_reused(self):
        grupo = Grupoinvitacion.objects.create(
            evento=self.evento,
            nombre_grupo="Grupo lleno",
            tipo="FAMILIAR",
            cantidad_maxima=4,
        )
        people = [
            Invitado.objects.create(grupo=grupo, nombre=f"P{i}", orden=i)
            for i in range(1, 5)
        ]
        people[0].asistira = False
        people[0].save(update_fields=["asistira"])

        self.client.force_login(self.admin)
        response = self.client.post(self.url(), {
            "accion": "guardar_grupo",
            "nombre_grupo": "Nuevo lugar",
            "tipo": "PERSONAL",
            "telefono_contacto": "",
            "correo_contacto": "",
            "cantidad_extra_permitida": "0",
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            Grupoinvitacion.objects.filter(nombre_grupo="Nuevo lugar").exists()
        )

    def test_capacity_rejects_new_reserved_seat_when_full(self):
        grupo = Grupoinvitacion.objects.create(
            evento=self.evento,
            nombre_grupo="Grupo lleno",
            tipo="FAMILIAR",
            cantidad_maxima=4,
        )
        for i in range(1, 5):
            Invitado.objects.create(grupo=grupo, nombre=f"P{i}", orden=i)

        self.client.force_login(self.admin)
        response = self.client.post(self.url(), {
            "accion": "guardar_grupo",
            "nombre_grupo": "Exceso",
            "tipo": "PERSONAL",
            "telefono_contacto": "",
            "correo_contacto": "",
            "cantidad_extra_permitida": "0",
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(
            Grupoinvitacion.objects.filter(nombre_grupo="Exceso").exists()
        )

    def test_manual_no_response_keeps_person_and_releases_seat(self):
        grupo = self.grupo()
        invitado = grupo.invitados.first()
        self.client.force_login(self.admin)
        response = self.client.post(self.url(), {
            "accion": "respuesta",
            "invitado_id": invitado.id,
            "respuesta": "NO",
        })
        self.assertEqual(response.status_code, 302)
        invitado.refresh_from_db()
        self.assertIs(invitado.asistira, False)
        self.assertTrue(Invitado.objects.filter(pk=invitado.id).exists())
        self.assertEqual(resumen_cupo_evento(self.evento).reservados, 0)

    def test_reset_response_returns_seat_to_reserved(self):
        grupo = self.grupo()
        invitado = grupo.invitados.first()
        invitado.asistira = False
        invitado.save(update_fields=["asistira"])

        self.client.force_login(self.admin)
        self.client.post(self.url(), {
            "accion": "respuesta",
            "invitado_id": invitado.id,
            "respuesta": "PENDIENTE",
        })
        invitado.refresh_from_db()
        self.assertIsNone(invitado.asistira)
        self.assertEqual(resumen_cupo_evento(self.evento).reservados, 1)

    def test_filter_no_attendance(self):
        grupo = self.grupo()
        invitado = grupo.invitados.first()
        invitado.asistira = False
        invitado.save(update_fields=["asistira"])
        self.client.force_login(self.admin)
        response = self.client.get(self.url(), {"estado": "NO_ASISTEN"})
        self.assertContains(response, grupo.nombre_grupo)

    def test_fresh_group_can_be_deleted(self):
        grupo = self.grupo()
        self.client.force_login(self.admin)
        response = self.client.post(self.url(), {
            "accion": "eliminar_grupo",
            "grupo_id": grupo.id,
            "confirmacion": "ELIMINAR",
        })
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Grupoinvitacion.objects.filter(pk=grupo.id).exists())

    def test_answered_group_cannot_be_deleted(self):
        grupo = self.grupo()
        invitado = grupo.invitados.first()
        invitado.asistira = True
        invitado.save(update_fields=["asistira"])

        self.client.force_login(self.admin)
        self.client.post(self.url(), {
            "accion": "eliminar_grupo",
            "grupo_id": grupo.id,
            "confirmacion": "ELIMINAR",
        })
        self.assertTrue(Grupoinvitacion.objects.filter(pk=grupo.id).exists())

    def test_assigned_planner_can_manage_guests(self):
        self.client.force_login(self.planner)
        response = self.client.post(self.url(), {
            "accion": "guardar_grupo",
            "nombre_grupo": "Planner guest",
            "tipo": "PERSONAL",
            "telefono_contacto": "",
            "correo_contacto": "",
            "cantidad_extra_permitida": "0",
        })
        self.assertEqual(response.status_code, 302)

    def test_other_tenant_cannot_open_event_guests(self):
        outsider = get_user_model().objects.create_user(
            username="outsider-r4fa",
            password="Pass-R4FA-2026!",
        )
        MembresiaEmpresa.objects.create(
            empresa=self.otra,
            usuario=outsider,
            rol="ADMIN_EMPRESA",
        )
        self.client.force_login(outsider)
        response = self.client.get(self.url())
        self.assertEqual(response.status_code, 404)
