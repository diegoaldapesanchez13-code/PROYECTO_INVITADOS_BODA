from django.test import SimpleTestCase
from django.urls import NoReverseMatch, reverse


class CollaborationK811HistoricalContractRetiredTests(SimpleTestCase):
    """K.8.1.1 queda documentado como historial; sus endpoints fueron retirados en K.8.7.8."""

    def test_endpoints_legacy_k811_permanecen_retirados(self):
        for name in [
            'colaboracion_cliente_crear_solicitud',
            'colaboracion_planner_asignar_proveedor',
            'colaboracion_planner_enviar_propuesta',
            'colaboracion_enviar_mensaje',
        ]:
            with self.assertRaises(NoReverseMatch):
                reverse(name)
