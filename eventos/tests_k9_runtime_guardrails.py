import json
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from catalogo.models import ServicioCatalogo
from documentos.models import DocumentoEvento
from eventos.models import ContratoEvento
from invitaciones.models import DisenoInvitacion, EventoBoda, Grupoinvitacion, Invitado
from itinerario.models import ActividadItinerario
from mesas.models import Mesa
from organizaciones.models import EmpresaSuscriptora, MembresiaEmpresa
from paquetes.models import PaqueteBoda, PaqueteServicio, PropuestaEvento
from presupuesto.models import CategoriaGasto, GastoEvento, PagoClienteEvento, PagoEvento
from proveedores.models import Proveedor, ServicioEvento
from tareas.models import TareaEvento


@override_settings(MEDIA_ROOT="media/test/k9_runtime_guardrails")
class K9RuntimeGuardrailsTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.empresa = EmpresaSuscriptora.objects.create(
            nombre_comercial="Empresa Guardrails",
            slug="empresa-guardrails",
        )
        self.otra_empresa = EmpresaSuscriptora.objects.create(
            nombre_comercial="Otra Guardrails",
            slug="otra-guardrails",
        )
        self.admin = User.objects.create_user(
            username="admin-guardrails",
            password="Pass-Guardrails-2026!",
        )
        self.planner = User.objects.create_user(
            username="planner-guardrails",
            password="Pass-Guardrails-2026!",
        )
        self.cliente = User.objects.create_user(
            username="cliente-guardrails",
            password="Pass-Guardrails-2026!",
        )
        self.proveedor_user = User.objects.create_user(
            username="proveedor-guardrails",
            password="Pass-Guardrails-2026!",
        )
        self.outsider = User.objects.create_user(
            username="outsider-guardrails",
            password="Pass-Guardrails-2026!",
        )
        for user, rol in [
            (self.admin, "ADMIN_EMPRESA"),
            (self.planner, "WEDDING_PLANNER"),
            (self.cliente, "CLIENTE"),
            (self.proveedor_user, "PROVEEDOR"),
        ]:
            MembresiaEmpresa.objects.create(empresa=self.empresa, usuario=user, rol=rol)
        MembresiaEmpresa.objects.create(
            empresa=self.otra_empresa,
            usuario=self.outsider,
            rol="ADMIN_EMPRESA",
        )

        now = timezone.now()
        self.evento = EventoBoda.objects.create(
            empresa=self.empresa,
            wedding_planner=self.planner,
            nombre_evento="Evento Guardrails",
            novio="A",
            novia="B",
            frase_portada="Test",
            mensaje_general="Test",
            fecha_misa=now + timedelta(days=20),
            lugar_misa="Ceremonia",
            fecha_fiesta=now + timedelta(days=20),
            lugar_fiesta="Recepcion",
            capacidad_contratada=100,
        )
        self.evento.clientes.add(self.cliente)
        self.proveedor = Proveedor.objects.create(
            empresa=self.empresa,
            usuario=self.proveedor_user,
            nombre_comercial="Proveedor Guardrails",
            tipo_proveedor="DECORACION",
        )
        self.servicio = ServicioEvento.objects.create(
            evento=self.evento,
            proveedor=self.proveedor,
            nombre_servicio="Decoracion Guardrails",
            origen="MANUAL",
            modalidad="ADICIONAL",
        )
        self.categoria = CategoriaGasto.objects.create(nombre="Guardrails")
        self.catalogo = ServicioCatalogo.objects.create(
            empresa=self.empresa,
            nombre="Audio Guardrails",
            categoria="AUDIO_ILUMINACION",
            unidad="EVENTO",
        )
        self.paquete = PaqueteBoda.objects.create(
            empresa=self.empresa,
            nombre="Paquete Guardrails",
            precio_adulto=Decimal("1000.00"),
            precio_nino=Decimal("500.00"),
            cargo_fijo=Decimal("10000.00"),
        )
        PaqueteServicio.objects.create(
            paquete=self.paquete,
            servicio_catalogo=self.catalogo,
            cantidad=1,
        )
        self.grupo = Grupoinvitacion.objects.create(
            evento=self.evento,
            nombre_grupo="Familia Guardrails",
            tipo="PERSONAL",
            cantidad_maxima=1,
        )
        self.invitado = Invitado.objects.create(
            grupo=self.grupo,
            nombre="Titular Guardrails",
            tipo_persona="ADULTO",
            orden=0,
        )
        document = {
            "schemaVersion": 3,
            "page": {"name": "Guardrails"},
            "sections": [],
            "nodes": [],
        }
        DisenoInvitacion.objects.create(
            evento=self.evento,
            documento_builder_borrador=document,
            documento_builder_publicado=document,
            estado="PUBLICADO",
        )

    def workspace_url(self, name, **extra):
        kwargs = {
            "empresa_slug": self.empresa.slug,
            "evento_id": self.evento.id,
        }
        kwargs.update(extra)
        return reverse(name, kwargs=kwargs)

    def accepted_proposal(self):
        return PropuestaEvento.objects.create(
            empresa=self.empresa,
            evento=self.evento,
            paquete=self.paquete,
            adultos=10,
            ninos=0,
            estado="ACEPTADO",
            created_by=self.admin,
            updated_by=self.admin,
        )

    def test_legacy_payment_review_is_blocked_but_k9_review_updates(self):
        pago = PagoClienteEvento.objects.create(
            evento=self.evento,
            registrado_por=self.cliente,
            concepto="Anticipo",
            monto=Decimal("1500.00"),
            fecha_pago=timezone.localdate(),
            metodo_pago="TRANSFERENCIA",
            comprobante=SimpleUploadedFile("cliente.pdf", b"%PDF-1.4"),
        )
        self.client.force_login(self.admin)

        response = self.client.post(
            reverse("pago_cliente_evento_revisar", args=[pago.id]),
            {"estado": "RECIBIDO", "comentario_equipo": "Legacy"},
        )
        self.assertEqual(response.status_code, 302)
        pago.refresh_from_db()
        self.assertEqual(pago.estado, "PENDIENTE")
        self.assertIsNone(pago.revisado_por)

        response = self.client.post(
            self.workspace_url("k9_finanzas_pago_cliente_revisar", pago_id=pago.id),
            {"estado": "RECIBIDO", "comentario_equipo": "K9"},
        )
        self.assertEqual(response.status_code, 302)
        pago.refresh_from_db()
        self.assertEqual(pago.estado, "RECIBIDO")
        self.assertEqual(pago.revisado_por, self.admin)

    def test_legacy_contract_posts_are_blocked_but_k9_commercial_generates_and_materializes(self):
        propuesta = self.accepted_proposal()
        self.client.force_login(self.admin)

        response = self.client.post(
            reverse(
                "eventos_contrato_generar",
                kwargs={"empresa_slug": self.empresa.slug, "propuesta_id": propuesta.id},
            )
        )
        self.assertEqual(response.status_code, 302)
        self.assertFalse(ContratoEvento.objects.filter(propuesta_origen=propuesta).exists())

        response = self.client.post(
            self.workspace_url("k9_evento_comercial") + f"?propuesta={propuesta.id}",
            {"accion": "generar_contrato", "propuesta_id": propuesta.id},
        )
        self.assertEqual(response.status_code, 302)
        contrato = ContratoEvento.objects.get(propuesta_origen=propuesta)

        response = self.client.post(
            reverse(
                "eventos_contrato_materializar",
                kwargs={"empresa_slug": self.empresa.slug, "contrato_id": contrato.id},
            )
        )
        self.assertEqual(response.status_code, 302)
        self.assertFalse(ServicioEvento.objects.filter(contrato_origen=contrato).exists())

        response = self.client.post(
            self.workspace_url("k9_evento_comercial") + f"?propuesta={propuesta.id}",
            {"accion": "materializar_contrato", "contrato_id": contrato.id},
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(ServicioEvento.objects.filter(contrato_origen=contrato).exists())

    def test_legacy_lifecycle_and_dashboard_action_are_blocked_but_k9_service_works(self):
        self.client.force_login(self.admin)

        response = self.client.post(
            reverse(
                "eventos_servicio_cancelar",
                kwargs={"empresa_slug": self.empresa.slug, "servicio_id": self.servicio.id},
            ),
            {"motivo": "Legacy"},
        )
        self.assertEqual(response.status_code, 302)
        self.servicio.refresh_from_db()
        self.assertNotEqual(self.servicio.estado_operativo, "CANCELADO")

        response = self.client.post(
            reverse("dashboard"),
            {
                "accion": "agregar_servicio_evento",
                "evento_id": self.evento.id,
                "nombre_servicio": "Legacy dashboard",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertFalse(
            ServicioEvento.objects.filter(evento=self.evento, nombre_servicio="Legacy dashboard").exists()
        )

        response = self.client.post(
            self.workspace_url("k9_evento_servicios") + f"?servicio={self.servicio.id}",
            {
                "accion": "cancelar",
                "servicio_id": self.servicio.id,
                "motivo": "K9",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.servicio.refresh_from_db()
        self.assertEqual(self.servicio.estado_operativo, "CANCELADO")

    def test_portal_cliente_can_still_register_payment(self):
        self.client.force_login(self.cliente)
        response = self.client.post(
            reverse("pago_cliente_evento_registrar", args=[self.evento.id]),
            {
                "monto": "2500.00",
                "concepto": "Pago cliente vivo",
                "metodo_pago": "TRANSFERENCIA",
                "comprobante": SimpleUploadedFile("pago.pdf", b"%PDF-1.4"),
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            PagoClienteEvento.objects.filter(
                evento=self.evento,
                concepto="Pago cliente vivo",
            ).exists()
        )

    def test_portal_proveedor_still_accessible(self):
        self.client.force_login(self.proveedor_user)
        response = self.client.get(reverse("portal_proveedor"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Mis servicios")

    def test_colaboracion_still_writes_inside_authorized_subdomain(self):
        self.client.force_login(self.planner)
        response = self.client.post(
            reverse("colaboracion_k86_tarea_crear", args=[self.servicio.id]),
            {
                "titulo": "Tarea colaboracion viva",
                "prioridad": "ALTA",
                "categoria": "PROVEEDORES",
            },
        )
        self.assertEqual(response.status_code, 302)
        tarea = TareaEvento.objects.get(titulo="Tarea colaboracion viva")
        self.assertEqual(tarea.servicio_evento, self.servicio)

    def test_rsvp_public_still_updates_guest(self):
        response = self.client.post(
            reverse("builder_public_rsvp_api", args=[self.grupo.codigo]),
            data=json.dumps({"guestId": self.invitado.id, "attending": True}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.invitado.refresh_from_db()
        self.assertIs(self.invitado.asistira, True)

    def test_builder_editor_still_accessible(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse("editor_invitacion_visual", args=[self.evento.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "dirtec-builder-bootstrap")

    def test_mesas_and_calendario_legacy_are_not_blocked(self):
        self.client.force_login(self.admin)
        response = self.client.post(
            reverse("mesas_visual"),
            {
                "accion": "crear_mesa",
                "evento_id": self.evento.id,
                "nombre_mesa": "Mesa viva",
                "capacidad_mesa": "8",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Mesa.objects.filter(evento=self.evento, nombre="Mesa viva").exists())

        ActividadItinerario.objects.create(
            evento=self.evento,
            titulo="Agenda viva",
            fecha=timezone.localdate() + timedelta(days=3),
            hora_inicio=timezone.now().time(),
        )
        response = self.client.get(
            reverse("calendario_eventos_json"),
            {"evento": self.evento.id},
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json())

    def test_cross_tenant_still_rejected(self):
        self.client.force_login(self.outsider)
        response = self.client.post(
            reverse(
                "eventos_contrato_generar",
                kwargs={"empresa_slug": self.empresa.slug, "propuesta_id": self.accepted_proposal().id},
            )
        )
        self.assertEqual(response.status_code, 404)
