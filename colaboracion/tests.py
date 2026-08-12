from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import NoReverseMatch, reverse
from django.utils import timezone

from invitaciones.models import EventoBoda
from organizaciones.models import EmpresaSuscriptora, MembresiaEmpresa
from proveedores.models import Proveedor, ServicioEvento


class CollaborationLegacyRetirementK878Tests(TestCase):
    """Contrato vigente: ExpedienteServicio permanece en esquema, pero sus rutas legacy ya no son públicas."""

    LEGACY_NAMES = [
        'colaboracion_cliente_crear_solicitud',
        'colaboracion_enviar_mensaje',
        'colaboracion_planner_asignar_proveedor',
        'colaboracion_proveedor_cotizar',
        'colaboracion_planner_decidir_cotizacion',
        'colaboracion_planner_enviar_propuesta',
        'colaboracion_cliente_responder_propuesta',
        'colaboracion_planner_confirmar_proveedor',
    ]

    def setUp(self):
        User = get_user_model()
        self.empresa = EmpresaSuscriptora.objects.create(
            nombre_comercial='Empresa Collab K878', slug='empresa-collab-k878'
        )
        self.planner = User.objects.create_user(username='planner-collab-k878', password='test123')
        self.proveedor_user = User.objects.create_user(username='provider-collab-k878', password='test123')
        MembresiaEmpresa.objects.create(
            empresa=self.empresa, usuario=self.planner, rol='WEDDING_PLANNER'
        )
        MembresiaEmpresa.objects.create(
            empresa=self.empresa, usuario=self.proveedor_user, rol='PROVEEDOR'
        )
        self.evento = EventoBoda.objects.create(
            empresa=self.empresa,
            wedding_planner=self.planner,
            novio='A', novia='B', frase_portada='Test', mensaje_general='Test',
            fecha_misa=timezone.now(), lugar_misa='Ceremonia',
            fecha_fiesta=timezone.now(), lugar_fiesta='Recepcion',
        )
        self.proveedor = Proveedor.objects.create(
            empresa=self.empresa,
            usuario=self.proveedor_user,
            nombre_comercial='Proveedor Collab K878',
            tipo_proveedor='DECORACION',
        )
        self.servicio = ServicioEvento.objects.create(
            evento=self.evento,
            proveedor=self.proveedor,
            nombre_servicio='Decoración K878',
            origen='MANUAL',
        )

    def test_rutas_legacy_no_se_publican(self):
        for name in self.LEGACY_NAMES:
            with self.assertRaises(NoReverseMatch, msg=name):
                reverse(name)

    def test_workspace_servicio_es_la_ruta_oficial(self):
        self.client.force_login(self.planner)
        response = self.client.get(
            reverse('colaboracion_workspace_servicio', args=[self.servicio.id]),
            {'canal': 'PLANNER_PROVEEDOR'},
        )
        self.assertEqual(response.status_code, 200)
