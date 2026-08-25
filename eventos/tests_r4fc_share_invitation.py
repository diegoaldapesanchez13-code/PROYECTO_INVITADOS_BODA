from pathlib import Path

from django.test import SimpleTestCase
from django.template.loader import get_template


class GuestShareActionsR4Tests(SimpleTestCase):
    def test_guest_template_keeps_uuid_public_invitation_route(self):
        template = get_template("eventos/workspace/invitados.html")
        content = Path(template.origin.name).read_text(encoding="utf-8")
        self.assertIn("{% url 'ver_invitacion' item.codigo as invitation_path %}", content)
        self.assertIn("data-copy-invitation", content)
        self.assertIn("data-whatsapp-invitation", content)
        self.assertIn("data-workspace-native", content)

    def test_share_runtime_reinitializes_after_workspace_navigation(self):
        root = Path(__file__).resolve().parent
        runtime = (
            root / "static" / "eventos" / "js" / "workspace_guests_share_r4.js"
        ).read_text(encoding="utf-8")
        self.assertIn("dirtec:workspace:loaded", runtime)
        self.assertIn("navigator.clipboard", runtime)
        self.assertIn("https://wa.me/?text=", runtime)
        self.assertIn("window.location.origin", runtime)
