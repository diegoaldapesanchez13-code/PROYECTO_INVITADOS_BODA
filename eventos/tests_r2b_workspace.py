from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from invitaciones.models import EventoBoda
from organizaciones.models import EmpresaSuscriptora, MembresiaEmpresa, SedeEvento


class EventWorkspaceR2BTests(TestCase):
    def setUp(self):
        self.User = get_user_model()
        self.password = "Pass-R2B-2026!"

        self.empresa = EmpresaSuscriptora.objects.create(
            nombre_comercial="Empresa R2B",
            slug="empresa-r2b",
        )
        self.otra_empresa = EmpresaSuscriptora.objects.create(
            nombre_comercial="Otra Empresa R2B",
            slug="otra-empresa-r2b",
        )

        self.admin = self.User.objects.create_user(
            username="admin-r2b",
            password=self.password,
        )
        MembresiaEmpresa.objects.create(
            empresa=self.empresa,
            usuario=self.admin,
            rol="ADMIN_EMPRESA",
        )

        self.planner = self.User.objects.create_user(
            username="planner-r2b",
            password=self.password,
        )
        MembresiaEmpresa.objects.create(
            empresa=self.empresa,
            usuario=self.planner,
            rol="WEDDING_PLANNER",
        )

        self.otro_planner = self.User.objects.create_user(
            username="otro-planner-r2b",
            password=self.password,
        )
        MembresiaEmpresa.objects.create(
            empresa=self.empresa,
            usuario=self.otro_planner,
            rol="WEDDING_PLANNER",
        )

        self.cliente = self.User.objects.create_user(
            username="cliente-r2b",
            password=self.password,
        )
        MembresiaEmpresa.objects.create(
            empresa=self.empresa,
            usuario=self.cliente,
            rol="CLIENTE",
        )

        self.sede = SedeEvento.objects.create(
            empresa=self.empresa,
            nombre="Sede R2B",
            activa=True,
        )

    def test_company_event_list_uses_new_app_shell(self):
        self.client.force_login(self.admin)
        response = self.client.get(
            reverse("k9_evento_list", kwargs={"empresa_slug": self.empresa.slug})
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Eventos")
        self.assertContains(response, "core/app/tokens.css")
        self.assertContains(response, "Nuevo evento")

    def test_company_navigation_points_events_to_canonical_route(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse("app_shell_preview"))
        expected = reverse("k9_evento_list", kwargs={"empresa_slug": self.empresa.slug})
        self.assertContains(response, expected)

    def test_admin_creates_minimal_event_and_enters_workspace(self):
        self.client.force_login(self.admin)
        response = self.client.post(
            reverse("k9_evento_create", kwargs={"empresa_slug": self.empresa.slug}),
            {
                "nombre_evento": "  Cena   Anual ACME ",
                "tipo_evento": "CORPORATIVO",
                "fecha_inicio": "",
                "fecha_fin": "",
                "cliente": "",
                "planner": "",
                "sede": "",
            },
        )
        evento = EventoBoda.objects.get(nombre_evento="Cena Anual ACME")
        self.assertRedirects(
            response,
            reverse(
                "k9_evento_resumen",
                kwargs={"empresa_slug": self.empresa.slug, "evento_id": evento.id},
            ),
        )
        self.assertIsNone(evento.fecha_inicio)
        self.assertIsNone(evento.fecha_fiesta)
        self.assertEqual(evento.novio, "")
        self.assertEqual(evento.estado, "BORRADOR")

    def test_planner_create_assigns_creator_and_workspace_is_accessible(self):
        self.client.force_login(self.planner)
        response = self.client.post(
            reverse("k9_evento_create", kwargs={"empresa_slug": self.empresa.slug}),
            {
                "nombre_evento": "Evento del planner",
                "tipo_evento": "OTRO",
                "fecha_inicio": "",
                "fecha_fin": "",
                "cliente": "",
                "planner": str(self.planner.id),
                "sede": "",
            },
        )
        evento = EventoBoda.objects.get(nombre_evento="Evento del planner")
        self.assertEqual(evento.wedding_planner, self.planner)
        self.assertEqual(response.status_code, 302)
        self.client.get(response["Location"])
        detail = self.client.get(response["Location"])
        self.assertEqual(detail.status_code, 200)

    def test_planner_list_only_shows_assigned_events(self):
        propio = EventoBoda.objects.create(
            empresa=self.empresa,
            nombre_evento="Propio",
            wedding_planner=self.planner,
        )
        EventoBoda.objects.create(
            empresa=self.empresa,
            nombre_evento="Ajeno",
            wedding_planner=self.otro_planner,
        )
        self.client.force_login(self.planner)
        response = self.client.get(
            reverse("k9_evento_list", kwargs={"empresa_slug": self.empresa.slug})
        )
        self.assertContains(response, propio.nombre_evento)
        self.assertNotContains(response, "Ajeno")

    def test_cross_tenant_slug_returns_404(self):
        self.client.force_login(self.admin)
        response = self.client.get(
            reverse("k9_evento_list", kwargs={"empresa_slug": self.otra_empresa.slug})
        )
        self.assertEqual(response.status_code, 404)

    def test_client_cannot_access_backoffice_event_list(self):
        self.client.force_login(self.cliente)
        response = self.client.get(
            reverse("k9_evento_list", kwargs={"empresa_slug": self.empresa.slug})
        )
        self.assertEqual(response.status_code, 403)

    def test_edit_updates_event_and_stays_in_data_context(self):
        evento = EventoBoda.objects.create(
            empresa=self.empresa,
            nombre_evento="Original",
        )
        fecha = timezone.now().replace(second=0, microsecond=0)
        self.client.force_login(self.admin)
        response = self.client.post(
            reverse(
                "k9_evento_datos",
                kwargs={"empresa_slug": self.empresa.slug, "evento_id": evento.id},
            ),
            {
                "nombre_evento": "Evento actualizado",
                "tipo_evento": "CORPORATIVO",
                "fecha_inicio": fecha.strftime("%Y-%m-%dT%H:%M"),
                "fecha_fin": "",
                "cliente": str(self.cliente.id),
                "planner": str(self.planner.id),
                "sede": str(self.sede.id),
            },
        )
        evento.refresh_from_db()
        self.assertRedirects(
            response,
            reverse(
                "k9_evento_datos",
                kwargs={"empresa_slug": self.empresa.slug, "evento_id": evento.id},
            ),
        )
        self.assertEqual(evento.nombre_evento, "Evento actualizado")
        self.assertEqual(evento.wedding_planner, self.planner)
        self.assertEqual(evento.sede, self.sede)
        self.assertTrue(evento.clientes.filter(id=self.cliente.id).exists())
        self.assertEqual(evento.estado, "ACTIVO")

    def test_edit_rejects_end_before_start(self):
        evento = EventoBoda.objects.create(
            empresa=self.empresa,
            nombre_evento="Fechas",
        )
        self.client.force_login(self.admin)
        response = self.client.post(
            reverse(
                "k9_evento_datos",
                kwargs={"empresa_slug": self.empresa.slug, "evento_id": evento.id},
            ),
            {
                "nombre_evento": "Fechas",
                "tipo_evento": "OTRO",
                "fecha_inicio": "2026-10-10T18:00",
                "fecha_fin": "2026-10-10T17:00",
                "cliente": "",
                "planner": "",
                "sede": "",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "no puede ser anterior")

    def test_summary_uses_generic_date_and_no_fake_wedding_fields(self):
        fecha = timezone.now()
        evento = EventoBoda.objects.create(
            empresa=self.empresa,
            nombre_evento="Evento genérico",
            fecha_inicio=fecha,
            fecha_fiesta=fecha,
        )
        self.client.force_login(self.admin)
        response = self.client.get(
            reverse(
                "k9_evento_resumen",
                kwargs={"empresa_slug": self.empresa.slug, "evento_id": evento.id},
            )
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Evento genérico")
        self.assertContains(response, "Información general")
        self.assertNotContains(response, "Novio")
        self.assertNotContains(response, "Novia")
