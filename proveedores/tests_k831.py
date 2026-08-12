from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from invitaciones.models import EventoBoda
from organizaciones.models import EmpresaSuscriptora
from proveedores.models import ServicioEvento


class FinancialSemanticsK831Tests(TestCase):
    def setUp(self):
        self.empresa = EmpresaSuscriptora.objects.create(
            nombre_comercial='DIRTEC K831',
            slug='dirtec-k831',
        )
        ahora = timezone.now()
        self.evento = EventoBoda.objects.create(
            empresa=self.empresa,
            novio='Diego',
            novia='Fernanda',
            frase_portada='Nos casamos',
            mensaje_general='Evento de prueba',
            fecha_misa=ahora,
            lugar_misa='Templo',
            fecha_fiesta=ahora,
            lugar_fiesta='Salon',
        )

    def test_incluido_puede_tener_valor_sin_cargo_adicional(self):
        servicio = ServicioEvento(
            evento=self.evento,
            nombre_servicio='Banquete',
            modalidad='INCLUIDO',
            valor_contratado=Decimal('80000.00'),
            cargo_adicional_cliente=Decimal('0.00'),
        )
        servicio.full_clean()
        self.assertTrue(servicio.incluido_en_paquete)
        self.assertEqual(servicio.importe_adicional_cliente, Decimal('0.00'))

    def test_incluido_rechaza_cargo_adicional(self):
        servicio = ServicioEvento(
            evento=self.evento,
            nombre_servicio='Banquete',
            modalidad='INCLUIDO',
            valor_contratado=Decimal('80000.00'),
            cargo_adicional_cliente=Decimal('1000.00'),
        )
        with self.assertRaises(ValidationError):
            servicio.full_clean()

    def test_adicional_distingue_valor_y_cargo(self):
        servicio = ServicioEvento.objects.create(
            evento=self.evento,
            nombre_servicio='Saxofonista',
            modalidad='ADICIONAL',
            valor_contratado=Decimal('6500.00'),
            cargo_adicional_cliente=Decimal('6500.00'),
        )
        self.assertEqual(servicio.valor_contratado, Decimal('6500.00'))
        self.assertEqual(servicio.importe_adicional_cliente, Decimal('6500.00'))

    def test_upgrade_puede_cobrar_solo_la_diferencia(self):
        servicio = ServicioEvento.objects.create(
            evento=self.evento,
            nombre_servicio='Decoracion premium',
            modalidad='UPGRADE',
            valor_contratado=Decimal('16500.00'),
            cargo_adicional_cliente=Decimal('4500.00'),
        )
        self.assertEqual(servicio.valor_contratado, Decimal('16500.00'))
        self.assertEqual(servicio.importe_adicional_cliente, Decimal('4500.00'))
