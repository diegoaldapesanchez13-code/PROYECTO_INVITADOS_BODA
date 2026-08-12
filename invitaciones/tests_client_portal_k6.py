from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from aprobaciones.models import AprobacionEvento
from documentos.models import DocumentoEvento
from invitaciones.models import EventoBoda
from organizaciones.models import (
    EmpresaSuscriptora,
    MembresiaEmpresa,
)
from tareas.models import TareaEvento


class ClientPortalK6Tests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.empresa = EmpresaSuscriptora.objects.create(
            nombre_comercial="Casa Cliente K6",
            slug="casa-cliente-k6",
        )
        self.cliente = User.objects.create_user(
            username="cliente_k6",
            password="test123",
            first_name="Fernanda",
        )
        MembresiaEmpresa.objects.create(
            empresa=self.empresa,
            usuario=self.cliente,
            rol="CLIENTE",
        )
        self.planner = User.objects.create_user(
            username="planner_k6",
            password="test123",
        )
        MembresiaEmpresa.objects.create(
            empresa=self.empresa,
            usuario=self.planner,
            rol="WEDDING_PLANNER",
        )
        self.evento = EventoBoda.objects.create(
            empresa=self.empresa,
            wedding_planner=self.planner,
            novio="A",
            novia="B",
            frase_portada="Test",
            mensaje_general="Test",
            fecha_misa=timezone.now() + timedelta(days=30),
            lugar_misa="Ceremonia K6",
            fecha_fiesta=timezone.now() + timedelta(days=30),
            lugar_fiesta="Recepcion K6",
        )
        self.evento.clientes.add(self.cliente)
        self.client.force_login(self.cliente)

    def test_client_gets_client_specific_workspace(self):
        response = self.client.get(
            reverse("cliente_dashboard")
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "Mi evento",
        )
        self.assertContains(
            response,
            "Lo que necesitas hacer",
        )
        self.assertContains(
            response,
            "Agenda",
        )
        self.assertContains(
            response,
            "Aprobaciones",
        )
        self.assertContains(
            response,
            "Documentos",
        )

    def test_internal_planner_task_is_not_exposed_to_client(self):
        TareaEvento.objects.create(
            evento=self.evento,
            titulo="Costo interno proveedor",
            responsable=self.planner,
            fecha_limite=timezone.localdate() + timedelta(days=1),
        )
        TareaEvento.objects.create(
            evento=self.evento,
            titulo="Prueba de menu cliente",
            responsable=self.cliente,
            fecha_inicio=timezone.localdate() + timedelta(days=2),
        )

        response = self.client.get(
            reverse("cliente_dashboard")
        )
        self.assertContains(
            response,
            "Prueba de menu cliente",
        )
        self.assertNotContains(
            response,
            "Costo interno proveedor",
        )

    def test_only_client_visible_documents_are_exposed(self):
        # Avoid actual FileField storage: unsaved file paths are sufficient for
        # queryset visibility assertions in the rendered portal.
        visible = DocumentoEvento.objects.create(
            evento=self.evento,
            tipo_documento="MENU",
            titulo="Menu visible",
            archivo="documentos/eventos/menu.pdf",
            visible_cliente=True,
        )
        DocumentoEvento.objects.create(
            evento=self.evento,
            tipo_documento="CONTRATO",
            titulo="Contrato interno",
            archivo="documentos/eventos/interno.pdf",
            visible_cliente=False,
        )

        response = self.client.get(
            reverse("cliente_dashboard")
        )
        self.assertContains(
            response,
            visible.titulo,
        )
        self.assertNotContains(
            response,
            "Contrato interno",
        )

    def test_pending_approval_can_be_answered_and_returns_to_client_dashboard(self):
        approval = AprobacionEvento.objects.create(
            evento=self.evento,
            tipo="MENU",
            titulo="Aprobar menu",
            estado="PENDIENTE",
        )

        response = self.client.post(
            reverse(
                "responder_aprobacion_cliente",
                args=[approval.id],
            ),
            {
                "accion": "aprobar",
                "comentario": "De acuerdo",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertIn(
            "/cliente/dashboard/",
            response["Location"],
        )

        approval.refresh_from_db()
        self.assertEqual(
            approval.estado,
            "APROBADO",
        )
        self.assertEqual(
            approval.aprobado_por,
            self.cliente,
        )

    def test_client_portal_does_not_render_internal_financial_summary(self):
        response = self.client.get(
            reverse("cliente_dashboard")
        )
        content = response.content.decode()
        self.assertNotIn(
            "Total evento",
            content,
        )
        self.assertNotIn(
            "Saldo",
            content,
        )
        self.assertNotIn(
            ">Pagado<",
            content,
        )
