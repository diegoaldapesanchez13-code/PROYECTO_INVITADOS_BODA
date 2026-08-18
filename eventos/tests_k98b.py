from datetime import time
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from auditoria.models import RegistroAuditoria
from documentos.models import DocumentoEvento
from eventos.models import ParticipanteEvento
from invitaciones.models import EventoBoda
from itinerario.models import ActividadItinerario
from organizaciones.models import EmpresaSuscriptora, MembresiaEmpresa
from presupuesto.models import CategoriaGasto, GastoEvento, PagoEvento
from proveedores.models import Proveedor, ServicioEvento
from tareas.models import TareaEvento


class OperationalLifecycleEndpointsK98BTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.empresa = EmpresaSuscriptora.objects.create(nombre_comercial='Empresa K98B', slug='empresa-k98b')
        self.empresa_b = EmpresaSuscriptora.objects.create(nombre_comercial='Empresa B K98B', slug='empresa-b-k98b')
        self.admin = User.objects.create_user(username='admin-k98b', password='test123')
        self.admin_b = User.objects.create_user(username='admin-b-k98b', password='test123')
        self.planner = User.objects.create_user(username='planner-k98b', password='test123')
        self.cliente = User.objects.create_user(username='cliente-k98b', password='test123')
        self.proveedor_user = User.objects.create_user(username='proveedor-k98b', password='test123')

        MembresiaEmpresa.objects.create(empresa=self.empresa, usuario=self.admin, rol='ADMIN_EMPRESA')
        MembresiaEmpresa.objects.create(empresa=self.empresa_b, usuario=self.admin_b, rol='ADMIN_EMPRESA')
        MembresiaEmpresa.objects.create(empresa=self.empresa, usuario=self.planner, rol='WEDDING_PLANNER')
        MembresiaEmpresa.objects.create(empresa=self.empresa, usuario=self.cliente, rol='CLIENTE')
        MembresiaEmpresa.objects.create(empresa=self.empresa, usuario=self.proveedor_user, rol='PROVEEDOR')

        now = timezone.now()
        self.evento = EventoBoda.objects.create(
            empresa=self.empresa,
            nombre_evento='Evento K98B',
            novio='Cliente',
            novia='Principal',
            frase_portada='Celebracion',
            mensaje_general='Mensaje',
            fecha_misa=now,
            lugar_misa='Ceremonia',
            fecha_fiesta=now,
            lugar_fiesta='Recepcion',
            wedding_planner=self.planner,
        )
        self.evento.clientes.add(self.cliente)
        self.evento_b = EventoBoda.objects.create(
            empresa=self.empresa_b,
            nombre_evento='Evento B K98B',
            novio='Otro',
            novia='Cliente',
            frase_portada='Celebracion',
            mensaje_general='Mensaje',
            fecha_misa=now,
            lugar_misa='Ceremonia B',
            fecha_fiesta=now,
            lugar_fiesta='Recepcion B',
        )
        self.proveedor = Proveedor.objects.create(
            empresa=self.empresa,
            usuario=self.proveedor_user,
            nombre_comercial='Proveedor K98B',
        )
        self.servicio = ServicioEvento.objects.create(
            evento=self.evento,
            proveedor=self.proveedor,
            nombre_servicio='DJ K98B',
            estado='CONTRATADO',
            estado_comercial='CONTRATADO',
            estado_operativo='PROGRAMADO',
        )
        self.servicio_b = ServicioEvento.objects.create(
            evento=self.evento_b,
            nombre_servicio='Servicio B K98B',
            estado='CONTRATADO',
            estado_comercial='CONTRATADO',
            estado_operativo='PROGRAMADO',
        )
        self.tarea = TareaEvento.objects.create(evento=self.evento, servicio_evento=self.servicio, titulo='Tarea K98B')
        self.actividad = ActividadItinerario.objects.create(
            evento=self.evento,
            servicio_evento=self.servicio,
            tipo='CITA',
            titulo='Cita K98B',
            fecha=timezone.localdate(),
            hora_inicio=time(10, 0),
        )
        self.documento = DocumentoEvento.objects.create(
            evento=self.evento,
            servicio_evento=self.servicio,
            titulo='Documento K98B',
            archivo='documentos/eventos/k98b.pdf',
        )
        self.categoria = CategoriaGasto.objects.create(nombre='Operacion K98B')
        self.gasto = GastoEvento.objects.create(
            evento=self.evento,
            servicio_evento=self.servicio,
            categoria=self.categoria,
            concepto='Gasto K98B',
            monto_estimado=Decimal('10000.00'),
            monto_real=Decimal('9000.00'),
        )
        self.pago = PagoEvento.objects.create(gasto=self.gasto, monto=Decimal('2000.00'))
        # El signal legacy puede crear/actualizar el participante. Para estas pruebas
        # la autorizacion financiera se controla de forma explicita.
        ParticipanteEvento.objects.update_or_create(
            evento=self.evento,
            usuario=self.planner,
            rol='PLANNER',
            defaults={'activo': True, 'puede_ver_finanzas': False},
        )

    def url(self, name, objeto_id, *, empresa=None):
        empresa = empresa or self.empresa
        return reverse(name, args=[empresa.slug, objeto_id])

    def test_acciones_requieren_post(self):
        self.client.force_login(self.admin)
        response = self.client.get(self.url('eventos_servicio_cancelar', self.servicio.id))
        self.assertEqual(response.status_code, 405)
        self.servicio.refresh_from_db()
        self.assertEqual(self.servicio.estado_operativo, 'PROGRAMADO')

    def test_anonimo_redirige_login(self):
        response = self.client.post(self.url('eventos_servicio_cancelar', self.servicio.id))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)

    def test_admin_cancela_servicio_y_audita(self):
        self.client.force_login(self.admin)
        response = self.client.post(self.url('eventos_servicio_cancelar', self.servicio.id), {'motivo': 'Ya no aplica'})
        self.assertEqual(response.status_code, 302)
        self.servicio.refresh_from_db()
        self.assertEqual(self.servicio.estado_operativo, 'CANCELADO')
        self.assertTrue(ServicioEvento.objects.filter(pk=self.servicio.id).exists())
        self.assertTrue(RegistroAuditoria.objects.filter(accion='servicio_evento.cancelar', objeto_id=str(self.servicio.id)).exists())

    def test_servicio_cross_tenant_devuelve_404(self):
        self.client.force_login(self.admin)
        response = self.client.post(self.url('eventos_servicio_cancelar', self.servicio_b.id))
        self.assertEqual(response.status_code, 404)
        self.servicio_b.refresh_from_db()
        self.assertEqual(self.servicio_b.estado_operativo, 'PROGRAMADO')

    def test_cliente_no_cancela_servicio(self):
        self.client.force_login(self.cliente)
        response = self.client.post(self.url('eventos_servicio_cancelar', self.servicio.id))
        self.assertEqual(response.status_code, 403)

    def test_proveedor_no_cancela_servicio_por_endpoint_interno(self):
        self.client.force_login(self.proveedor_user)
        response = self.client.post(self.url('eventos_servicio_cancelar', self.servicio.id))
        self.assertEqual(response.status_code, 403)

    def test_planner_asignado_cancela_tarea(self):
        self.client.force_login(self.planner)
        response = self.client.post(self.url('eventos_tarea_cancelar', self.tarea.id), {'motivo': 'Cambio operativo'})
        self.assertEqual(response.status_code, 302)
        self.tarea.refresh_from_db()
        self.assertEqual(self.tarea.estado, 'CANCELADA')

    def test_archivar_tarea_pendiente_no_modifica_registro(self):
        self.client.force_login(self.admin)
        response = self.client.post(self.url('eventos_tarea_archivar', self.tarea.id))
        self.assertEqual(response.status_code, 302)
        self.tarea.refresh_from_db()
        self.assertIsNone(self.tarea.archivado_en)
        self.assertEqual(self.tarea.estado, 'PENDIENTE')

    def test_cancelar_y_archivar_actividad(self):
        self.client.force_login(self.admin)
        self.client.post(self.url('eventos_actividad_cancelar', self.actividad.id), {'motivo': 'Cancelada'})
        response = self.client.post(self.url('eventos_actividad_archivar', self.actividad.id))
        self.assertEqual(response.status_code, 302)
        self.actividad.refresh_from_db()
        self.assertEqual(self.actividad.estado, 'CANCELADA')
        self.assertIsNotNone(self.actividad.archivado_en)

    def test_archivar_documento_conserva_archivo(self):
        self.client.force_login(self.admin)
        archivo = self.documento.archivo.name
        response = self.client.post(self.url('eventos_documento_archivar', self.documento.id), {'motivo': 'Historico'})
        self.assertEqual(response.status_code, 302)
        self.documento.refresh_from_db()
        self.assertIsNotNone(self.documento.archivado_en)
        self.assertEqual(self.documento.archivo.name, archivo)

    def test_desarchivar_no_reactiva_servicio_cancelado(self):
        self.client.force_login(self.admin)
        self.client.post(self.url('eventos_servicio_cancelar', self.servicio.id))
        self.client.post(self.url('eventos_servicio_archivar', self.servicio.id))
        response = self.client.post(self.url('eventos_servicio_desarchivar', self.servicio.id))
        self.assertEqual(response.status_code, 302)
        self.servicio.refresh_from_db()
        self.assertIsNone(self.servicio.archivado_en)
        self.assertEqual(self.servicio.estado_operativo, 'CANCELADO')

    def test_planner_sin_permiso_financiero_no_anula_pago(self):
        self.client.force_login(self.planner)
        response = self.client.post(self.url('eventos_pago_anular', self.pago.id), {'motivo': 'Error'})
        self.assertEqual(response.status_code, 403)
        self.pago.refresh_from_db()
        self.assertEqual(self.pago.estado, 'ACTIVO')

    def test_planner_con_permiso_financiero_anula_pago(self):
        ParticipanteEvento.objects.filter(evento=self.evento, usuario=self.planner, rol='PLANNER').update(puede_ver_finanzas=True)
        self.client.force_login(self.planner)
        response = self.client.post(self.url('eventos_pago_anular', self.pago.id), {'motivo': 'Duplicado'})
        self.assertEqual(response.status_code, 302)
        self.pago.refresh_from_db()
        self.assertEqual(self.pago.estado, 'ANULADO')
        self.assertTrue(RegistroAuditoria.objects.filter(accion='pago_evento.anular', objeto_id=str(self.pago.id)).exists())

    def test_admin_anula_pago(self):
        self.client.force_login(self.admin)
        response = self.client.post(self.url('eventos_pago_anular', self.pago.id), {'motivo': 'Captura duplicada'})
        self.assertEqual(response.status_code, 302)
        self.pago.refresh_from_db()
        self.assertEqual(self.pago.estado, 'ANULADO')

    def test_gasto_con_pago_activo_no_se_cancela_desde_endpoint(self):
        self.client.force_login(self.admin)
        response = self.client.post(self.url('eventos_gasto_cancelar', self.gasto.id), {'motivo': 'Cancelar'})
        self.assertEqual(response.status_code, 302)
        self.gasto.refresh_from_db()
        self.assertEqual(self.gasto.estado, 'PENDIENTE')

    def test_gasto_se_cancela_despues_de_anular_pago(self):
        self.client.force_login(self.admin)
        self.client.post(self.url('eventos_pago_anular', self.pago.id), {'motivo': 'Anular primero'})
        response = self.client.post(self.url('eventos_gasto_cancelar', self.gasto.id), {'motivo': 'Ya no aplica'})
        self.assertEqual(response.status_code, 302)
        self.gasto.refresh_from_db()
        self.assertEqual(self.gasto.estado, 'CANCELADO')

    def test_cliente_no_accede_accion_financiera(self):
        self.client.force_login(self.cliente)
        response = self.client.post(self.url('eventos_pago_anular', self.pago.id))
        self.assertEqual(response.status_code, 403)

    def test_redireccion_operativa_es_contextual_y_no_usa_next(self):
        self.client.force_login(self.admin)
        response = self.client.post(
            self.url('eventos_tarea_cancelar', self.tarea.id) + '?next=https://evil.example/',
            {'motivo': 'Prueba'},
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('empresa_dashboard', kwargs={'empresa_slug': self.empresa.slug}), response.url)
        self.assertIn(f'evento={self.evento.id}', response.url)
        self.assertNotIn('evil.example', response.url)
