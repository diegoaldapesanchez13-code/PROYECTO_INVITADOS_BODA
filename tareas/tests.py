from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from invitaciones.models import EventoBoda
from .models import TareaEvento


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


class TareaEventoTests(TestCase):
    def test_detecta_tarea_vencida_y_completa_avance(self):
        tarea = TareaEvento.objects.create(
            evento=crear_evento(),
            titulo='Confirmar florista',
            fecha_limite=timezone.localdate() - timedelta(days=1),
        )

        self.assertTrue(tarea.esta_vencida)

        tarea.estado = 'COMPLETADA'
        tarea.save()
        self.assertEqual(tarea.porcentaje_avance, 100)
        self.assertFalse(tarea.esta_vencida)
