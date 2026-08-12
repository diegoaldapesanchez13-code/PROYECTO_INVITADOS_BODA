from django.test import TestCase

from invitaciones.guest_domain import asegurar_roster_grupo
from invitaciones.models import EventoBoda, Grupoinvitacion, Invitado


class GuestDashboardV2DomainTests(TestCase):
    def setUp(self):
        self.evento = EventoBoda.objects.create(
            novio='Diego',
            novia='Fernanda',
            frase_portada='Test',
            mensaje_general='Test',
            fecha_misa='2027-01-01T12:00:00Z',
            lugar_misa='Ceremonia',
            fecha_fiesta='2027-01-01T15:00:00Z',
            lugar_fiesta='Recepción',
        )

    def test_personal_has_one_nominal_and_optional_extras(self):
        grupo = Grupoinvitacion.objects.create(
            evento=self.evento,
            nombre_grupo='Carlos Ramírez',
            tipo='PERSONAL',
            permitir_acompanantes_extra=True,
            cantidad_extra_permitida=2,
        )

        asegurar_roster_grupo(grupo)

        self.assertEqual(
            grupo.invitados.filter(
                es_acompanante_extra=False
            ).count(),
            1,
        )
        self.assertEqual(
            grupo.invitados.filter(
                es_acompanante_extra=True
            ).count(),
            2,
        )

    def test_family_members_are_independent_people(self):
        grupo = Grupoinvitacion.objects.create(
            evento=self.evento,
            nombre_grupo='Familia Pérez',
            tipo='FAMILIAR',
        )

        ana = Invitado.objects.create(
            grupo=grupo,
            nombre='Ana',
            tipo_persona='ADULTO',
        )
        sofia = Invitado.objects.create(
            grupo=grupo,
            nombre='Sofía',
            tipo_persona='NINO',
        )

        ana.asistira = True
        ana.save(update_fields=['asistira'])

        self.assertEqual(
            grupo.total_personas_v2,
            2,
        )
        self.assertEqual(
            grupo.confirmados_v2,
            1,
        )
        self.assertIsNone(
            sofia.asistira,
        )

    def test_buffet_is_internal_and_derived_by_person_type(self):
        grupo = Grupoinvitacion.objects.create(
            evento=self.evento,
            nombre_grupo='Familia Buffet',
            tipo='FAMILIAR',
        )

        nino = Invitado.objects.create(
            grupo=grupo,
            nombre='N',
            tipo_persona='NINO',
        )
        adulto = Invitado.objects.create(
            grupo=grupo,
            nombre='A',
            tipo_persona='ADULTO',
        )

        self.assertEqual(
            nino.menu_buffet_efectivo,
            'INFANTIL',
        )
        self.assertEqual(
            adulto.menu_buffet_efectivo,
            'ADULTO',
        )

        nino.menu_asignado = 'ADULTO'

        self.assertEqual(
            nino.menu_buffet_efectivo,
            'ADULTO',
        )
