from pathlib import Path

from django.test import SimpleTestCase


class ClientPortalLayoutK6Tests(SimpleTestCase):
    def test_portal_uses_dedicated_client_stylesheet(self):
        root = Path(__file__).resolve().parents[1]
        template = (
            root
            / "invitaciones/templates/invitaciones/portal_cliente.html"
        ).read_text(encoding="utf-8")
        self.assertIn(
            "portal_cliente_v3.css",
            template,
        )
        self.assertNotIn(
            "dashboard.css",
            template,
        )

    def test_client_css_contains_mobile_breakpoints(self):
        root = Path(__file__).resolve().parents[1]
        css = (
            root
            / "invitaciones/static/invitaciones/css/portal_cliente_v3.css"
        ).read_text(encoding="utf-8")
        self.assertIn(
            "@media (max-width: 680px)",
            css,
        )
        self.assertIn(
            "@media (max-width: 480px)",
            css,
        )
