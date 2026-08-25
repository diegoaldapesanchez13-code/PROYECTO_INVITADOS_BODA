from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from eventos.models import ContratoEvento, ParticipanteEvento
from invitaciones.models import EventoBoda
from organizaciones.models import EmpresaSuscriptora, MembresiaEmpresa
from proveedores.models import Proveedor, ServicioEvento

from .models import CategoriaGasto, GastoEvento, PagoClienteEvento, PagoEvento
from .services import (
    obtener_resumen_financiero_evento,
    resumen_financiero_cliente,
    resumen_financiero_interno,
)


def crear_evento(empresa, *, planner=None, cliente=None, nombre='Evento K97'):
    evento = EventoBoda.objects.create(
        empresa=empresa,
        nombre_evento=nombre,
        novio='Cliente',
        novia='Principal',
        frase_portada='Celebracion',
        mensaje_general='Mensaje del evento.',
        fecha_misa=timezone.now(),
        lugar_misa='Ceremonia',
        fecha_fiesta=timezone.now(),
        lugar_fiesta='Recepcion',
        wedding_planner=planner,
    )
    if cliente:
        evento.clientes.add(cliente)
    return evento


class FinanzasIntegradasK97Tests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.empresa = EmpresaSuscriptora.objects.create(nombre_comercial='Empresa K97', slug='empresa-k97')
        self.empresa_b = EmpresaSuscriptora.objects.create(nombre_comercial='Empresa B K97', slug='empresa-b-k97')
        self.admin = User.objects.create_user(username='admin-k97', password='test123')
        self.admin_b = User.objects.create_user(username='admin-b-k97', password='test123')
        self.planner = User.objects.create_user(username='planner-k97', password='test123')
        self.cliente = User.objects.create_user(username='cliente-k97', password='test123')
        self.cliente_b = User.objects.create_user(username='cliente-b-k97', password='test123')
        self.proveedor_user = User.objects.create_user(username='proveedor-k97', password='test123')
        MembresiaEmpresa.objects.create(empresa=self.empresa, usuario=self.admin, rol='ADMIN_EMPRESA')
        MembresiaEmpresa.objects.create(empresa=self.empresa_b, usuario=self.admin_b, rol='ADMIN_EMPRESA')
        MembresiaEmpresa.objects.create(empresa=self.empresa, usuario=self.planner, rol='WEDDING_PLANNER')
        MembresiaEmpresa.objects.create(empresa=self.empresa, usuario=self.cliente, rol='CLIENTE')
        MembresiaEmpresa.objects.create(empresa=self.empresa_b, usuario=self.cliente_b, rol='CLIENTE')
        MembresiaEmpresa.objects.create(empresa=self.empresa, usuario=self.proveedor_user, rol='PROVEEDOR')
        self.evento = crear_evento(self.empresa, planner=self.planner, cliente=self.cliente)
        self.evento_b = crear_evento(self.empresa_b, cliente=self.cliente_b, nombre='Evento B K97')
        self.proveedor = Proveedor.objects.create(
            empresa=self.empresa,
            usuario=self.proveedor_user,
            nombre_comercial='Proveedor K97',
        )
        self.categoria = CategoriaGasto.objects.create(nombre='Operacion K97')
        self.contrato = ContratoEvento.objects.create(
            evento=self.evento,
            version=1,
            estado='CONTRATADO',
            monto_base=Decimal('100000.00'),
            snapshot_version=2,
            snapshot_comercial={
                'version': 2,
                'totales': {'total_final': '100000.00'},
            },
        )
        self.servicio = ServicioEvento.objects.create(
            evento=self.evento,
            proveedor=self.proveedor,
            prestacion_tipo='PROVEEDOR',
            nombre_servicio='DJ',
            valor_contratado=Decimal('20000.00'),
        )
        self.servicio_interno = ServicioEvento.objects.create(
            evento=self.evento,
            proveedor=None,
            prestacion_tipo='EMPRESA',
            nombre_servicio='Coordinacion interna',
            valor_contratado=Decimal('10000.00'),
        )
        self.servicio_por_definir = ServicioEvento.objects.create(
            evento=self.evento,
            proveedor=None,
            prestacion_tipo='POR_DEFINIR',
            nombre_servicio='Flores por definir',
            valor_contratado=Decimal('5000.00'),
        )
        ParticipanteEvento.objects.filter(evento=self.evento, usuario=self.planner, rol='PLANNER').update(
            puede_ver_finanzas=True
        )

    def crear_pago_cliente(self, monto='25000.00', estado='RECIBIDO', evento=None, registrado_por=None):
        return PagoClienteEvento.objects.create(
            evento=evento or self.evento,
            registrado_por=registrado_por or self.cliente,
            monto=Decimal(monto),
            estado=estado,
            comprobante='presupuesto/pagos_cliente_evento/test.jpg',
        )

    def crear_gasto(self, *, estimado='30000.00', real='25000.00', servicio=None):
        return GastoEvento.objects.create(
            evento=self.evento,
            servicio_evento=servicio or self.servicio,
            categoria=self.categoria,
            proveedor=self.proveedor,
            concepto='Costo operativo',
            monto_estimado=Decimal(estimado),
            monto_real=Decimal(real),
        )

    def test_total_contrato_desde_v2(self):
        resumen = obtener_resumen_financiero_evento(self.evento)
        self.assertEqual(resumen['total_contratado'], Decimal('100000.00'))
        self.assertEqual(resumen['fuente_total'], 'K9_CONTRATO_V2')

    def test_pago_cliente_suma_correctamente(self):
        self.crear_pago_cliente('25000.00')
        self.crear_pago_cliente('10000.00', estado='PENDIENTE')
        resumen = obtener_resumen_financiero_evento(self.evento)
        self.assertEqual(resumen['pagos_cliente_recibidos'], Decimal('25000.00'))

    def test_saldo_cliente_correcto(self):
        self.crear_pago_cliente('25000.00')
        resumen = obtener_resumen_financiero_evento(self.evento)
        self.assertEqual(resumen['saldo_cliente'], Decimal('75000.00'))

    def test_sobrepago_reporta_credito(self):
        self.crear_pago_cliente('120000.00')
        resumen = obtener_resumen_financiero_evento(self.evento)
        self.assertEqual(resumen['saldo_cliente'], Decimal('0.00'))
        self.assertEqual(resumen['sobrepago_cliente'], Decimal('20000.00'))

    def test_costo_estimado(self):
        self.crear_gasto(estimado='30000.00', real='25000.00')
        self.crear_gasto(estimado='10000.00', real='0.00', servicio=self.servicio_interno)
        resumen = obtener_resumen_financiero_evento(self.evento)
        self.assertEqual(resumen['costo_estimado'], Decimal('40000.00'))

    def test_costo_real_usa_solo_valores_reales_registrados(self):
        self.crear_gasto(estimado='30000.00', real='25000.00')
        self.crear_gasto(estimado='10000.00', real='0.00', servicio=self.servicio_interno)
        resumen = obtener_resumen_financiero_evento(self.evento)
        self.assertEqual(resumen['costo_real'], Decimal('25000.00'))

    def test_costo_comprometido_usa_real_o_estimado(self):
        self.crear_gasto(estimado='30000.00', real='25000.00')
        self.crear_gasto(estimado='10000.00', real='0.00', servicio=self.servicio_interno)
        resumen = obtener_resumen_financiero_evento(self.evento)
        self.assertEqual(resumen['costo_comprometido'], Decimal('35000.00'))

    def test_pagos_operativos(self):
        gasto = self.crear_gasto()
        PagoEvento.objects.create(gasto=gasto, monto=Decimal('15000.00'))
        resumen = obtener_resumen_financiero_evento(self.evento)
        self.assertEqual(resumen['pagos_operativos_realizados'], Decimal('15000.00'))

    def test_saldo_operativo(self):
        gasto = self.crear_gasto()
        PagoEvento.objects.create(gasto=gasto, monto=Decimal('15000.00'))
        resumen = obtener_resumen_financiero_evento(self.evento)
        self.assertEqual(resumen['saldo_operativo'], Decimal('10000.00'))

    def test_margen_estimado(self):
        self.crear_gasto(estimado='40000.00', real='0.00')
        resumen = obtener_resumen_financiero_evento(self.evento)
        self.assertEqual(resumen['margen_estimado'], Decimal('60000.00'))

    def test_margen_real(self):
        self.crear_gasto(estimado='40000.00', real='25000.00')
        resumen = obtener_resumen_financiero_evento(self.evento)
        self.assertEqual(resumen['margen_real'], Decimal('75000.00'))

    def test_porcentaje_margen(self):
        self.crear_gasto(estimado='40000.00', real='25000.00')
        resumen = obtener_resumen_financiero_evento(self.evento)
        self.assertEqual(resumen['porcentaje_margen_real'], Decimal('75.00'))

    def test_total_cero_no_divide(self):
        evento = crear_evento(self.empresa, cliente=self.cliente, nombre='Sin contrato')
        resumen = obtener_resumen_financiero_evento(evento)
        self.assertEqual(resumen['porcentaje_margen_real'], Decimal('0.00'))

    def test_flujo_caja(self):
        self.crear_pago_cliente('50000.00')
        gasto = self.crear_gasto()
        PagoEvento.objects.create(gasto=gasto, monto=Decimal('15000.00'))
        resumen = obtener_resumen_financiero_evento(self.evento)
        self.assertEqual(resumen['flujo_neto_caja'], Decimal('35000.00'))

    def test_margen_no_es_flujo_caja(self):
        self.crear_pago_cliente('50000.00')
        gasto = self.crear_gasto(estimado='30000.00', real='25000.00')
        PagoEvento.objects.create(gasto=gasto, monto=Decimal('15000.00'))
        resumen = obtener_resumen_financiero_evento(self.evento)
        self.assertNotEqual(resumen['margen_real'], resumen['flujo_neto_caja'])

    def test_proveedor_costo_no_cambia_contrato(self):
        snapshot = dict(self.contrato.snapshot_comercial)
        self.servicio.costo_proveedor = Decimal('99999.00')
        self.servicio.proveedor = self.proveedor
        self.servicio.save(update_fields=['costo_proveedor', 'proveedor'])
        self.contrato.refresh_from_db()
        resumen = obtener_resumen_financiero_evento(self.evento)
        self.assertEqual(self.contrato.snapshot_comercial, snapshot)
        self.assertEqual(resumen['total_contratado'], Decimal('100000.00'))

    def test_pago_operativo_no_cambia_contrato(self):
        gasto = self.crear_gasto()
        PagoEvento.objects.create(gasto=gasto, monto=Decimal('15000.00'))
        self.contrato.refresh_from_db()
        self.assertEqual(self.contrato.snapshot_comercial['totales']['total_final'], '100000.00')

    def test_pago_cliente_no_cambia_contrato(self):
        self.crear_pago_cliente('25000.00')
        self.contrato.refresh_from_db()
        self.assertEqual(self.contrato.snapshot_comercial['totales']['total_final'], '100000.00')

    def test_servicio_propio_sin_proveedor_valido(self):
        resumen = obtener_resumen_financiero_evento(self.evento)
        interno = next(item for item in resumen['servicios'] if item['nombre'] == 'Coordinacion interna')
        self.assertEqual(interno['prestacion_tipo'], 'EMPRESA')
        self.assertIsNone(interno['proveedor'])

    def test_servicio_por_definir_valido(self):
        resumen = obtener_resumen_financiero_evento(self.evento)
        pendiente = next(item for item in resumen['servicios'] if item['nombre'] == 'Flores por definir')
        self.assertTrue(pendiente['costo_pendiente'])

    def test_costo_pendiente_genera_advertencia(self):
        resumen = obtener_resumen_financiero_evento(self.evento)
        self.assertTrue(any('Flores por definir' in item for item in resumen['advertencias']))

    def test_cliente_no_ve_margen(self):
        data = resumen_financiero_cliente(self.evento, user=self.cliente)
        self.assertNotIn('margen_real', data)

    def test_cliente_no_ve_costos(self):
        data = resumen_financiero_cliente(self.evento, user=self.cliente)
        self.assertNotIn('costo_real', data)
        self.assertNotIn('pagos_operativos_realizados', data)

    def test_cliente_ve_total_pagos_saldo(self):
        self.crear_pago_cliente('25000.00')
        data = resumen_financiero_cliente(self.evento, user=self.cliente)
        self.assertEqual(data['total_contratado'], Decimal('100000.00'))
        self.assertEqual(data['pagos_cliente_recibidos'], Decimal('25000.00'))
        self.assertEqual(data['saldo_cliente'], Decimal('75000.00'))

    def test_planner_sin_permiso_financiero_no_ve_margen(self):
        ParticipanteEvento.objects.filter(evento=self.evento, usuario=self.planner, rol='PLANNER').update(
            puede_ver_finanzas=False
        )
        with self.assertRaises(PermissionDenied):
            resumen_financiero_interno(self.evento, user=self.planner)

    def test_planner_autorizado_si_ve_margen(self):
        data = resumen_financiero_interno(self.evento, user=self.planner)
        self.assertIn('margen_real', data)

    def test_empresa_mismo_tenant_ve(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse('presupuesto_finanzas_evento', args=[self.empresa.slug, self.evento.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Margen real')

    def test_empresa_otro_tenant_no_ve(self):
        self.client.force_login(self.admin_b)
        response = self.client.get(reverse('presupuesto_finanzas_evento', args=[self.empresa_b.slug, self.evento.id]))
        self.assertEqual(response.status_code, 404)

    def test_proveedor_no_ve_contrato_total(self):
        self.client.force_login(self.proveedor_user)
        response = self.client.get(reverse('presupuesto_finanzas_evento', args=[self.empresa.slug, self.evento.id]))
        self.assertEqual(response.status_code, 403)

    def test_proveedor_no_ve_pagos_cliente(self):
        with self.assertRaises(PermissionDenied):
            resumen_financiero_interno(self.evento, user=self.proveedor_user)
