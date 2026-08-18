from datetime import time
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from auditoria.models import RegistroAuditoria
from core.services.ciclo_vida_operativo import (
    anular_pago_evento,
    archivar_actividad_itinerario,
    archivar_documento_evento,
    archivar_gasto_evento,
    archivar_servicio_evento,
    archivar_tarea_evento,
    cancelar_actividad_itinerario,
    cancelar_gasto_evento,
    cancelar_servicio_evento,
    cancelar_tarea_evento,
    desarchivar_actividad_itinerario,
    desarchivar_documento_evento,
    desarchivar_gasto_evento,
    desarchivar_servicio_evento,
    desarchivar_tarea_evento,
)
from documentos.models import DocumentoEvento
from eventos.models import ContratoEvento
from invitaciones.models import EventoBoda
from itinerario.models import ActividadItinerario
from organizaciones.models import EmpresaSuscriptora
from presupuesto.models import CategoriaGasto, GastoEvento, PagoEvento
from presupuesto.services import obtener_resumen_financiero_evento
from proveedores.models import ServicioEvento
from tareas.models import TareaEvento


class CicloVidaOperativoK98ATests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username='operador-k98a', password='test123')
        self.empresa = EmpresaSuscriptora.objects.create(
            nombre_comercial='Empresa K98A',
            slug='empresa-k98a',
        )
        self.evento = EventoBoda.objects.create(
            empresa=self.empresa,
            nombre_evento='Evento K98A',
            novio='Cliente',
            novia='Principal',
            frase_portada='Celebracion',
            mensaje_general='Mensaje',
            fecha_misa=timezone.now(),
            lugar_misa='Ceremonia',
            fecha_fiesta=timezone.now(),
            lugar_fiesta='Recepcion',
        )
        self.servicio = ServicioEvento.objects.create(
            evento=self.evento,
            nombre_servicio='DJ K98A',
            estado='CONTRATADO',
            estado_comercial='CONTRATADO',
            estado_operativo='PROGRAMADO',
        )
        self.tarea = TareaEvento.objects.create(
            evento=self.evento,
            servicio_evento=self.servicio,
            titulo='Confirmar montaje',
        )
        self.actividad = ActividadItinerario.objects.create(
            evento=self.evento,
            servicio_evento=self.servicio,
            tipo='CITA',
            titulo='Cita proveedor',
            fecha=timezone.localdate(),
            hora_inicio=time(10, 0),
        )
        self.documento = DocumentoEvento.objects.create(
            evento=self.evento,
            servicio_evento=self.servicio,
            titulo='Documento prueba',
            archivo='documentos/eventos/prueba.pdf',
        )
        self.categoria = CategoriaGasto.objects.create(nombre='Operacion K98A')
        self.gasto = GastoEvento.objects.create(
            evento=self.evento,
            servicio_evento=self.servicio,
            categoria=self.categoria,
            concepto='Costo DJ',
            monto_estimado=Decimal('20000.00'),
            monto_real=Decimal('18000.00'),
        )

    def test_cancelar_servicio_conserva_registro_y_audita(self):
        servicio_id = self.servicio.id
        cancelar_servicio_evento(self.servicio, actor=self.user, motivo='Cliente cancelo el servicio')
        self.servicio.refresh_from_db()
        self.assertEqual(self.servicio.id, servicio_id)
        self.assertEqual(self.servicio.estado, 'CANCELADO')
        self.assertEqual(self.servicio.estado_comercial, 'CANCELADO')
        self.assertEqual(self.servicio.estado_operativo, 'CANCELADO')
        self.assertEqual(self.servicio.cancelado_por, self.user)
        self.assertIsNotNone(self.servicio.cancelado_en)
        self.assertTrue(RegistroAuditoria.objects.filter(accion='servicio_evento.cancelar', objeto_id=str(servicio_id)).exists())

    def test_cancelar_servicio_es_idempotente(self):
        cancelar_servicio_evento(self.servicio, actor=self.user)
        cancelar_servicio_evento(self.servicio, actor=self.user)
        self.assertEqual(RegistroAuditoria.objects.filter(accion='servicio_evento.cancelar', objeto_id=str(self.servicio.id)).count(), 1)

    def test_servicio_activo_no_se_archiva(self):
        with self.assertRaises(ValidationError):
            archivar_servicio_evento(self.servicio, actor=self.user)

    def test_servicio_cancelado_se_archiva_y_restaurar_no_reactiva(self):
        cancelar_servicio_evento(self.servicio, actor=self.user)
        archivar_servicio_evento(self.servicio, actor=self.user)
        self.servicio.refresh_from_db()
        self.assertIsNotNone(self.servicio.archivado_en)
        desarchivar_servicio_evento(self.servicio, actor=self.user)
        self.servicio.refresh_from_db()
        self.assertIsNone(self.servicio.archivado_en)
        self.assertEqual(self.servicio.estado_operativo, 'CANCELADO')

    def test_tarea_cancelar_archivar_desarchivar(self):
        cancelar_tarea_evento(self.tarea, actor=self.user, motivo='Ya no aplica')
        archivar_tarea_evento(self.tarea, actor=self.user)
        self.tarea.refresh_from_db()
        self.assertEqual(self.tarea.estado, 'CANCELADA')
        self.assertIsNotNone(self.tarea.archivado_en)
        desarchivar_tarea_evento(self.tarea, actor=self.user)
        self.tarea.refresh_from_db()
        self.assertIsNone(self.tarea.archivado_en)
        self.assertEqual(self.tarea.estado, 'CANCELADA')

    def test_tarea_pendiente_no_se_archiva(self):
        with self.assertRaises(ValidationError):
            archivar_tarea_evento(self.tarea, actor=self.user)

    def test_actividad_cancelar_archivar_desarchivar(self):
        cancelar_actividad_itinerario(self.actividad, actor=self.user, motivo='Reprogramacion externa')
        archivar_actividad_itinerario(self.actividad, actor=self.user)
        self.actividad.refresh_from_db()
        self.assertEqual(self.actividad.estado, 'CANCELADA')
        self.assertIsNotNone(self.actividad.archivado_en)
        desarchivar_actividad_itinerario(self.actividad, actor=self.user)
        self.actividad.refresh_from_db()
        self.assertIsNone(self.actividad.archivado_en)
        self.assertEqual(self.actividad.estado, 'CANCELADA')

    def test_documento_archivar_no_borra_archivo_ni_registro(self):
        documento_id = self.documento.id
        archivo = self.documento.archivo.name
        archivar_documento_evento(self.documento, actor=self.user, motivo='Version historica')
        self.documento.refresh_from_db()
        self.assertEqual(self.documento.id, documento_id)
        self.assertEqual(self.documento.archivo.name, archivo)
        self.assertIsNotNone(self.documento.archivado_en)
        desarchivar_documento_evento(self.documento, actor=self.user)
        self.documento.refresh_from_db()
        self.assertIsNone(self.documento.archivado_en)

    def test_gasto_con_pago_activo_no_se_cancela(self):
        PagoEvento.objects.create(gasto=self.gasto, monto=Decimal('5000.00'))
        with self.assertRaises(ValidationError):
            cancelar_gasto_evento(self.gasto, actor=self.user)
        self.gasto.refresh_from_db()
        self.assertEqual(self.gasto.estado, 'PENDIENTE')

    def test_anular_pago_lo_excluye_de_total_pagado(self):
        pago = PagoEvento.objects.create(gasto=self.gasto, monto=Decimal('5000.00'))
        self.assertEqual(self.gasto.total_pagado, Decimal('5000.00'))
        anular_pago_evento(pago, actor=self.user, motivo='Captura duplicada')
        pago.refresh_from_db()
        self.assertEqual(pago.estado, 'ANULADO')
        self.assertEqual(self.gasto.total_pagado, 0)
        self.assertTrue(RegistroAuditoria.objects.filter(accion='pago_evento.anular', objeto_id=str(pago.id)).exists())

    def test_anular_pago_es_idempotente(self):
        pago = PagoEvento.objects.create(gasto=self.gasto, monto=Decimal('5000.00'))
        anular_pago_evento(pago, actor=self.user)
        anular_pago_evento(pago, actor=self.user)
        self.assertEqual(RegistroAuditoria.objects.filter(accion='pago_evento.anular', objeto_id=str(pago.id)).count(), 1)

    def test_gasto_se_cancela_despues_de_anular_pagos(self):
        pago = PagoEvento.objects.create(gasto=self.gasto, monto=Decimal('5000.00'))
        anular_pago_evento(pago, actor=self.user)
        cancelar_gasto_evento(self.gasto, actor=self.user, motivo='Gasto descartado')
        self.gasto.refresh_from_db()
        self.assertEqual(self.gasto.estado, 'CANCELADO')
        self.assertIsNotNone(self.gasto.cancelado_en)

    def test_gasto_cancelado_se_archiva_y_desarchiva(self):
        cancelar_gasto_evento(self.gasto, actor=self.user)
        archivar_gasto_evento(self.gasto, actor=self.user)
        self.gasto.refresh_from_db()
        self.assertIsNotNone(self.gasto.archivado_en)
        desarchivar_gasto_evento(self.gasto, actor=self.user)
        self.gasto.refresh_from_db()
        self.assertIsNone(self.gasto.archivado_en)
        self.assertEqual(self.gasto.estado, 'CANCELADO')

    def test_gasto_pendiente_no_se_archiva(self):
        with self.assertRaises(ValidationError):
            archivar_gasto_evento(self.gasto, actor=self.user)

    def test_resumen_financiero_excluye_pago_anulado(self):
        ContratoEvento.objects.create(
            evento=self.evento,
            version=1,
            estado='CONTRATADO',
            monto_base=Decimal('100000.00'),
            snapshot_version=2,
            snapshot_comercial={'version': 2, 'totales': {'total_final': '100000.00'}},
        )
        pago = PagoEvento.objects.create(gasto=self.gasto, monto=Decimal('5000.00'))
        data = obtener_resumen_financiero_evento(self.evento)
        self.assertEqual(data['pagos_operativos_realizados'], Decimal('5000.00'))
        anular_pago_evento(pago, actor=self.user)
        data = obtener_resumen_financiero_evento(self.evento)
        self.assertEqual(data['pagos_operativos_realizados'], Decimal('0.00'))
        self.assertEqual(data['flujo_neto_caja'], Decimal('0.00'))

    def test_archivar_no_equivale_a_eliminar(self):
        cancelar_servicio_evento(self.servicio, actor=self.user)
        archivar_servicio_evento(self.servicio, actor=self.user)
        cancelar_tarea_evento(self.tarea, actor=self.user)
        archivar_tarea_evento(self.tarea, actor=self.user)
        archivar_documento_evento(self.documento, actor=self.user)
        self.assertTrue(ServicioEvento.objects.filter(pk=self.servicio.pk).exists())
        self.assertTrue(TareaEvento.objects.filter(pk=self.tarea.pk).exists())
        self.assertTrue(DocumentoEvento.objects.filter(pk=self.documento.pk).exists())
