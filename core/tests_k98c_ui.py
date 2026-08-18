from pathlib import Path

from django.conf import settings
from django.template.loader import get_template
from django.test import SimpleTestCase
from django.urls import reverse


class OperationalLifecycleUITests(SimpleTestCase):
    TEMPLATE_NAMES = [
        'invitaciones/dashboard.html',
        'invitaciones/dashboard/v3/_servicios.html',
        'invitaciones/dashboard/v3/_tareas.html',
        'invitaciones/dashboard/v3/_agenda.html',
        'invitaciones/dashboard/v3/_documentos.html',
        'invitaciones/dashboard/v3/_finanzas.html',
        'invitaciones/dashboard/partials/_operacion_gestion.html',
    ]

    def _source(self, relative):
        return (Path(settings.BASE_DIR) / relative).read_text(encoding='utf-8')

    def test_templates_compile(self):
        for name in self.TEMPLATE_NAMES:
            with self.subTest(template=name):
                get_template(name)

    def test_dashboard_loads_lifecycle_stylesheet(self):
        source = self._source('invitaciones/templates/invitaciones/dashboard.html')
        self.assertIn('k98_lifecycle.css', source)

    def test_legacy_operation_ui_no_longer_posts_hard_delete_actions(self):
        source = self._source('invitaciones/templates/invitaciones/dashboard/partials/_operacion_gestion.html')
        for action in (
            'eliminar_servicio_evento',
            'eliminar_tarea_evento',
            'eliminar_gasto_evento',
            'eliminar_pago_evento',
            'eliminar_documento_evento',
        ):
            with self.subTest(action=action):
                self.assertNotIn(f'value="{action}"', source)

    def test_legacy_document_link_uses_secure_view(self):
        source = self._source('invitaciones/templates/invitaciones/dashboard/partials/_operacion_gestion.html')
        self.assertIn("secure_documento_evento", source)
        self.assertNotIn('documento.archivo.url', source)

    def test_v3_services_exposes_cancel_archive_restore(self):
        source = self._source('invitaciones/templates/invitaciones/dashboard/v3/_servicios.html')
        self.assertIn('eventos_servicio_cancelar', source)
        self.assertIn('eventos_servicio_archivar', source)
        self.assertIn('eventos_servicio_desarchivar', source)
        self.assertIn('data-filter-field="lifecycle"', source)

    def test_v3_tasks_exposes_cancel_archive_restore(self):
        source = self._source('invitaciones/templates/invitaciones/dashboard/v3/_tareas.html')
        self.assertIn('eventos_tarea_cancelar', source)
        self.assertIn('eventos_tarea_archivar', source)
        self.assertIn('eventos_tarea_desarchivar', source)

    def test_v3_agenda_exposes_lifecycle_actions(self):
        source = self._source('invitaciones/templates/invitaciones/dashboard/v3/_agenda.html')
        self.assertIn('eventos_actividad_cancelar', source)
        self.assertIn('eventos_actividad_archivar', source)
        self.assertIn('eventos_actividad_desarchivar', source)

    def test_v3_documents_use_secure_download_and_archive(self):
        source = self._source('invitaciones/templates/invitaciones/dashboard/v3/_documentos.html')
        self.assertIn('secure_documento_evento', source)
        self.assertIn('eventos_documento_archivar', source)
        self.assertIn('eventos_documento_desarchivar', source)

    def test_v3_finance_annuls_payments_instead_of_deleting(self):
        source = self._source('invitaciones/templates/invitaciones/dashboard/v3/_finanzas.html')
        self.assertIn('eventos_pago_anular', source)
        self.assertIn('eventos_gasto_cancelar', source)
        self.assertIn('eventos_gasto_archivar', source)
        self.assertIn('eventos_gasto_desarchivar', source)
        self.assertNotIn('eliminar_pago_evento', source)
        self.assertNotIn('eliminar_gasto_evento', source)

    def test_lifecycle_routes_reverse(self):
        samples = (
            ('eventos_servicio_cancelar', {'empresa_slug': 'empresa', 'servicio_id': 1}),
            ('eventos_tarea_archivar', {'empresa_slug': 'empresa', 'tarea_id': 1}),
            ('eventos_actividad_desarchivar', {'empresa_slug': 'empresa', 'actividad_id': 1}),
            ('eventos_documento_archivar', {'empresa_slug': 'empresa', 'documento_id': 1}),
            ('eventos_gasto_cancelar', {'empresa_slug': 'empresa', 'gasto_id': 1}),
            ('eventos_pago_anular', {'empresa_slug': 'empresa', 'pago_id': 1}),
        )
        for name, kwargs in samples:
            with self.subTest(route=name):
                self.assertTrue(reverse(name, kwargs=kwargs).startswith('/eventos/'))

    def test_dashboard_v3_builds_historical_collections(self):
        source = self._source('eventos/dashboard_v3.py')
        for name in (
            'servicios_gestion_v3',
            'tareas_gestion_v3',
            'actividades_historial_v3',
            'documentos_archivados_v3',
        ):
            with self.subTest(name=name):
                self.assertIn(name, source)
