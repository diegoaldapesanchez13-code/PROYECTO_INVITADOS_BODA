from pathlib import Path

from django.test import SimpleTestCase


class ProviderPortalLayoutK7Tests(SimpleTestCase):
    def test_portal_has_dedicated_css_and_no_dashboard_css(self):
        root = Path(__file__).resolve().parents[1]
        template = (
            root
            / "invitaciones/templates/invitaciones/portal_proveedor.html"
        ).read_text(encoding="utf-8")
        self.assertIn("portal_proveedor_v3.css", template)
        self.assertNotIn("dashboard.css", template)
        self.assertNotIn('name="visible_cliente"', template)

    def test_provider_css_is_responsive(self):
        root = Path(__file__).resolve().parents[1]
        css = (
            root
            / "invitaciones/static/invitaciones/css/portal_proveedor_v3.css"
        ).read_text(encoding="utf-8")
        self.assertIn("@media (max-width: 680px)", css)
        self.assertIn("@media (max-width: 480px)", css)
