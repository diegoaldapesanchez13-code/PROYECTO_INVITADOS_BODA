from django.test import TestCase

from invitaciones.guest_domain import asegurar_roster_grupo, sincronizar_rsvp_personal_legacy
from invitaciones.models import EventoBoda, Grupoinvitacion, Invitado


class GuestDomainV2Tests(TestCase):
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

    def test_personal_crea_una_persona_nominal_sin_extras(self):
        grupo = Grupoinvitacion.objects.create(
            evento=self.evento,
            nombre_grupo='José Fernando Sánchez',
            tipo='PERSONAL',
        )
        asegurar_roster_grupo(grupo)

        self.assertEqual(grupo.invitados.count(), 1)
        principal = grupo.invitados.get()
        self.assertEqual(principal.nombre, 'José Fernando Sánchez')
        self.assertFalse(principal.es_acompanante_extra)

    def test_acompanantes_solo_existen_si_organizador_los_habilita(self):
        grupo = Grupoinvitacion.objects.create(
            evento=self.evento,
            nombre_grupo='Invitación con extras',
            tipo='PERSONAL',
            permitir_acompanantes_extra=True,
            cantidad_extra_permitida=2,
        )
        asegurar_roster_grupo(grupo)

        self.assertEqual(grupo.invitados_nominales.count(), 1)
        self.assertEqual(grupo.acompanantes_extra.count(), 2)
        self.assertEqual(
            list(grupo.acompanantes_extra.values_list('nombre', flat=True)),
            ['Acompañante 1', 'Acompañante 2'],
        )

    def test_familiar_conserva_integrantes_nominales_y_extras_separados(self):
        grupo = Grupoinvitacion.objects.create(
            evento=self.evento,
            nombre_grupo='Familia Pérez',
            tipo='FAMILIAR',
            permitir_acompanantes_extra=True,
            cantidad_extra_permitida=1,
        )
        Invitado.objects.create(grupo=grupo, nombre='Ana Pérez', tipo_persona='ADULTO')
        Invitado.objects.create(grupo=grupo, nombre='Sofía Pérez', tipo_persona='NINO')
        asegurar_roster_grupo(grupo)

        self.assertEqual(grupo.invitados_nominales.count(), 2)
        self.assertEqual(grupo.acompanantes_extra.count(), 1)

    def test_rsvp_legacy_personal_se_proyecta_al_roster_sin_inventar_pases(self):
        grupo = Grupoinvitacion.objects.create(
            evento=self.evento,
            nombre_grupo='José Fernando',
            tipo='PERSONAL',
            permitir_acompanantes_extra=True,
            cantidad_extra_permitida=2,
        )
        asegurar_roster_grupo(grupo)
        sincronizar_rsvp_personal_legacy(grupo, True, 2)

        self.assertEqual(grupo.invitados.filter(asistira=True).count(), 2)
        self.assertEqual(grupo.invitados.filter(asistira=False).count(), 1)
        self.assertEqual(grupo.total_lugares, 3)
        self.assertEqual(grupo.lugares_asistiran, 2)

    def test_buffet_default_depende_de_adulto_nino_pero_organizador_puede_override(self):
        grupo = Grupoinvitacion.objects.create(
            evento=self.evento,
            nombre_grupo='Familia Buffet',
            tipo='FAMILIAR',
        )
        nino = Invitado.objects.create(grupo=grupo, nombre='Sofía', tipo_persona='NINO')
        self.assertEqual(nino.menu_buffet_efectivo, 'INFANTIL')

        nino.menu_asignado = 'ADULTO'
        self.assertEqual(nino.menu_buffet_efectivo, 'ADULTO')
