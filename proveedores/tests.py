from django.test import TestCase
from django.utils import timezone

from invitaciones.models import EventoBoda
from .models import Proveedor, ServicioEvento


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


class ServicioEventoTests(TestCase):
    def test_servicio_conserva_costo_proveedor(self):
        evento = crear_evento()
        proveedor = Proveedor.objects.create(
            nombre_comercial='Foto Luz',
            tipo_proveedor='FOTOGRAFIA',
        )
        servicio = ServicioEvento.objects.create(
            evento=evento,
            proveedor=proveedor,
            nombre_servicio='Fotografia completa',
            costo_proveedor=15000,
        )

        self.assertEqual(servicio.costo_proveedor, 15000)
