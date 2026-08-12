import re
from pathlib import Path

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from invitaciones.models import EventoBoda, Grupoinvitacion, Invitado
from mesas.models import AsignacionMesa, Mesa


ROOT = Path(__file__).resolve().parents[1]


class ProductAcceptanceR8Tests(TestCase):
    def setUp(self):
        self.evento = EventoBoda.objects.create(
            novio="Diego",
            novia="Fernanda",
            frase_portada="Test",
            mensaje_general="Test",
            fecha_misa=timezone.now(),
            lugar_misa="Ceremonia",
            fecha_fiesta=timezone.now(),
            lugar_fiesta="Recepción",
        )
        User = get_user_model()
        self.user = User.objects.create_superuser(
            username="r8_admin",
            password="test123",
        )
        self.client.force_login(self.user)

    def test_guest_dashboard_uses_real_table_assignment_only(self):
        grupo = Grupoinvitacion.objects.create(
            evento=self.evento,
            nombre_grupo="Familia R8",
            tipo="FAMILIAR",
        )
        invitado = Invitado.objects.create(
            grupo=grupo,
            nombre="Ana",
            asistira=True,
        )
        mesa = Mesa.objects.create(
            evento=self.evento,
            nombre="Mesa Real",
            capacidad=10,
        )
        AsignacionMesa.objects.create(
            mesa=mesa,
            invitado=invitado,
        )

        response = self.client.get(
            reverse("dashboard")
            + f"?evento={self.evento.id}#invitados"
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'name="mesa_invitado"')
        self.assertNotContains(response, 'Mesa de referencia')
        self.assertContains(response, 'Mesa Real')
        self.assertContains(response, 'Herramientas → Mesas')

    def test_retired_rsvp_template_has_no_second_contract(self):
        source = (
            ROOT
            / "invitaciones/templates/invitaciones/partials/_section_rsvp.html"
        ).read_text(encoding="utf-8")
        for forbidden in (
            "acompanantes_adultos",
            "acompanantes_ninos",
            "restricciones_alimentarias",
            "alergias",
            "requiere_menu_infantil",
        ):
            self.assertNotIn(forbidden, source)

    def test_dashboard_buttons_have_explicit_type(self):
        paths = [
            ROOT / "invitaciones/templates/invitaciones/dashboard.html",
            *(
                ROOT
                / "invitaciones/templates/invitaciones/dashboard/partials"
            ).glob("*.html"),
        ]
        for path in paths:
            source = path.read_text(encoding="utf-8", errors="ignore")
            for match in re.finditer(
                r"<button\b([^>]*)>",
                source,
                flags=re.IGNORECASE,
            ):
                self.assertRegex(
                    match.group(1),
                    r'\btype\s*=\s*["\'](?:button|submit)["\']',
                    msg=f"Button without explicit type in {path.name}",
                )

    def test_rsvp_authority_is_individual(self):
        grupo = Grupoinvitacion.objects.create(
            evento=self.evento,
            nombre_grupo="Familia RSVP",
            tipo="FAMILIAR",
        )
        ana = Invitado.objects.create(grupo=grupo, nombre="Ana")
        luis = Invitado.objects.create(grupo=grupo, nombre="Luis")
        ana.asistira = True
        ana.save(update_fields=["asistira"])
        ana.refresh_from_db()
        luis.refresh_from_db()
        self.assertIs(ana.asistira, True)
        self.assertIsNone(luis.asistira)
