from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from auditoria.models import RegistroAuditoria
from invitaciones.models import EventoBoda
from organizaciones.models import EmpresaSuscriptora, MembresiaEmpresa


class ActivityWorkspaceS23C3CTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.empresa = EmpresaSuscriptora.objects.create(
            nombre_comercial="Empresa C3C",
            slug="empresa-c3c",
        )
        self.otra_empresa = EmpresaSuscriptora.objects.create(
            nombre_comercial="Otra C3C",
            slug="otra-c3c",
        )
        self.admin = User.objects.create_user(
            username="admin-c3c",
            password="Pass-C3C-2026!",
        )
        MembresiaEmpresa.objects.create(
            empresa=self.empresa,
            usuario=self.admin,
            rol="ADMIN_EMPRESA",
        )
        self.evento = EventoBoda.objects.create(
            empresa=self.empresa,
            nombre_evento="Evento C3C",
        )
        self.otro_evento = EventoBoda.objects.create(
            empresa=self.otra_empresa,
            nombre_evento="Otro evento C3C",
        )

        RegistroAuditoria.objects.create(
            usuario=self.admin,
            empresa=self.empresa,
            evento=self.evento,
            accion="servicio_evento.actualizar",
            modelo="ServicioEvento",
            objeto_id="15",
            descripcion="Se actualizó un servicio del evento.",
            valores_anteriores={"estado": "PENDIENTE"},
            valores_nuevos={"estado": "CONFIRMADO"},
        )
        RegistroAuditoria.objects.create(
            usuario=self.admin,
            empresa=self.otra_empresa,
            evento=self.otro_evento,
            accion="otro.evento",
            modelo="EventoBoda",
            objeto_id=str(self.otro_evento.id),
            descripcion="No debe aparecer.",
        )

    def url(self):
        return reverse(
            "k9_evento_actividad",
            kwargs={
                "empresa_slug": self.empresa.slug,
                "evento_id": self.evento.id,
            },
        )

    def test_activity_center_reads_existing_audit_records(self):
        self.client.force_login(self.admin)
        response = self.client.get(self.url())

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "servicio_evento.actualizar")
        self.assertContains(response, "Se actualizó un servicio del evento.")
        self.assertContains(response, "ServicioEvento")
        self.assertNotContains(response, "No debe aparecer.")
        self.assertEqual(response.context["total_registros"], 1)

    def test_activity_filters_existing_records(self):
        self.client.force_login(self.admin)

        response = self.client.get(
            self.url(),
            {"modelo": "ServicioEvento", "q": "actualizó"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["total_registros"], 1)

        response = self.client.get(
            self.url(),
            {"modelo": "EventoBoda"},
        )
        self.assertEqual(response.context["total_registros"], 0)

    def test_activity_is_read_only(self):
        self.client.force_login(self.admin)
        before = RegistroAuditoria.objects.count()

        response = self.client.get(self.url())

        self.assertEqual(response.status_code, 200)
        self.assertEqual(RegistroAuditoria.objects.count(), before)
        self.assertContains(response, 'method="get"')

        post_response = self.client.post(
            self.url(),
            {"q": "intento-de-escritura"},
        )

        self.assertEqual(post_response.status_code, 405)
        self.assertEqual(RegistroAuditoria.objects.count(), before)

    def test_activity_tab_is_enabled_for_internal_user(self):
        self.client.force_login(self.admin)
        response = self.client.get(self.url())
        activity = next(
            tab
            for tab in response.context["workspace_navigation"]["tabs"]
            if tab["key"] == "actividad"
        )
        self.assertTrue(activity["enabled"])
        self.assertEqual(activity["url"], self.url())

    def test_other_tenant_cannot_open_activity(self):
        self.client.force_login(self.admin)
        response = self.client.get(
            reverse(
                "k9_evento_actividad",
                kwargs={
                    "empresa_slug": self.empresa.slug,
                    "evento_id": self.otro_evento.id,
                },
            )
        )
        self.assertEqual(response.status_code, 404)
