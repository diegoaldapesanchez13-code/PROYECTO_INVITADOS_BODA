from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from eventos.models import ContratoEvento
from invitaciones.models import EventoBoda
from organizaciones.models import EmpresaSuscriptora, MembresiaEmpresa


class EventLifecycleVisibleR2CTests(TestCase):
    def setUp(self):
        self.User = get_user_model()
        self.password = "Pass-R2C-2026!"
        self.empresa = EmpresaSuscriptora.objects.create(
            nombre_comercial="Empresa R2C",
            slug="empresa-r2c",
        )
        self.otra_empresa = EmpresaSuscriptora.objects.create(
            nombre_comercial="Otra R2C",
            slug="otra-r2c",
        )
        self.admin = self.User.objects.create_user(
            username="admin-r2c",
            password=self.password,
        )
        MembresiaEmpresa.objects.create(
            empresa=self.empresa,
            usuario=self.admin,
            rol="ADMIN_EMPRESA",
        )
        self.planner = self.User.objects.create_user(
            username="planner-r2c",
            password=self.password,
        )
        MembresiaEmpresa.objects.create(
            empresa=self.empresa,
            usuario=self.planner,
            rol="WEDDING_PLANNER",
        )

    def _evento(self, **kwargs):
        defaults = {
            "empresa": self.empresa,
            "nombre_evento": "Evento R2C",
            "wedding_planner": self.planner,
        }
        defaults.update(kwargs)
        return EventoBoda.objects.create(**defaults)

    def test_configuration_page_shows_lifecycle_and_danger_zone(self):
        evento = self._evento()
        self.client.force_login(self.admin)
        response = self.client.get(reverse(
            "k9_evento_configuracion",
            kwargs={"empresa_slug": self.empresa.slug, "evento_id": evento.id},
        ))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Lifecycle del evento")
        self.assertContains(response, "Danger Zone")
        self.assertContains(response, "Eliminar evento creado por error")

    def test_lifecycle_endpoints_are_post_only(self):
        evento = self._evento()
        self.client.force_login(self.admin)
        for name in (
            "k9_evento_finalizar",
            "k9_evento_cancelar",
            "k9_evento_archivar",
            "k9_evento_restaurar",
            "k9_evento_eliminar_error",
            "k9_evento_purgar",
        ):
            response = self.client.get(reverse(
                name,
                kwargs={"empresa_slug": self.empresa.slug, "evento_id": evento.id},
            ))
            self.assertEqual(response.status_code, 405, name)

    def test_finalize_preserves_record(self):
        evento = self._evento()
        self.client.force_login(self.admin)
        response = self.client.post(reverse(
            "k9_evento_finalizar",
            kwargs={"empresa_slug": self.empresa.slug, "evento_id": evento.id},
        ))
        evento.refresh_from_db()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(evento.estado, "FINALIZADO")
        self.assertTrue(EventoBoda.objects.filter(pk=evento.id).exists())

    def test_cancel_preserves_record_and_reason(self):
        evento = self._evento()
        self.client.force_login(self.admin)
        self.client.post(
            reverse(
                "k9_evento_cancelar",
                kwargs={"empresa_slug": self.empresa.slug, "evento_id": evento.id},
            ),
            {"motivo": "Cliente no continúa"},
        )
        evento.refresh_from_db()
        self.assertEqual(evento.estado, "CANCELADO")
        self.assertEqual(evento.motivo_cancelacion, "Cliente no continúa")

    def test_archive_then_restore_returns_previous_state(self):
        evento = self._evento(estado="FINALIZADO")
        self.client.force_login(self.admin)
        self.client.post(reverse(
            "k9_evento_archivar",
            kwargs={"empresa_slug": self.empresa.slug, "evento_id": evento.id},
        ))
        evento.refresh_from_db()
        self.assertEqual(evento.estado, "ARCHIVADO")
        self.client.post(reverse(
            "k9_evento_restaurar",
            kwargs={"empresa_slug": self.empresa.slug, "evento_id": evento.id},
        ))
        evento.refresh_from_db()
        self.assertEqual(evento.estado, "FINALIZADO")

    def test_error_delete_requires_confirmation(self):
        evento = self._evento()
        self.client.force_login(self.admin)
        response = self.client.post(
            reverse(
                "k9_evento_eliminar_error",
                kwargs={"empresa_slug": self.empresa.slug, "evento_id": evento.id},
            ),
            {"confirmacion": "NO"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(EventoBoda.objects.filter(pk=evento.id).exists())

    def test_fresh_event_can_be_deleted_as_error(self):
        evento = self._evento()
        evento_id = evento.id
        self.client.force_login(self.admin)
        response = self.client.post(
            reverse(
                "k9_evento_eliminar_error",
                kwargs={"empresa_slug": self.empresa.slug, "evento_id": evento.id},
            ),
            {"confirmacion": "ELIMINAR"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertFalse(EventoBoda.objects.filter(pk=evento_id).exists())

    def test_contract_blocks_error_delete(self):
        evento = self._evento()
        ContratoEvento.objects.create(evento=evento, version=1)
        self.client.force_login(self.admin)
        self.client.post(
            reverse(
                "k9_evento_eliminar_error",
                kwargs={"empresa_slug": self.empresa.slug, "evento_id": evento.id},
            ),
            {"confirmacion": "ELIMINAR"},
        )
        self.assertTrue(EventoBoda.objects.filter(pk=evento.id).exists())

    def test_purge_requires_archived_state(self):
        evento = self._evento()
        self.client.force_login(self.admin)
        self.client.post(
            reverse(
                "k9_evento_purgar",
                kwargs={"empresa_slug": self.empresa.slug, "evento_id": evento.id},
            ),
            {"confirmacion": "PURGAR"},
        )
        self.assertTrue(EventoBoda.objects.filter(pk=evento.id).exists())

    def test_admin_can_purge_empty_archived_event(self):
        evento = self._evento(estado="ARCHIVADO", activo=False)
        evento_id = evento.id
        self.client.force_login(self.admin)
        self.client.post(
            reverse(
                "k9_evento_purgar",
                kwargs={"empresa_slug": self.empresa.slug, "evento_id": evento.id},
            ),
            {"confirmacion": "PURGAR"},
        )
        self.assertFalse(EventoBoda.objects.filter(pk=evento_id).exists())

    def test_cross_tenant_event_is_not_reachable(self):
        evento = self._evento()
        outsider = self.User.objects.create_user(
            username="outsider-r2c",
            password=self.password,
        )
        MembresiaEmpresa.objects.create(
            empresa=self.otra_empresa,
            usuario=outsider,
            rol="ADMIN_EMPRESA",
        )
        self.client.force_login(outsider)
        response = self.client.get(reverse(
            "k9_evento_configuracion",
            kwargs={"empresa_slug": self.empresa.slug, "evento_id": evento.id},
        ))
        self.assertEqual(response.status_code, 404)

    def test_planner_can_manage_assigned_event_but_not_purge(self):
        evento = self._evento()
        self.client.force_login(self.planner)
        response = self.client.post(reverse(
            "k9_evento_archivar",
            kwargs={"empresa_slug": self.empresa.slug, "evento_id": evento.id},
        ))
        self.assertEqual(response.status_code, 302)
        evento.refresh_from_db()
        self.assertEqual(evento.estado, "ARCHIVADO")

        response = self.client.post(
            reverse(
                "k9_evento_purgar",
                kwargs={"empresa_slug": self.empresa.slug, "evento_id": evento.id},
            ),
            {"confirmacion": "PURGAR"},
        )
        self.assertEqual(response.status_code, 403)
        self.assertTrue(EventoBoda.objects.filter(pk=evento.id).exists())
