from pathlib import Path

from django.test import SimpleTestCase


class OperationsLayoutK51Tests(SimpleTestCase):
    def test_operations_css_has_responsive_single_column_fallback(self):
        root = Path(__file__).resolve().parents[1]
        css = (
            root
            / "invitaciones/static/invitaciones/css/dashboard.css"
        ).read_text(encoding="utf-8")

        self.assertIn(
            "PHASE K.5.1",
            css,
        )
        self.assertIn(
            "@media (max-width: 1280px)",
            css,
        )
        self.assertIn(
            ".operation-manager .operation-panel-grid",
            css,
        )

    def test_task_form_exposes_time_fields(self):
        root = Path(__file__).resolve().parents[1]
        template = (
            root
            / "invitaciones/templates/invitaciones/dashboard/partials/_operacion_gestion.html"
        ).read_text(encoding="utf-8")

        self.assertIn(
            'name="hora_inicio_tarea"',
            template,
        )
        self.assertIn(
            'name="hora_fin_tarea"',
            template,
        )
