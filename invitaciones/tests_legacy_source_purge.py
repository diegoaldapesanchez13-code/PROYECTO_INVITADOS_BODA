from django.test import SimpleTestCase
import invitaciones.views as views

class LegacyPythonSourcePurgeTests(SimpleTestCase):
    def test_legacy_runtime_entry_points_are_gone(self):
        for name in ("editor_invitacion_visual","ver_invitacion","guardar_diseno_invitacion_visual","publicar_diseno_invitacion_visual","componentes_invitacion_visual","componente_invitacion_visual"):
            self.assertFalse(hasattr(views,name),name)
    def test_dashboard_remains(self):
        self.assertTrue(hasattr(views,"dashboard"))
