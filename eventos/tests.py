from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from invitaciones.models import EventoBoda
from organizaciones.models import EmpresaSuscriptora, MembresiaEmpresa

from .models import ContratoEvento, ParticipanteEvento
from .services import sincronizar_participantes_legacy


class EventDomainFoundationTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.empresa = EmpresaSuscriptora.objects.create(
            nombre_comercial='Empresa K82', slug='empresa-k82'
        )
        self.planner = User.objects.create_user(username='planner-k82', password='test')
        self.cliente = User.objects.create_user(username='cliente-k82', password='test')
        MembresiaEmpresa.objects.create(
            empresa=self.empresa,
            usuario=self.planner,
            rol='WEDDING_PLANNER',
            activo=True,
        )
        now = timezone.now()
        self.evento = EventoBoda.objects.create(
            empresa=self.empresa,
            nombre_evento='Evento Foundation',
            novio='Diego',
            novia='Fernanda',
            frase_portada='Test',
            mensaje_general='Test',
            fecha_misa=now,
            lugar_misa='Ceremonia',
            fecha_fiesta=now,
            lugar_fiesta='Recepcion',
            wedding_planner=self.planner,
        )
        self.evento.clientes.add(self.cliente)

    def test_sync_legacy_creates_domain_participants(self):
        result = sincronizar_participantes_legacy(self.evento)
        self.assertEqual(result['creados'], 0)
        self.assertTrue(
            ParticipanteEvento.objects.filter(
                evento=self.evento, usuario=self.planner, rol='PLANNER'
            ).exists()
        )
        self.assertTrue(
            ParticipanteEvento.objects.filter(
                evento=self.evento, usuario=self.cliente, rol='CLIENTE'
            ).exists()
        )

    def test_sync_is_idempotent(self):
        sincronizar_participantes_legacy(self.evento)
        sincronizar_participantes_legacy(self.evento)
        self.assertEqual(ParticipanteEvento.objects.filter(evento=self.evento).count(), 2)


    def test_legacy_client_removal_deactivates_domain_participant(self):
        self.evento.clientes.remove(self.cliente)
        participante = ParticipanteEvento.objects.get(
            evento=self.evento, usuario=self.cliente, rol='CLIENTE'
        )
        self.assertFalse(participante.activo)

    def test_legacy_planner_change_deactivates_previous_participant(self):
        User = get_user_model()
        nuevo = User.objects.create_user(username='planner-k82-2', password='test')
        MembresiaEmpresa.objects.create(
            empresa=self.empresa, usuario=nuevo, rol='WEDDING_PLANNER', activo=True
        )
        self.evento.wedding_planner = nuevo
        self.evento.save(update_fields=['wedding_planner'])
        anterior = ParticipanteEvento.objects.get(
            evento=self.evento, usuario=self.planner, rol='PLANNER'
        )
        actual = ParticipanteEvento.objects.get(
            evento=self.evento, usuario=nuevo, rol='PLANNER'
        )
        self.assertFalse(anterior.activo)
        self.assertTrue(actual.activo)

    def test_cross_tenant_planner_is_rejected(self):
        User = get_user_model()
        outsider = User.objects.create_user(username='outsider-k82', password='test')
        participante = ParticipanteEvento(
            evento=self.evento,
            usuario=outsider,
            rol='PLANNER',
        )
        with self.assertRaises(ValidationError):
            participante.full_clean()

    def test_contract_versions_are_event_scoped(self):
        ContratoEvento.objects.create(evento=self.evento, version=1, monto_base=1000)
        with self.assertRaises(Exception):
            ContratoEvento.objects.create(evento=self.evento, version=1, monto_base=1200)
