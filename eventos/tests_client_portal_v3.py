from datetime import time, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from colaboracion.models import AprobacionServicio, CotizacionServicio, PropuestaServicioCliente
from documentos.models import DocumentoEvento
from invitaciones.models import EventoBoda
from itinerario.models import ActividadItinerario, ParticipanteActividad
from organizaciones.models import EmpresaSuscriptora, MembresiaEmpresa
from proveedores.models import Proveedor, ServicioEvento
from tareas.models import TareaEvento


class ClientPortalV3Tests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.empresa = EmpresaSuscriptora.objects.create(
            nombre_comercial="Empresa Cliente V3", slug="empresa-cliente-v3"
        )
        self.planner = User.objects.create_user(username="planner-client-v3", password="test123")
        self.cliente = User.objects.create_user(username="cliente-v3", password="test123")
        self.otro_cliente = User.objects.create_user(username="otro-cliente-v3", password="test123")
        self.proveedor_user = User.objects.create_user(username="proveedor-client-v3", password="test123")
        for user, rol in [
            (self.planner, "WEDDING_PLANNER"),
            (self.cliente, "CLIENTE"),
            (self.otro_cliente, "CLIENTE"),
            (self.proveedor_user, "PROVEEDOR"),
        ]:
            MembresiaEmpresa.objects.create(empresa=self.empresa, usuario=user, rol=rol)

        now = timezone.now()
        self.evento = EventoBoda.objects.create(
            empresa=self.empresa,
            wedding_planner=self.planner,
            nombre_evento="Boda Portal V3",
            novio="A", novia="B", frase_portada="Test", mensaje_general="Test",
            fecha_misa=now + timedelta(days=20), lugar_misa="Ceremonia",
            fecha_fiesta=now + timedelta(days=20), lugar_fiesta="Recepción",
        )
        self.evento.clientes.add(self.cliente, self.otro_cliente)
        self.proveedor = Proveedor.objects.create(
            empresa=self.empresa, usuario=self.proveedor_user,
            nombre_comercial="Proveedor Privado", tipo_proveedor="BANQUETE",
        )
        self.servicio = ServicioEvento.objects.create(
            evento=self.evento, proveedor=self.proveedor,
            nombre_servicio="Banquete V3", origen="MANUAL", modalidad="ADICIONAL",
        )
        self.client.force_login(self.cliente)

    def test_portal_es_action_first_y_no_renderiza_legacy(self):
        response = self.client.get(reverse("cliente_dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Lo que necesitas hacer")
        self.assertContains(response, "Servicios del evento")
        self.assertContains(response, "Una tarea es algo que debes hacer antes de una fecha")
        self.assertNotContains(response, "Solicitudes y propuestas")
        self.assertNotContains(response, "Nueva solicitud")

    def test_aprobacion_propuesta_cita_y_tarea_aparecen_como_acciones(self):
        AprobacionServicio.objects.create(
            servicio_evento=self.servicio, titulo="Aprobar menú", solicitado_por=self.planner
        )
        PropuestaServicioCliente.objects.create(
            servicio_evento=self.servicio, version=1, modalidad="UPGRADE",
            descripcion="Upgrade de menú", cargo_adicional_cliente=Decimal("1500"),
            estado="ENVIADA", enviado_por=self.planner, fecha_envio=timezone.now(),
        )
        tarea = TareaEvento.objects.create(
            evento=self.evento, servicio_evento=self.servicio,
            titulo="Enviar lista final", responsable=self.cliente,
            fecha_limite=timezone.localdate() + timedelta(days=2),
        )
        cita = ActividadItinerario.objects.create(
            evento=self.evento, servicio_evento=self.servicio, proveedor=self.proveedor,
            tipo="CITA", titulo="Prueba de menú",
            fecha=timezone.localdate() + timedelta(days=3), hora_inicio=time(16, 0),
        )
        ParticipanteActividad.objects.create(
            actividad=cita, usuario=self.cliente, rol="CLIENTE", estado="PENDIENTE"
        )
        response = self.client.get(reverse("cliente_dashboard"))
        for text in ["Aprobar decisión", "Revisar propuesta", "Confirmar cita", "Tarea pendiente", tarea.titulo]:
            self.assertContains(response, text)

    def test_cita_privada_de_otro_cliente_no_se_muestra(self):
        cita = ActividadItinerario.objects.create(
            evento=self.evento, servicio_evento=self.servicio, proveedor=self.proveedor,
            tipo="CITA", titulo="Cita solo otro cliente",
            fecha=timezone.localdate() + timedelta(days=3), hora_inicio=time(12, 0),
        )
        ParticipanteActividad.objects.create(
            actividad=cita, usuario=self.otro_cliente, rol="CLIENTE", estado="PENDIENTE"
        )
        response = self.client.get(reverse("cliente_dashboard"))
        self.assertNotContains(response, "Cita solo otro cliente")

    def test_portal_no_expone_cotizacion_costo_proveedor_ni_documento_interno(self):
        CotizacionServicio.objects.create(
            servicio_evento=self.servicio, version=1,
            costo_proveedor=Decimal("98765.43"), estado="ENVIADA",
            creado_por=self.proveedor_user,
        )
        DocumentoEvento.objects.create(
            evento=self.evento, servicio_evento=self.servicio,
            titulo="Documento interno secreto", tipo_documento="CONTRATO",
            archivo="documentos/eventos/interno.pdf", visible_cliente=False,
        )
        DocumentoEvento.objects.create(
            evento=self.evento, servicio_evento=self.servicio,
            titulo="Menú visible cliente", tipo_documento="MENU",
            archivo="documentos/eventos/menu.pdf", visible_cliente=True,
        )
        response = self.client.get(reverse("cliente_dashboard"))
        self.assertContains(response, "Menú visible cliente")
        self.assertNotContains(response, "Documento interno secreto")
        self.assertNotContains(response, "98765.43")

        # También protege el workspace al que el cliente entra desde Servicios.
        response = self.client.get(
            reverse("colaboracion_workspace_servicio", args=[self.servicio.id]),
            {"canal": "CLIENTE_PLANNER"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "98765.43")


    def test_actividad_operativa_de_servicio_no_se_expone_automaticamente(self):
        ActividadItinerario.objects.create(
            evento=self.evento, servicio_evento=self.servicio, proveedor=self.proveedor,
            tipo="ACTIVIDAD", titulo="Montaje interno proveedor",
            fecha=timezone.localdate() + timedelta(days=3), hora_inicio=time(8, 0),
        )
        ActividadItinerario.objects.create(
            evento=self.evento, tipo="HITO", titulo="Ceremonia compartida",
            fecha=timezone.localdate() + timedelta(days=3), hora_inicio=time(17, 0),
        )
        response = self.client.get(reverse("cliente_dashboard"))
        self.assertNotContains(response, "Montaje interno proveedor")
        self.assertContains(response, "Ceremonia compartida")


    def test_cita_general_sin_servicio_renderiza_y_se_confirma(self):
        cita = ActividadItinerario.objects.create(
            evento=self.evento,
            tipo="CITA",
            titulo="Reunión general con cliente",
            fecha=timezone.localdate() + timedelta(days=4),
            hora_inicio=time(18, 0),
        )
        participante = ParticipanteActividad.objects.create(
            actividad=cita,
            usuario=self.cliente,
            rol="CLIENTE",
            estado="PENDIENTE",
        )

        response = self.client.get(reverse("cliente_dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Reunión general con cliente")
        self.assertContains(
            response,
            reverse(
                "colaboracion_k8712_cita_evento_responder",
                args=[participante.id],
            ),
        )

        response = self.client.post(
            reverse(
                "colaboracion_k8712_cita_evento_responder",
                args=[participante.id],
            ),
            {"estado": "CONFIRMADO"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("portal_cliente"), response.url)
        participante.refresh_from_db()
        self.assertEqual(participante.estado, "CONFIRMADO")

    def test_cliente_puede_confirmar_su_cita_desde_portal(self):
        cita = ActividadItinerario.objects.create(
            evento=self.evento, servicio_evento=self.servicio, proveedor=self.proveedor,
            tipo="CITA", titulo="Confirmación cliente",
            fecha=timezone.localdate() + timedelta(days=3), hora_inicio=time(10, 0),
        )
        participante = ParticipanteActividad.objects.create(
            actividad=cita, usuario=self.cliente, rol="CLIENTE", estado="PENDIENTE"
        )
        response = self.client.post(
            reverse("colaboracion_k8712_cita_responder", args=[self.servicio.id, participante.id]),
            {"estado": "CONFIRMADO"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("portal_cliente"), response.url)
        participante.refresh_from_db()
        self.assertEqual(participante.estado, "CONFIRMADO")
