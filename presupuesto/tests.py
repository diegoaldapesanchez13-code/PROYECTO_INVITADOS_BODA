from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from invitaciones.models import EventoBoda
from .models import CategoriaGasto, GastoEvento, PagoEvento


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


class GastoEventoTests(TestCase):
    def test_calcula_saldo_y_vencimiento(self):
        categoria = CategoriaGasto.objects.create(nombre='Salon')
        gasto = GastoEvento.objects.create(
            evento=crear_evento(),
            categoria=categoria,
            concepto='Renta de salon',
            monto_real=20000,
            fecha_limite=timezone.localdate() - timedelta(days=1),
        )
        PagoEvento.objects.create(gasto=gasto, monto=5000)

        self.assertEqual(gasto.total_pagado, 5000)
        self.assertEqual(gasto.saldo_pendiente, 15000)
        self.assertTrue(gasto.esta_vencido)
