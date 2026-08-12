from decimal import Decimal
from datetime import time

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from documentos.models import DocumentoEvento
from itinerario.models import ActividadItinerario
from invitaciones.models import EventoBoda
from organizaciones.models import EmpresaSuscriptora, MembresiaEmpresa
from presupuesto.models import CategoriaGasto, GastoEvento, PagoEvento
from proveedores.models import Proveedor, ServicioEvento
from tareas.models import TareaEvento


@override_settings(MEDIA_ROOT='media/test/dirtec_k86_test_media')
class ServiceOperationsK86Tests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.empresa = EmpresaSuscriptora.objects.create(nombre_comercial='Empresa K86', slug='empresa-k86')
        self.planner = User.objects.create_user(username='planner-k86', password='test123')
        self.cliente = User.objects.create_user(username='cliente-k86', password='test123')
        self.proveedor_user = User.objects.create_user(username='proveedor-k86', password='test123')
        for user, rol in [(self.planner, 'WEDDING_PLANNER'), (self.cliente, 'CLIENTE'), (self.proveedor_user, 'PROVEEDOR')]:
            MembresiaEmpresa.objects.create(empresa=self.empresa, usuario=user, rol=rol)
        now = timezone.now()
        self.evento = EventoBoda.objects.create(
            empresa=self.empresa, wedding_planner=self.planner, nombre_evento='Boda K86',
            novio='A', novia='B', frase_portada='Test', mensaje_general='Test',
            fecha_misa=now, lugar_misa='Ceremonia', fecha_fiesta=now, lugar_fiesta='Recepcion',
        )
        self.evento.clientes.add(self.cliente)
        self.proveedor = Proveedor.objects.create(
            empresa=self.empresa, usuario=self.proveedor_user,
            nombre_comercial='Proveedor K86', tipo_proveedor='DECORACION',
        )
        self.servicio = ServicioEvento.objects.create(
            evento=self.evento, proveedor=self.proveedor, nombre_servicio='Decoracion K86',
            origen='MANUAL', modalidad='ADICIONAL',
        )
        self.categoria = CategoriaGasto.objects.create(nombre='Decoracion K86')

    def workspace(self):
        return reverse('colaboracion_workspace_servicio', args=[self.servicio.id])

    def test_planner_crea_tarea_vinculada(self):
        self.client.force_login(self.planner)
        response = self.client.post(reverse('colaboracion_k86_tarea_crear', args=[self.servicio.id]), {
            'titulo': 'Confirmar montaje', 'prioridad': 'ALTA', 'categoria': 'PROVEEDORES',
        })
        self.assertEqual(response.status_code, 302)
        tarea = TareaEvento.objects.get(titulo='Confirmar montaje')
        self.assertEqual(tarea.evento, self.evento)
        self.assertEqual(tarea.servicio_evento, self.servicio)
        self.assertEqual(tarea.responsable, self.planner)

    def test_planner_crea_cita_y_hereda_proveedor(self):
        self.client.force_login(self.planner)
        response = self.client.post(reverse('colaboracion_k86_actividad_crear', args=[self.servicio.id]), {
            'titulo': 'Prueba de montaje', 'fecha': '2026-09-01', 'hora_inicio': '16:30',
            'categoria': 'MONTAJE', 'prioridad': 'MEDIA',
        })
        self.assertEqual(response.status_code, 302)
        actividad = ActividadItinerario.objects.get(titulo='Prueba de montaje')
        self.assertEqual(actividad.servicio_evento, self.servicio)
        self.assertEqual(actividad.proveedor, self.proveedor)

    def test_documento_visible_cliente_se_muestra_en_workspace_cliente(self):
        DocumentoEvento.objects.create(
            evento=self.evento, servicio_evento=self.servicio, titulo='Plano aprobado',
            tipo_documento='PLANO', archivo=SimpleUploadedFile('plano.pdf', b'%PDF-1.4'),
            proveedor=self.proveedor, cargado_por=self.planner, visible_cliente=True,
        )
        DocumentoEvento.objects.create(
            evento=self.evento, servicio_evento=self.servicio, titulo='Contrato interno',
            tipo_documento='CONTRATO', archivo=SimpleUploadedFile('interno.pdf', b'%PDF-1.4'),
            proveedor=self.proveedor, cargado_por=self.planner, visible_cliente=False,
        )
        self.client.force_login(self.cliente)
        response = self.client.get(self.workspace())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Plano aprobado')
        self.assertNotContains(response, 'Contrato interno')

    def test_gasto_y_pago_quedan_contextualizados_y_ocultos_al_cliente(self):
        self.client.force_login(self.planner)
        response = self.client.post(reverse('colaboracion_k86_gasto_crear', args=[self.servicio.id]), {
            'categoria_id': self.categoria.id, 'concepto': 'Upgrade floral', 'monto_estimado': '4500.00',
        })
        self.assertEqual(response.status_code, 302)
        gasto = GastoEvento.objects.get(concepto='Upgrade floral')
        self.assertEqual(gasto.servicio_evento, self.servicio)
        self.assertEqual(gasto.proveedor, self.proveedor)
        response = self.client.post(reverse('colaboracion_k86_pago_crear', args=[self.servicio.id]), {
            'gasto_id': gasto.id, 'monto': '1500.00', 'metodo_pago': 'TRANSFERENCIA',
        })
        self.assertEqual(response.status_code, 302)
        pago = PagoEvento.objects.get(gasto=gasto)
        self.assertEqual(pago.monto, Decimal('1500.00'))
        self.assertEqual(pago.servicio_evento, self.servicio)
        self.client.force_login(self.cliente)
        response = self.client.get(self.workspace())
        self.assertNotContains(response, 'Upgrade floral')
        self.assertNotContains(response, 'Finanzas del servicio')

    def test_vincular_existente_no_duplica(self):
        tarea = TareaEvento.objects.create(evento=self.evento, titulo='Tarea legacy')
        self.client.force_login(self.planner)
        response = self.client.post(reverse('colaboracion_k86_vincular', args=[self.servicio.id]), {
            'tipo': 'TAREA', 'registro_id': tarea.id,
        })
        self.assertEqual(response.status_code, 302)
        tarea.refresh_from_db()
        self.assertEqual(tarea.servicio_evento, self.servicio)
        self.assertEqual(TareaEvento.objects.filter(titulo='Tarea legacy').count(), 1)

    def test_desvincular_no_elimina_registro(self):
        tarea = TareaEvento.objects.create(evento=self.evento, servicio_evento=self.servicio, titulo='Conservar')
        self.client.force_login(self.planner)
        response = self.client.post(reverse('colaboracion_k86_desvincular', args=[self.servicio.id]), {
            'tipo': 'TAREA', 'registro_id': tarea.id,
        })
        self.assertEqual(response.status_code, 302)
        tarea.refresh_from_db()
        self.assertIsNone(tarea.servicio_evento)
        self.assertTrue(TareaEvento.objects.filter(pk=tarea.pk).exists())

    def test_cliente_no_puede_crear_finanzas(self):
        self.client.force_login(self.cliente)
        response = self.client.post(reverse('colaboracion_k86_gasto_crear', args=[self.servicio.id]), {
            'categoria_id': self.categoria.id, 'concepto': 'No permitido', 'monto_estimado': '100',
        })
        self.assertEqual(response.status_code, 403)
        self.assertFalse(GastoEvento.objects.filter(concepto='No permitido').exists())

    def test_proveedor_ve_cita_pero_no_finanzas(self):
        ActividadItinerario.objects.create(
            evento=self.evento, servicio_evento=self.servicio, titulo='Montaje proveedor',
            categoria='MONTAJE', fecha=timezone.localdate(), hora_inicio=time(10, 0),
            proveedor=self.proveedor,
        )
        GastoEvento.objects.create(
            evento=self.evento, servicio_evento=self.servicio, categoria=self.categoria,
            proveedor=self.proveedor, concepto='Costo privado', monto_estimado=1000,
        )
        self.client.force_login(self.proveedor_user)
        response = self.client.get(self.workspace())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Montaje proveedor')
        self.assertNotContains(response, 'Costo privado')
        self.assertNotContains(response, 'Finanzas del servicio')

    def test_modelo_rechaza_servicio_de_otro_evento(self):
        now = timezone.now()
        otro = EventoBoda.objects.create(
            empresa=self.empresa, wedding_planner=self.planner, nombre_evento='Otra boda K86',
            novio='C', novia='D', frase_portada='Test', mensaje_general='Test',
            fecha_misa=now, lugar_misa='Ceremonia', fecha_fiesta=now, lugar_fiesta='Recepcion',
        )
        tarea = TareaEvento(evento=otro, servicio_evento=self.servicio, titulo='Cruce incorrecto')
        with self.assertRaises(ValidationError):
            tarea.full_clean()
