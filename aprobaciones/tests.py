from django.test import TestCase
from django.utils import timezone

from invitaciones.models import EventoBoda
from .models import AprobacionEvento


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


class AprobacionEventoTests(TestCase):
    def test_guarda_fecha_respuesta_al_aprobar(self):
        aprobacion = AprobacionEvento.objects.create(
            evento=crear_evento(),
            tipo='DECORACION',
            titulo='Centro de mesa',
        )

        self.assertIsNone(aprobacion.fecha_respuesta)

        aprobacion.estado = 'APROBADO'
        aprobacion.save()

        self.assertIsNotNone(aprobacion.fecha_respuesta)
