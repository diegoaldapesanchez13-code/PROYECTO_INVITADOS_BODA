from django.test import TestCase
from django.utils import timezone

from invitaciones.models import EventoBoda
from .models import PaqueteBoda, PaqueteEvento


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


class PaqueteEventoTests(TestCase):
    def test_guarda_total_si_no_se_captura(self):
        paquete = PaqueteBoda.objects.create(
            nombre='Premium',
            precio_base=50000,
            numero_personas_incluidas=100,
        )
        paquete_evento = PaqueteEvento.objects.create(
            evento=crear_evento(),
            paquete=paquete,
            precio_acordado=52000,
            descuento=2000,
        )

        self.assertEqual(paquete_evento.total, 50000)
