from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase
from django.utils import timezone

from invitaciones.models import EventoBoda, Grupoinvitacion, Invitado
from .models import AsignacionMesa, Mesa


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


class AsignacionMesaTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_superuser(
            username='mesas_admin',
            password='test123',
        )
        self.client.force_login(self.user)

    def test_no_permite_exceder_capacidad(self):
        evento = crear_evento()
        mesa = Mesa.objects.create(
            evento=evento,
            nombre='Mesa 1',
            capacidad=1,
        )
        grupo = Grupoinvitacion.objects.create(
            evento=evento,
            nombre_grupo='Familia Perez',
            tipo='FAMILIAR',
        )
        invitado_1 = Invitado.objects.create(
            grupo=grupo,
            nombre='Ana',
        )
        invitado_2 = Invitado.objects.create(
            grupo=grupo,
            nombre='Luis',
        )

        AsignacionMesa.objects.create(
            mesa=mesa,
            invitado=invitado_1,
        )

        with self.assertRaises(ValidationError):
            AsignacionMesa.objects.create(
                mesa=mesa,
                invitado=invitado_2,
            )

    def test_personal_se_asigna_por_su_titular(self):
        evento = crear_evento()
        mesa = Mesa.objects.create(
            evento=evento,
            nombre='Mesa 2',
            capacidad=2,
        )
        grupo = Grupoinvitacion.objects.create(
            evento=evento,
            nombre_grupo='Carlos',
            tipo='PERSONAL',
        )
        titular = Invitado.objects.create(
            grupo=grupo,
            nombre='Carlos',
            es_acompanante_extra=False,
        )

        asignacion = AsignacionMesa.objects.create(
            mesa=mesa,
            invitado=titular,
        )

        self.assertEqual(
            str(asignacion),
            'Carlos en Mesa 2',
        )

    def test_una_persona_no_puede_tener_dos_mesas(self):
        evento = crear_evento()
        mesa_1 = Mesa.objects.create(
            evento=evento,
            nombre='Mesa A',
            capacidad=5,
        )
        mesa_2 = Mesa.objects.create(
            evento=evento,
            nombre='Mesa B',
            capacidad=5,
        )
        grupo = Grupoinvitacion.objects.create(
            evento=evento,
            nombre_grupo='Familia',
            tipo='FAMILIAR',
        )
        invitado = Invitado.objects.create(
            grupo=grupo,
            nombre='Ana',
        )

        AsignacionMesa.objects.create(
            mesa=mesa_1,
            invitado=invitado,
        )

        with self.assertRaises(ValidationError):
            AsignacionMesa.objects.create(
                mesa=mesa_2,
                invitado=invitado,
            )

    def test_no_permite_persona_de_otro_evento(self):
        evento = crear_evento()
        otro = crear_evento()
        mesa = Mesa.objects.create(
            evento=evento,
            nombre='Mesa Local',
            capacidad=5,
        )
        grupo = Grupoinvitacion.objects.create(
            evento=otro,
            nombre_grupo='Familia externa',
            tipo='FAMILIAR',
        )
        invitado = Invitado.objects.create(
            grupo=grupo,
            nombre='Externo',
        )

        with self.assertRaises(ValidationError):
            AsignacionMesa.objects.create(
                mesa=mesa,
                invitado=invitado,
            )

    def test_endpoint_actualiza_posicion_de_mesa(self):
        evento = crear_evento()
        mesa = Mesa.objects.create(
            evento=evento,
            nombre='Mesa 3',
            capacidad=8,
        )

        response = self.client.post(
            '/dashboard/mesas/guardar-posiciones/',
            {
                'evento_id': evento.id,
                'posiciones': (
                    '[{"id": %s, "x": 120, "y": 80, '
                    '"ancho": 160, "alto": 120}]'
                    % mesa.id
                ),
            },
        )

        mesa.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(mesa.posicion_x, 120)
        self.assertEqual(mesa.posicion_y, 80)
        self.assertEqual(mesa.ancho, 160)
        self.assertEqual(mesa.alto, 120)

    def test_endpoint_no_actualiza_mesa_de_otro_evento(self):
        evento = crear_evento()
        otro_evento = crear_evento()
        mesa = Mesa.objects.create(
            evento=otro_evento,
            nombre='Mesa externa',
            capacidad=8,
        )

        response = self.client.post(
            '/dashboard/mesas/guardar-posiciones/',
            {
                'evento_id': evento.id,
                'posiciones': (
                    '[{"id": %s, "x": 220, "y": 120}]'
                    % mesa.id
                ),
            },
        )

        mesa.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(mesa.posicion_x, 0)
        self.assertEqual(mesa.posicion_y, 0)
