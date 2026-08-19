from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.test import TestCase
from django.utils import timezone

from eventos.event_domain import (
    archivar_evento,
    cancelar_evento,
    crear_evento_generico,
    eliminar_evento_error,
    evaluar_eliminacion_evento,
    restaurar_evento,
)
from eventos.models import ContratoEvento
from invitaciones.models import EventoBoda
from organizaciones.models import EmpresaSuscriptora, MembresiaEmpresa


class GenericEventDomainR2ATests(TestCase):
    def setUp(self):
        self.User = get_user_model()
        self.empresa = EmpresaSuscriptora.objects.create(
            nombre_comercial="Empresa R2A",
            slug="empresa-r2a",
        )
        self.otra_empresa = EmpresaSuscriptora.objects.create(
            nombre_comercial="Otra Empresa R2A",
            slug="otra-empresa-r2a",
        )
        self.admin = self.User.objects.create_user(
            username="admin-r2a",
            password="Pass-R2A-2026!",
        )
        MembresiaEmpresa.objects.create(
            empresa=self.empresa,
            usuario=self.admin,
            rol="ADMIN_EMPRESA",
        )
        self.planner = self.User.objects.create_user(
            username="planner-r2a",
            password="Pass-R2A-2026!",
        )
        MembresiaEmpresa.objects.create(
            empresa=self.empresa,
            usuario=self.planner,
            rol="WEDDING_PLANNER",
        )

    def test_model_can_exist_without_legacy_wedding_data(self):
        evento = EventoBoda.objects.create(
            empresa=self.empresa,
            nombre_evento="Evento mínimo",
        )
        self.assertEqual(evento.estado, "BORRADOR")
        self.assertEqual(evento.tipo_evento, "OTRO")
        self.assertEqual(evento.novio, "")
        self.assertEqual(evento.novia, "")
        self.assertIsNone(evento.fecha_misa)
        self.assertIsNone(evento.fecha_fiesta)

    def test_generic_service_creates_without_fake_legacy_values(self):
        evento = crear_evento_generico(
            empresa=self.empresa,
            usuario=self.admin,
            nombre_evento="  Cena   Anual  ",
        )
        self.assertEqual(evento.nombre_evento, "Cena Anual")
        self.assertEqual(evento.novio, "")
        self.assertEqual(evento.lugar_misa, "")
        self.assertIsNone(evento.fecha_inicio)
        self.assertIsNone(evento.fecha_fiesta)

    def test_generic_creation_with_date_keeps_legacy_date_compatibility(self):
        fecha = timezone.now()
        evento = crear_evento_generico(
            empresa=self.empresa,
            usuario=self.admin,
            nombre_evento="Evento con fecha",
            fecha_inicio=fecha,
        )
        self.assertEqual(evento.fecha_inicio, fecha)
        self.assertEqual(evento.fecha_fiesta, fecha)

    def test_generic_creation_requires_name(self):
        with self.assertRaises(ValidationError):
            crear_evento_generico(
                empresa=self.empresa,
                usuario=self.admin,
                nombre_evento="   ",
            )

    def test_planner_can_create_event_and_is_not_automatically_assigned(self):
        evento = crear_evento_generico(
            empresa=self.empresa,
            usuario=self.planner,
            nombre_evento="Lead planner",
        )
        self.assertIsNone(evento.wedding_planner)

    def test_cancel_preserves_event_and_records_actor(self):
        evento = crear_evento_generico(
            empresa=self.empresa,
            usuario=self.admin,
            nombre_evento="Evento cancelable",
        )
        cancelar_evento(evento, usuario=self.admin, motivo="Cliente cancelo")
        evento.refresh_from_db()
        self.assertEqual(evento.estado, "CANCELADO")
        self.assertEqual(evento.cancelado_por, self.admin)
        self.assertIsNotNone(evento.cancelado_en)
        self.assertFalse(evento.activo)

    def test_archive_and_restore_return_previous_state(self):
        evento = crear_evento_generico(
            empresa=self.empresa,
            usuario=self.admin,
            nombre_evento="Evento archivo",
        )
        evento.estado = "FINALIZADO"
        evento.save(update_fields=["estado"])
        archivar_evento(evento, usuario=self.admin)
        evento.refresh_from_db()
        self.assertEqual(evento.estado, "ARCHIVADO")
        self.assertEqual(evento.estado_previo_archivado, "FINALIZADO")

        restaurar_evento(evento, usuario=self.admin)
        evento.refresh_from_db()
        self.assertEqual(evento.estado, "FINALIZADO")
        self.assertEqual(evento.estado_previo_archivado, "")

    def test_fresh_event_is_deletable_even_with_structural_audit(self):
        evento = crear_evento_generico(
            empresa=self.empresa,
            usuario=self.admin,
            nombre_evento="Error de captura",
        )
        evaluacion = evaluar_eliminacion_evento(evento)
        self.assertTrue(evaluacion.permitido)
        evento_id = evento.id
        eliminar_evento_error(evento, usuario=self.admin)
        self.assertFalse(EventoBoda.objects.filter(pk=evento_id).exists())

    def test_contract_blocks_error_delete(self):
        evento = crear_evento_generico(
            empresa=self.empresa,
            usuario=self.admin,
            nombre_evento="Evento contractual",
        )
        ContratoEvento.objects.create(evento=evento, version=1)
        evaluacion = evaluar_eliminacion_evento(evento)
        self.assertFalse(evaluacion.permitido)
        self.assertTrue(any("contrato" in reason.lower() for reason in evaluacion.motivos))
        with self.assertRaises(ValidationError):
            eliminar_evento_error(evento, usuario=self.admin)

    def test_cross_tenant_user_cannot_delete(self):
        evento = crear_evento_generico(
            empresa=self.empresa,
            usuario=self.admin,
            nombre_evento="Evento tenant A",
        )
        outsider = self.User.objects.create_user(
            username="outsider-r2a",
            password="Pass-R2A-2026!",
        )
        MembresiaEmpresa.objects.create(
            empresa=self.otra_empresa,
            usuario=outsider,
            rol="ADMIN_EMPRESA",
        )
        with self.assertRaises(PermissionDenied):
            eliminar_evento_error(evento, usuario=outsider)

    def test_unassigned_planner_cannot_cancel_company_event(self):
        evento = crear_evento_generico(
            empresa=self.empresa,
            usuario=self.admin,
            nombre_evento="Evento admin",
        )
        with self.assertRaises(PermissionDenied):
            cancelar_evento(evento, usuario=self.planner)
