from django.test import TestCase
from django.utils import timezone

from invitaciones.models import EventoBoda
from .models import EntretenimientoEvento


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


class EntretenimientoEventoTests(TestCase):
    def test_calcula_saldo_pendiente(self):
        entretenimiento = EntretenimientoEvento.objects.create(
            evento=crear_evento(),
            tipo='DJ',
            nombre_artista='DJ Luna',
            costo=12000,
            anticipo=3000,
        )

        self.assertEqual(entretenimiento.saldo_pendiente, 9000)
