from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from core.services.ciclo_vida_operativo import cancelar_servicio_evento
from eventos.workspace_services import guardar_servicio_operativo
from invitaciones.models import EventoBoda
from organizaciones.models import EmpresaSuscriptora
from proveedores.models import ServicioEvento
from proveedores.service_lifecycle import (
    aplicar_estado_comercial,
    aplicar_estado_operativo,
    aplicar_estado_proveedor,
    legacy_estado_canonico,
    servicio_consistente,
    sincronizar_estado_legacy,
)


class D4ServiceLifecycleTests(TestCase):
    def setUp(self):
        User=get_user_model()
        self.user=User.objects.create_user(username="d4-user",password="test123")
        self.empresa=EmpresaSuscriptora.objects.create(nombre_comercial="Empresa D4",slug="empresa-d4")
        now=timezone.now()
        self.evento=EventoBoda.objects.create(
            empresa=self.empresa,nombre_evento="Evento D4",novio="A",novia="B",
            frase_portada="D4",mensaje_general="D4",fecha_misa=now,lugar_misa="X",
            fecha_fiesta=now,lugar_fiesta="Y",
        )

    def servicio(self, **kwargs):
        data=dict(evento=self.evento,nombre_servicio="Servicio D4")
        data.update(kwargs)
        return ServicioEvento.objects.create(**data)

    def test_commercial_operational_provider_are_independent_dimensions(self):
        servicio=self.servicio(estado_comercial="CONTRATADO",estado_operativo="PROGRAMADO")
        aplicar_estado_proveedor(servicio,"CONFIRMADO")
        self.assertEqual(servicio.estado_comercial,"CONTRATADO")
        self.assertEqual(servicio.estado_operativo,"PROGRAMADO")
        self.assertEqual(servicio.estado_proveedor,"CONFIRMADO")

    def test_legacy_state_is_derived_from_canonical_fields(self):
        servicio=self.servicio(estado="SOLICITADO",estado_comercial="CONTRATADO",estado_operativo="PENDIENTE")
        sincronizar_estado_legacy(servicio)
        self.assertEqual(servicio.estado,"CONTRATADO")
        aplicar_estado_operativo(servicio,"PROGRAMADO")
        self.assertEqual(servicio.estado,"CONTRATADO")
        aplicar_estado_operativo(servicio,"LISTO")
        aplicar_estado_operativo(servicio,"EN_EJECUCION")
        aplicar_estado_operativo(servicio,"COMPLETADO")
        self.assertEqual(servicio.estado,"SERVICIO_COMPLETADO")

    def test_invalid_operational_jump_is_rejected(self):
        servicio=self.servicio(estado_operativo="PENDIENTE")
        with self.assertRaises(ValidationError):
            aplicar_estado_operativo(servicio,"COMPLETADO")

    def test_completed_and_cancelled_are_terminal(self):
        completo=self.servicio(nombre_servicio="Completo",estado_operativo="COMPLETADO")
        with self.assertRaises(ValidationError):
            aplicar_estado_operativo(completo,"PROGRAMADO")
        cancelado=self.servicio(
            nombre_servicio="Cancelado",estado="CANCELADO",
            estado_comercial="CANCELADO",estado_operativo="CANCELADO"
        )
        with self.assertRaises(ValidationError):
            aplicar_estado_comercial(cancelado,"CONTRATADO")

    def test_cancellation_synchronizes_three_internal_states(self):
        servicio=self.servicio(
            estado="CONTRATADO",estado_comercial="CONTRATADO",estado_operativo="PROGRAMADO"
        )
        cancelar_servicio_evento(servicio,actor=self.user,motivo="D4")
        servicio.refresh_from_db()
        self.assertEqual(servicio.estado,"CANCELADO")
        self.assertEqual(servicio.estado_comercial,"CANCELADO")
        self.assertEqual(servicio.estado_operativo,"CANCELADO")
        self.assertEqual(servicio.estado_proveedor,"PENDIENTE")
        self.assertTrue(servicio_consistente(servicio))

    def test_financial_legacy_marker_is_preserved_until_terminal_transition(self):
        servicio=self.servicio(
            estado="LIQUIDADO",estado_comercial="CONTRATADO",estado_operativo="PROGRAMADO"
        )
        sincronizar_estado_legacy(servicio)
        self.assertEqual(servicio.estado,"LIQUIDADO")
        aplicar_estado_operativo(servicio,"CANCELADO")
        self.assertEqual(servicio.estado,"CANCELADO")

    def test_workspace_rejects_illegal_operational_transition(self):
        servicio=self.servicio(
            estado="CONTRATADO",estado_comercial="CONTRATADO",estado_operativo="PENDIENTE"
        )
        with self.assertRaises(ValidationError):
            guardar_servicio_operativo(
                servicio,
                evento=self.evento,
                cleaned_data={
                    "nombre_servicio":"Servicio D4",
                    "estado_operativo":"COMPLETADO",
                },
                user=self.user,
            )
