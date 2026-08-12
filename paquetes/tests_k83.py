from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from invitaciones.models import EventoBoda
from organizaciones.models import EmpresaSuscriptora
from proveedores.models import ServicioEvento

from .models import PaqueteBoda, PaqueteEvento, ServicioPaquete
from .services import capturar_snapshot_paquete, materializar_servicios_paquete


def crear_evento(empresa=None):
    ahora = timezone.now()
    return EventoBoda.objects.create(
        empresa=empresa,
        novio='Diego',
        novia='Wendy',
        frase_portada='Nos casamos',
        mensaje_general='Gracias por acompanarnos.',
        fecha_misa=ahora,
        lugar_misa='Templo',
        fecha_fiesta=ahora,
        lugar_fiesta='Salon',
    )


class PackageSnapshotMaterializationK83Tests(TestCase):
    def setUp(self):
        self.empresa = EmpresaSuscriptora.objects.create(
            nombre_comercial='DIRTEC Demo',
            slug='dirtec-demo-k83',
        )
        self.evento = crear_evento(self.empresa)
        self.paquete = PaqueteBoda.objects.create(
            empresa=self.empresa,
            nombre='Premium',
            descripcion='Paquete comercial premium',
            precio_base=Decimal('50000.00'),
            numero_personas_incluidas=100,
        )
        self.dj = ServicioPaquete.objects.create(
            paquete=self.paquete,
            tipo_servicio='DJ',
            descripcion='DJ por 6 horas',
            cantidad=1,
            precio_incluido=Decimal('8000.00'),
        )
        self.foto = ServicioPaquete.objects.create(
            paquete=self.paquete,
            tipo_servicio='FOTOGRAFIA',
            descripcion='Cobertura fotografica',
            cantidad=2,
            precio_incluido=Decimal('12000.00'),
        )
        self.paquete_evento = PaqueteEvento.objects.create(
            evento=self.evento,
            paquete=self.paquete,
            precio_acordado=Decimal('52000.00'),
            descuento=Decimal('2000.00'),
            estado='CONTRATADO',
        )

    def test_snapshot_congela_datos_del_paquete(self):
        snapshot = capturar_snapshot_paquete(self.paquete_evento)
        self.assertEqual(snapshot['nombre'], 'Premium')
        self.assertEqual(len(snapshot['servicios']), 2)

        self.paquete.nombre = 'Premium Nuevo'
        self.paquete.save(update_fields=['nombre'])
        self.dj.descripcion = 'DJ cambiado'
        self.dj.save(update_fields=['descripcion'])

        self.paquete_evento.refresh_from_db()
        self.assertEqual(self.paquete_evento.snapshot_paquete['nombre'], 'Premium')
        self.assertEqual(
            self.paquete_evento.snapshot_paquete['servicios'][0]['descripcion'],
            'DJ por 6 horas',
        )

    def test_materializacion_crea_servicios_independientes_e_idempotentes(self):
        resultado = materializar_servicios_paquete(self.paquete_evento)
        self.assertEqual(resultado['creados'], 2)
        self.assertEqual(
            ServicioEvento.objects.filter(paquete_evento=self.paquete_evento).count(),
            2,
        )

        servicio = ServicioEvento.objects.get(servicio_paquete_origen=self.foto)
        self.assertEqual(servicio.origen, 'PAQUETE')
        self.assertEqual(servicio.modalidad, 'INCLUIDO')
        self.assertEqual(servicio.cantidad_paquete, 2)
        self.assertEqual(servicio.paquete_nombre_snapshot, 'Premium')
        self.assertEqual(servicio.valor_contratado, Decimal('12000.00'))
        self.assertEqual(servicio.cargo_adicional_cliente, Decimal('0.00'))
        self.assertEqual(servicio.costo_proveedor, Decimal('0.00'))
        self.assertEqual(servicio.costo_total, Decimal('0.00'))
        # Compatibilidad temporal con pantallas legacy.
        self.assertEqual(servicio.precio_cliente, Decimal('12000.00'))

        segundo = materializar_servicios_paquete(self.paquete_evento)
        self.assertEqual(segundo['creados'], 0)
        self.assertEqual(segundo['actualizados'], 2)
        self.assertEqual(
            ServicioEvento.objects.filter(paquete_evento=self.paquete_evento).count(),
            2,
        )

    def test_paquete_de_otra_empresa_es_rechazado(self):
        otra = EmpresaSuscriptora.objects.create(
            nombre_comercial='Otra empresa',
            slug='otra-empresa-k83',
        )
        paquete_ajeno = PaqueteBoda.objects.create(
            empresa=otra,
            nombre='Ajeno',
            precio_base=1000,
        )
        asignacion = PaqueteEvento(
            evento=self.evento,
            paquete=paquete_ajeno,
            precio_acordado=1000,
        )
        with self.assertRaises(ValidationError):
            asignacion.full_clean()

    def test_snapshot_contratado_no_se_reemplaza(self):
        capturar_snapshot_paquete(self.paquete_evento)
        with self.assertRaises(ValidationError):
            capturar_snapshot_paquete(self.paquete_evento, reemplazar=True)
