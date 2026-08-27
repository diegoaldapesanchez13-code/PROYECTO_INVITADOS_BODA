from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from catalogo.models import ServicioCatalogo
from colaboracion.services import canales_visibles_workspace
from organizaciones.models import EmpresaSuscriptora, MembresiaEmpresa, SedeEvento
from paquetes.models import PaqueteBoda, PaqueteServicio, PropuestaEvento, PropuestaLinea
from presupuesto.models import GastoEvento, PagoClienteEvento, PagoEvento
from proveedores.models import Proveedor, ServicioEvento

from .models import ContratoEvento
from .workspace_commercial import aceptar_propuesta
from .services import (
    generar_contrato_v2_desde_propuesta,
    materializar_servicios_contrato_v2,
)


def crear_evento(empresa, *, planner=None, cliente=None, nombre='Evento K96'):
    from invitaciones.models import EventoBoda

    ahora = timezone.now()
    evento = EventoBoda.objects.create(
        empresa=empresa,
        nombre_evento=nombre,
        novio='Cliente',
        novia='Principal',
        frase_portada='Celebracion',
        mensaje_general='Mensaje del evento.',
        fecha_misa=ahora,
        lugar_misa='Ceremonia',
        fecha_fiesta=ahora,
        lugar_fiesta='Recepcion',
        wedding_planner=planner,
    )
    if cliente:
        evento.clientes.add(cliente)
    return evento


class MaterializacionContratoV2K96Tests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.empresa_a = EmpresaSuscriptora.objects.create(nombre_comercial='Empresa A K96', slug='empresa-a-k96')
        self.empresa_b = EmpresaSuscriptora.objects.create(nombre_comercial='Empresa B K96', slug='empresa-b-k96')
        self.admin = User.objects.create_user(username='admin-k96', password='test123')
        self.planner = User.objects.create_user(username='planner-k96', password='test123')
        self.cliente = User.objects.create_user(username='cliente-k96', password='test123')
        self.proveedor_user = User.objects.create_user(username='proveedor-k96', password='test123')
        MembresiaEmpresa.objects.create(empresa=self.empresa_a, usuario=self.admin, rol='ADMIN_EMPRESA')
        MembresiaEmpresa.objects.create(empresa=self.empresa_a, usuario=self.planner, rol='WEDDING_PLANNER')
        MembresiaEmpresa.objects.create(empresa=self.empresa_a, usuario=self.cliente, rol='CLIENTE')
        MembresiaEmpresa.objects.create(empresa=self.empresa_a, usuario=self.proveedor_user, rol='PROVEEDOR')
        self.proveedor = Proveedor.objects.create(
            empresa=self.empresa_a,
            usuario=self.proveedor_user,
            nombre_comercial='Proveedor K96',
        )
        self.sede = SedeEvento.objects.create(
            empresa=self.empresa_a,
            nombre='Salon K96',
            direccion='Direccion K96',
            precio_base=Decimal('10000.00'),
        )
        self.evento = crear_evento(self.empresa_a, planner=self.planner, cliente=self.cliente)
        self.dj = ServicioCatalogo.objects.create(empresa=self.empresa_a, nombre='DJ K96', categoria='MUSICA')
        self.alcohol = ServicioCatalogo.objects.create(empresa=self.empresa_a, nombre='Alcohol K96', categoria='BEBIDAS')
        self.catalogo_b = ServicioCatalogo.objects.create(empresa=self.empresa_b, nombre='Catalogo B K96', categoria='MUSICA')
        self.paquete = PaqueteBoda.objects.create(
            empresa=self.empresa_a,
            nombre='Paquete K96',
            descripcion='Paquete comercial',
            precio_adulto=Decimal('1000.00'),
            precio_nino=Decimal('500.00'),
            cargo_fijo=Decimal('2500.00'),
        )
        PaqueteServicio.objects.create(
            paquete=self.paquete,
            servicio_catalogo=self.dj,
            cantidad=1,
            orden=1,
            notas='Cabina principal',
            clave_origen='dj-principal',
        )
        PaqueteServicio.objects.create(
            paquete=self.paquete,
            servicio_catalogo=self.dj,
            cantidad=1,
            orden=2,
            notas='Cabina secundaria',
            clave_origen='dj-secundario',
        )
        self.propuesta = PropuestaEvento.objects.create(
            empresa=self.empresa_a,
            evento=self.evento,
            sede=self.sede,
            paquete=self.paquete,
            adultos=250,
            ninos=40,
            descuento=Decimal('5000.00'),
            estado='BORRADOR',
        )
        PropuestaLinea.objects.create(
            propuesta=self.propuesta,
            tipo='ADICIONAL',
            servicio_catalogo=self.alcohol,
            nombre='Alcohol',
            modo_precio='POR_PERSONA',
            tarifa=Decimal('450.00'),
            cantidad=1,
            orden=1,
        )
        PropuestaLinea.objects.create(
            propuesta=self.propuesta,
            tipo='ADICIONAL',
            nombre='Servicio manual',
            modo_precio='FIJO',
            tarifa=Decimal('3000.00'),
            cantidad=1,
            orden=2,
        )
        PropuestaLinea.objects.create(
            propuesta=self.propuesta,
            tipo='CORTESIA',
            nombre='Letras Hollywood',
            modo_precio='FIJO',
            tarifa=Decimal('8000.00'),
            valor_informativo=Decimal('8000.00'),
            orden=3,
        )
        aceptar_propuesta(self.propuesta, user=self.admin)
        self.propuesta.refresh_from_db()
        self.contrato = generar_contrato_v2_desde_propuesta(self.propuesta.id, user=self.admin)

    def materializar(self, contrato=None):
        return materializar_servicios_contrato_v2((contrato or self.contrato).id, user=self.admin)

    def servicios(self):
        return ServicioEvento.objects.filter(contrato_origen=self.contrato).order_by('linea_origen_key')

    def test_materializa_incluidos(self):
        self.materializar()
        self.assertEqual(self.servicios().filter(modalidad='INCLUIDO').count(), 2)

    def test_materializa_adicionales(self):
        self.materializar()
        self.assertEqual(self.servicios().filter(modalidad='ADICIONAL').count(), 2)

    def test_materializa_cortesias(self):
        self.materializar()
        self.assertEqual(self.servicios().filter(modalidad='CORTESIA').count(), 1)

    def test_cortesia_cargo_cliente_cero(self):
        self.materializar()
        cortesia = self.servicios().get(modalidad='CORTESIA')
        self.assertEqual(cortesia.cargo_adicional_cliente, Decimal('0.00'))

    def test_proveedor_inicial_null(self):
        self.materializar()
        self.assertFalse(self.servicios().exclude(proveedor__isnull=True).exists())

    def test_servicio_manual_funciona_sin_catalogo(self):
        self.materializar()
        manual = self.servicios().get(nombre_servicio='Servicio manual')
        self.assertEqual(manual.origen, 'MANUAL')
        self.assertIsNone(manual.servicio_catalogo_k9)

    def test_master_catalogo_ausente_no_rompe(self):
        snapshot = self.contrato.snapshot_comercial
        snapshot['adicionales'][0]['servicio_catalogo_id'] = 999999
        self.contrato.snapshot_comercial = snapshot
        self.contrato.save(update_fields=['snapshot_comercial'])
        self.materializar()
        alcohol = self.servicios().get(nombre_servicio='Alcohol')
        self.assertIsNone(alcohol.servicio_catalogo_k9)

    def test_master_catalogo_inactivo_no_rompe(self):
        self.alcohol.activo = False
        self.alcohol.save(update_fields=['activo'])
        self.materializar()
        alcohol = self.servicios().get(nombre_servicio='Alcohol')
        self.assertEqual(alcohol.servicio_catalogo_k9, self.alcohol)

    def test_dos_llamadas_no_duplican(self):
        self.materializar()
        self.materializar()
        self.assertEqual(self.servicios().count(), 5)

    def test_tres_llamadas_no_duplican(self):
        self.materializar()
        self.materializar()
        self.materializar()
        self.assertEqual(self.servicios().count(), 5)

    def test_lineas_distintas_mismo_catalogo_no_colisionan(self):
        self.materializar()
        self.assertEqual(self.servicios().filter(servicio_catalogo_k9=self.dj).count(), 2)

    def test_contrato_no_v2_no_materializa(self):
        self.contrato.snapshot_version = 1
        self.contrato.save(update_fields=['snapshot_version'])
        with self.assertRaises(ValidationError):
            self.materializar()

    def test_contrato_no_contratado_no_materializa(self):
        contrato = ContratoEvento.objects.create(
            evento=self.evento,
            version=2,
            estado='BORRADOR',
            snapshot_version=2,
            snapshot_comercial={'version': 2, 'incluidos': [], 'adicionales': [], 'cortesias': []},
        )
        with self.assertRaises(ValidationError):
            self.materializar(contrato)

    def test_contrato_cancelado_no_materializa(self):
        self.contrato.estado = 'CANCELADO'
        self.contrato.save(update_fields=['estado'])
        with self.assertRaises(ValidationError):
            self.materializar()

    def test_tenant_cruzado_rechaza_vinculo_catalogo(self):
        snapshot = self.contrato.snapshot_comercial
        snapshot['incluidos'][0]['servicio_catalogo_id'] = self.catalogo_b.id
        self.contrato.snapshot_comercial = snapshot
        self.contrato.save(update_fields=['snapshot_comercial'])
        self.materializar()
        servicio = self.servicios().get(linea_origen_key='INCLUIDO:dj-principal')
        self.assertIsNone(servicio.servicio_catalogo_k9)

    def test_valor_contratado_viene_del_snapshot(self):
        self.materializar()
        adicional = self.servicios().get(nombre_servicio='Alcohol')
        self.assertEqual(adicional.valor_contratado, Decimal('130500.00'))
        self.assertEqual(adicional.cargo_adicional_cliente, Decimal('130500.00'))

    def test_cambio_tarifa_catalogo_no_cambia_valor(self):
        self.materializar()
        self.alcohol.nombre = 'Alcohol cambiado'
        self.alcohol.save(update_fields=['nombre'])
        self.materializar()
        adicional = self.servicios().get(nombre_servicio='Alcohol')
        self.assertEqual(adicional.valor_contratado, Decimal('130500.00'))

    def test_cambio_paquete_no_cambia_valor(self):
        self.paquete.precio_adulto = Decimal('9999.00')
        self.paquete.save(update_fields=['precio_adulto'])
        self.materializar()
        adicional = self.servicios().get(nombre_servicio='Alcohol')
        self.assertEqual(adicional.valor_contratado, Decimal('130500.00'))

    def test_proveedor_asignado_se_conserva_tras_rematerializar(self):
        self.materializar()
        servicio = self.servicios().get(nombre_servicio='Alcohol')
        servicio.proveedor = self.proveedor
        servicio.prestacion_tipo = 'PROVEEDOR'
        servicio.save(update_fields=['proveedor', 'prestacion_tipo'])
        self.materializar()
        servicio.refresh_from_db()
        self.assertEqual(servicio.proveedor, self.proveedor)
        self.assertEqual(servicio.prestacion_tipo, 'PROVEEDOR')

    def test_costo_proveedor_se_conserva(self):
        self.materializar()
        servicio = self.servicios().get(nombre_servicio='Alcohol')
        servicio.costo_proveedor = Decimal('12500.00')
        servicio.save(update_fields=['costo_proveedor'])
        self.materializar()
        servicio.refresh_from_db()
        self.assertEqual(servicio.costo_proveedor, Decimal('12500.00'))

    def test_notas_operativas_se_conservan(self):
        self.materializar()
        servicio = self.servicios().get(nombre_servicio='Alcohol')
        servicio.notas = 'Nota operativa'
        servicio.notas_internas = 'Nota interna'
        servicio.save(update_fields=['notas', 'notas_internas'])
        self.materializar()
        servicio.refresh_from_db()
        self.assertEqual(servicio.notas, 'Nota operativa')
        self.assertEqual(servicio.notas_internas, 'Nota interna')

    def test_estado_operativo_se_conserva(self):
        self.materializar()
        servicio = self.servicios().get(nombre_servicio='Alcohol')
        servicio.estado_operativo = 'PROGRAMADO'
        servicio.save(update_fields=['estado_operativo'])
        self.materializar()
        servicio.refresh_from_db()
        self.assertEqual(servicio.estado_operativo, 'PROGRAMADO')

    def test_no_crea_gasto_evento(self):
        self.materializar()
        self.assertEqual(GastoEvento.objects.count(), 0)

    def test_no_crea_pago_evento(self):
        self.materializar()
        self.assertEqual(PagoEvento.objects.count(), 0)

    def test_no_crea_pago_cliente_evento(self):
        self.materializar()
        self.assertEqual(PagoClienteEvento.objects.count(), 0)

    def test_no_altera_total_contrato(self):
        total = self.contrato.monto_base
        self.materializar()
        self.contrato.refresh_from_db()
        self.assertEqual(self.contrato.monto_base, total)

    def test_materializado_en_se_registra(self):
        self.materializar()
        self.contrato.refresh_from_db()
        self.assertIsNotNone(self.contrato.materializado_en)

    def test_materializacion_version_es_2(self):
        self.materializar()
        self.contrato.refresh_from_db()
        self.assertEqual(self.contrato.materializacion_version, 2)
        self.assertFalse(self.servicios().exclude(materializacion_version=2).exists())

    def test_rollback_completo_si_falla_una_linea(self):
        snapshot = self.contrato.snapshot_comercial
        snapshot['adicionales'][0]['nombre'] = ''
        self.contrato.snapshot_comercial = snapshot
        self.contrato.save(update_fields=['snapshot_comercial'])
        with self.assertRaises(ValidationError):
            self.materializar()
        self.assertEqual(self.servicios().count(), 0)

    def test_workspace_resuelve_servicio_materializado(self):
        self.materializar()
        servicio = self.servicios().first()
        self.client.force_login(self.admin)
        response = self.client.get(reverse('colaboracion_workspace_servicio', args=[servicio.id]))
        self.assertEqual(response.status_code, 200)

    def test_proveedor_no_asignado_no_obtiene_acceso(self):
        self.materializar()
        servicio = self.servicios().first()
        self.client.force_login(self.proveedor_user)
        response = self.client.get(reverse('colaboracion_workspace_servicio', args=[servicio.id]))
        self.assertEqual(response.status_code, 403)

    def test_cliente_no_obtiene_acceso_operativo_indebido(self):
        self.materializar()
        servicio = self.servicios().first()
        self.assertEqual(canales_visibles_workspace(self.cliente, servicio), {'CLIENTE_PLANNER'})
