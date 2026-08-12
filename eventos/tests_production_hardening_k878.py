from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from documentos.models import DocumentoEvento
from invitaciones.models import EventoBoda, Grupoinvitacion
from organizaciones.models import EmpresaSuscriptora, MembresiaEmpresa
from presupuesto.models import PagoClienteEvento
from proveedores.models import Proveedor, ServicioEvento


@override_settings(MEDIA_ROOT='media/test/dirtec_k878_media')
class ProductionHardeningK878Tests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.empresa = EmpresaSuscriptora.objects.create(
            nombre_comercial='Empresa K878', slug='empresa-k878'
        )
        self.planner = User.objects.create_user(username='planner-k878', password='test123')
        self.cliente = User.objects.create_user(username='cliente-k878', password='test123')
        self.proveedor_user = User.objects.create_user(username='proveedor-k878', password='test123')
        for user, rol in [
            (self.planner, 'WEDDING_PLANNER'),
            (self.cliente, 'CLIENTE'),
            (self.proveedor_user, 'PROVEEDOR'),
        ]:
            MembresiaEmpresa.objects.create(empresa=self.empresa, usuario=user, rol=rol)
        now = timezone.now()
        self.evento = EventoBoda.objects.create(
            empresa=self.empresa,
            wedding_planner=self.planner,
            nombre_evento='Boda K878',
            novio='A', novia='B', frase_portada='Test', mensaje_general='Test',
            fecha_misa=now + timedelta(days=20), lugar_misa='Ceremonia',
            fecha_fiesta=now + timedelta(days=20), lugar_fiesta='Recepcion',
        )
        self.evento.clientes.add(self.cliente)
        self.proveedor = Proveedor.objects.create(
            empresa=self.empresa,
            usuario=self.proveedor_user,
            nombre_comercial='Proveedor K878',
            tipo_proveedor='BANQUETE',
        )
        self.servicio = ServicioEvento.objects.create(
            evento=self.evento,
            proveedor=self.proveedor,
            nombre_servicio='Banquete K878',
            origen='MANUAL',
        )

    def test_builder_deniega_cliente_y_proveedor(self):
        url = reverse('editor_invitacion_visual', args=[self.evento.id])
        self.client.force_login(self.cliente)
        self.assertEqual(self.client.get(url).status_code, 403)
        self.client.force_login(self.proveedor_user)
        self.assertEqual(self.client.get(url).status_code, 403)

    def test_builder_permite_planner_asignado(self):
        self.client.force_login(self.planner)
        self.assertEqual(
            self.client.get(reverse('editor_invitacion_visual', args=[self.evento.id])).status_code,
            200,
        )

    def test_proveedor_no_entra_a_portal_cliente(self):
        self.client.force_login(self.proveedor_user)
        response = self.client.get(reverse('cliente_dashboard'), {'evento': self.evento.id})
        self.assertEqual(response.status_code, 404)

    def test_roles_externos_no_entran_operacion_interna_por_url(self):
        internal_urls = [
            reverse('calendario_operativo') + f'?evento={self.evento.id}',
            reverse('mesas_visual') + f'?evento={self.evento.id}',
            reverse('exportar_resumen_evento') + f'?evento={self.evento.id}',
        ]
        for user in [self.cliente, self.proveedor_user]:
            self.client.force_login(user)
            for url in internal_urls:
                self.assertEqual(self.client.get(url).status_code, 403, url)

    def test_export_invitados_deniega_cliente_y_proveedor(self):
        url = reverse('exportar_excel') + f'?evento={self.evento.id}'
        self.client.force_login(self.cliente)
        self.assertEqual(self.client.get(url).status_code, 403)
        self.client.force_login(self.proveedor_user)
        self.assertEqual(self.client.get(url).status_code, 403)

    def test_marcar_envio_es_post_y_permiso_interno(self):
        grupo = Grupoinvitacion.objects.create(
            evento=self.evento,
            nombre_grupo='Familia K878',
            tipo='PERSONAL',
        )
        url = reverse('marcar_envio_invitacion', args=[grupo.id])
        self.client.force_login(self.planner)
        self.assertEqual(self.client.get(url).status_code, 405)
        self.assertEqual(self.client.post(url).status_code, 302)
        grupo.refresh_from_db()
        self.assertEqual(grupo.estado_envio, 'INVITACION_PREPARADA')

        self.client.force_login(self.cliente)
        self.assertEqual(self.client.post(url).status_code, 403)

    def test_documento_privado_no_se_descarga_por_cliente(self):
        doc = DocumentoEvento.objects.create(
            evento=self.evento,
            servicio_evento=self.servicio,
            titulo='Documento privado K878',
            tipo_documento='OTRO',
            archivo=SimpleUploadedFile('privado.pdf', b'%PDF-1.4 test', content_type='application/pdf'),
            visible_cliente=False,
            visible_proveedor=False,
            cargado_por=self.planner,
        )
        url = reverse('secure_documento_evento', args=[doc.id])
        self.client.force_login(self.cliente)
        self.assertEqual(self.client.get(url).status_code, 403)
        self.client.force_login(self.planner)
        self.assertEqual(self.client.get(url).status_code, 200)


    def test_planner_no_puede_mutar_evento_no_asignado_por_dashboard_actual(self):
        otro = EventoBoda.objects.create(
            empresa=self.empresa,
            nombre_evento='Evento no asignado K878',
            novio='X', novia='Y', frase_portada='Test', mensaje_general='Test',
            fecha_misa=timezone.now() + timedelta(days=25), lugar_misa='Ceremonia',
            fecha_fiesta=timezone.now() + timedelta(days=25), lugar_fiesta='Recepcion',
        )
        self.client.force_login(self.planner)
        response = self.client.post(
            reverse('dashboard'),
            {
                'accion': 'agregar_servicio_evento',
                'evento_id': otro.id,
                'nombre_servicio': 'Intento no autorizado',
            },
        )
        self.assertEqual(response.status_code, 403)
        self.assertFalse(
            ServicioEvento.objects.filter(
                evento=otro,
                nombre_servicio='Intento no autorizado',
            ).exists()
        )

    def test_planner_no_puede_usar_proveedor_oculto_o_ajeno_en_dashboard_actual(self):
        oculto = Proveedor.objects.create(
            empresa=self.empresa,
            nombre_comercial='Proveedor interno oculto',
            tipo_proveedor='OTROS',
            visible_para_wedding_planners=False,
        )
        otra_empresa = EmpresaSuscriptora.objects.create(
            nombre_comercial='Otra empresa K878',
            slug='otra-empresa-k878',
        )
        ajeno = Proveedor.objects.create(
            empresa=otra_empresa,
            nombre_comercial='Proveedor ajeno K878',
            tipo_proveedor='OTROS',
            visible_para_wedding_planners=True,
        )
        self.client.force_login(self.planner)

        for proveedor in (oculto, ajeno):
            response = self.client.post(
                reverse('dashboard'),
                {
                    'accion': 'agregar_servicio_evento',
                    'evento_id': self.evento.id,
                    'proveedor_id': proveedor.id,
                    'nombre_servicio': 'Servicio bloqueado',
                },
            )
            self.assertEqual(response.status_code, 404)

        self.assertFalse(
            ServicioEvento.objects.filter(
                evento=self.evento,
                nombre_servicio='Servicio bloqueado',
            ).exists()
        )

    def test_planner_dashboard_actual_solo_lista_proveedores_visibles(self):
        visible = Proveedor.objects.create(
            empresa=self.empresa,
            nombre_comercial='Proveedor visible K878',
            tipo_proveedor='OTROS',
            visible_para_wedding_planners=True,
        )
        oculto = Proveedor.objects.create(
            empresa=self.empresa,
            nombre_comercial='Proveedor oculto K878',
            tipo_proveedor='OTROS',
            visible_para_wedding_planners=False,
        )
        self.client.force_login(self.planner)
        response = self.client.get(
            reverse('dashboard') + f'?evento={self.evento.id}'
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, visible.nombre_comercial)
        self.assertNotContains(response, oculto.nombre_comercial)

    def test_pago_cliente_no_es_visible_al_proveedor(self):
        pago = PagoClienteEvento.objects.create(
            evento=self.evento,
            registrado_por=self.cliente,
            concepto='Anticipo privado',
            monto=Decimal('1234.56'),
            comprobante=SimpleUploadedFile('pago.jpg', b'fake', content_type='image/jpeg'),
        )
        url = reverse('secure_pago_cliente_comprobante', args=[pago.id])
        self.client.force_login(self.proveedor_user)
        self.assertEqual(self.client.get(url).status_code, 403)
        self.client.force_login(self.cliente)
        self.assertEqual(self.client.get(url).status_code, 200)
