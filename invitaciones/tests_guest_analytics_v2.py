from django.test import TestCase

from invitaciones.guest_analytics import (
    resumen_invitados_evento,
)
from invitaciones.models import (
    EventoBoda,
    Grupoinvitacion,
    Invitado,
)
from mesas.models import AsignacionMesa, Mesa


class GuestAnalyticsV2Tests(TestCase):
    def setUp(self):
        self.evento = EventoBoda.objects.create(
            novio="Diego",
            novia="Fernanda",
            frase_portada="Test",
            mensaje_general="Test",
            fecha_misa="2027-01-01T12:00:00Z",
            lugar_misa="Ceremonia",
            fecha_fiesta="2027-01-01T15:00:00Z",
            lugar_fiesta="Recepción",
        )
        self.familia = Grupoinvitacion.objects.create(
            evento=self.evento,
            nombre_grupo="Familia Métricas",
            tipo="FAMILIAR",
        )

    def crear(
        self,
        nombre,
        *,
        persona="ADULTO",
        menu="SEGUN_TIPO",
        asistira=None,
    ):
        return Invitado.objects.create(
            grupo=self.familia,
            nombre=nombre,
            tipo_persona=persona,
            menu_asignado=menu,
            asistira=asistira,
        )

    def test_rsvp_counts_are_person_based(self):
        self.crear("A", asistira=True)
        self.crear("B", asistira=False)
        self.crear("C", asistira=None)

        resumen = resumen_invitados_evento(
            self.evento,
        )

        self.assertEqual(
            resumen["total_personas"],
            3,
        )
        self.assertEqual(
            resumen["confirmados"],
            1,
        )
        self.assertEqual(
            resumen["no_asisten"],
            1,
        )
        self.assertEqual(
            resumen["pendientes"],
            1,
        )

    def test_buffet_uses_internal_menu_assignment_not_only_person_type(self):
        self.crear(
            "Niño con menú adulto",
            persona="NINO",
            menu="ADULTO",
            asistira=True,
        )
        self.crear(
            "Adulto con menú infantil",
            persona="ADULTO",
            menu="INFANTIL",
            asistira=True,
        )
        self.crear(
            "Niño default",
            persona="NINO",
            menu="SEGUN_TIPO",
            asistira=True,
        )

        resumen = resumen_invitados_evento(
            self.evento,
        )

        self.assertEqual(
            resumen["adultos_confirmados_persona"],
            1,
        )
        self.assertEqual(
            resumen["ninos_confirmados_persona"],
            2,
        )
        self.assertEqual(
            resumen["buffet_adultos"],
            1,
        )
        self.assertEqual(
            resumen["buffet_infantiles"],
            2,
        )

    def test_non_attending_people_do_not_count_for_buffet(self):
        self.crear(
            "No asiste",
            menu="ADULTO",
            asistira=False,
        )
        self.crear(
            "Pendiente",
            menu="INFANTIL",
            asistira=None,
        )

        resumen = resumen_invitados_evento(
            self.evento,
        )

        self.assertEqual(
            resumen["buffet_adultos"],
            0,
        )
        self.assertEqual(
            resumen["buffet_infantiles"],
            0,
        )

    def test_confirmed_without_table_uses_individual_assignments(self):
        invitado = self.crear(
            "Con mesa",
            asistira=True,
        )
        sin_mesa = self.crear(
            "Sin mesa",
            asistira=True,
        )
        mesa = Mesa.objects.create(
            evento=self.evento,
            nombre="Mesa 1",
            capacidad=10,
        )
        AsignacionMesa.objects.create(
            mesa=mesa,
            invitado=invitado,
        )

        resumen = resumen_invitados_evento(
            self.evento,
            incluir_mesas=True,
        )

        self.assertEqual(
            resumen["confirmados"],
            2,
        )
        self.assertEqual(
            resumen["confirmados_sin_mesa"],
            1,
        )

    def test_personal_and_extra_require_individual_table_assignments(self):
        personal = Grupoinvitacion.objects.create(
            evento=self.evento,
            nombre_grupo="Carlos",
            tipo="PERSONAL",
            permitir_acompanantes_extra=True,
            cantidad_extra_permitida=1,
        )
        titular = Invitado.objects.create(
            grupo=personal,
            nombre="Carlos",
            asistira=True,
            es_acompanante_extra=False,
        )
        extra = Invitado.objects.create(
            grupo=personal,
            nombre="Acompañante 1",
            asistira=True,
            es_acompanante_extra=True,
        )
        mesa = Mesa.objects.create(
            evento=self.evento,
            nombre="Mesa Individual",
            capacidad=10,
        )
        AsignacionMesa.objects.create(
            mesa=mesa,
            invitado=titular,
        )

        resumen = resumen_invitados_evento(
            self.evento,
            incluir_mesas=True,
        )

        self.assertEqual(
            resumen["confirmados_sin_mesa"],
            1,
        )

        AsignacionMesa.objects.create(
            mesa=mesa,
            invitado=extra,
        )
        resumen = resumen_invitados_evento(
            self.evento,
            incluir_mesas=True,
        )
        self.assertEqual(
            resumen["confirmados_sin_mesa"],
            0,
        )
