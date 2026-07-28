from django.test import TestCase
from django.utils import timezone

from invitaciones.models import EventoBoda
from .models import CateringEvento


def crear_evento():
    ahora = timezone.now()
    return EventoBoda.objects.create(
        novio='Diego',
        novia='Wendy',
        frase_portada='Nos casamos',
        mensaje_general='Gracias por acompanarnos.',
        fecha_misa=ahora,
        lugar_misa='Templo',
        fecha_fiesta=ahora,
        lugar_fiesta='Salon',
    )


class CateringEventoTests(TestCase):
    def test_total_personas_suma_adultos_ninos_y_proveedores(self):
        catering = CateringEvento.objects.create(
            evento=crear_evento(),
            cantidad_adultos=90,
            cantidad_ninos=10,
            cantidad_proveedores=8,
        )

        self.assertEqual(catering.total_personas, 108)
