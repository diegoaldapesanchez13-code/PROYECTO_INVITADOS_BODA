from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from invitaciones.models import EventoBoda
from organizaciones.models import EmpresaSuscriptora, MembresiaEmpresa
from proveedores.models import Proveedor, ServicioEvento

from .models import (
    AdjuntoMensajeServicio,
    ConversacionServicio,
    DecisionServicio,
    MensajeServicio,
    ReferenciaServicio,
    TemaServicio,
)


@override_settings(MEDIA_ROOT="media/test/dirtec_k877_test_media")
class CollaborationUXK877Tests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.empresa = EmpresaSuscriptora.objects.create(
            nombre_comercial="Empresa K877",
            slug="empresa-k877",
        )
        self.planner = User.objects.create_user(username="planner-k877", password="test123")
        self.cliente = User.objects.create_user(username="cliente-k877", password="test123")
        self.proveedor_user = User.objects.create_user(username="proveedor-k877", password="test123")
        for user, rol in [
            (self.planner, "WEDDING_PLANNER"),
            (self.cliente, "CLIENTE"),
            (self.proveedor_user, "PROVEEDOR"),
        ]:
            MembresiaEmpresa.objects.create(empresa=self.empresa, usuario=user, rol=rol)

        now = timezone.now()
        self.evento = EventoBoda.objects.create(
            empresa=self.empresa,
            wedding_planner=self.planner,
            nombre_evento="Boda K877",
            novio="A", novia="B",
            frase_portada="Test", mensaje_general="Test",
            fecha_misa=now, lugar_misa="Ceremonia",
            fecha_fiesta=now, lugar_fiesta="Recepción",
        )
        self.evento.clientes.add(self.cliente)
        self.proveedor = Proveedor.objects.create(
            empresa=self.empresa,
            usuario=self.proveedor_user,
            nombre_comercial="Proveedor K877",
            tipo_proveedor="DECORACION",
        )
        self.servicio = ServicioEvento.objects.create(
            evento=self.evento,
            proveedor=self.proveedor,
            nombre_servicio="Decoración K877",
            origen="MANUAL",
        )
        self.conv_cliente = ConversacionServicio.objects.create(
            servicio_evento=self.servicio,
            canal="CLIENTE_PLANNER",
            creada_por=self.planner,
        )
        self.conv_proveedor = ConversacionServicio.objects.create(
            servicio_evento=self.servicio,
            canal="PLANNER_PROVEEDOR",
            creada_por=self.planner,
        )

    def test_planner_ve_herramientas_de_limpieza(self):
        MensajeServicio.objects.create(
            conversacion=self.conv_cliente,
            autor=self.cliente,
            texto="Mensaje para habilitar limpieza",
        )
        self.client.force_login(self.planner)
        response = self.client.get(
            reverse("colaboracion_workspace_servicio", args=[self.servicio.id]),
            {"canal": "CLIENTE_PLANNER"},
        )
        self.assertContains(response, "Herramientas del Planner")
        self.assertContains(response, "Vaciar historial de este canal")
        self.assertContains(response, "Referencias")
        self.assertContains(response, "1 mensaje")

    def test_planner_no_muestra_vaciar_historial_si_canal_esta_vacio(self):
        self.client.force_login(self.planner)
        response = self.client.get(
            reverse("colaboracion_workspace_servicio", args=[self.servicio.id]),
            {"canal": "CLIENTE_PLANNER"},
        )
        self.assertContains(response, "Herramientas del Planner")
        self.assertContains(response, "0 mensajes")
        self.assertNotContains(response, "Vaciar historial de este canal")

    def test_cliente_no_ve_herramientas_destructivas(self):
        self.client.force_login(self.cliente)
        response = self.client.get(
            reverse("colaboracion_workspace_servicio", args=[self.servicio.id]),
            {"canal": "CLIENTE_PLANNER"},
        )
        self.assertNotContains(response, "Herramientas del Planner")
        self.assertNotContains(response, "Vaciar historial de este canal")
        self.assertNotContains(response, "Eliminar referencia")

    def test_planner_elimina_mensaje_individual(self):
        mensaje = MensajeServicio.objects.create(
            conversacion=self.conv_cliente,
            autor=self.cliente,
            texto="Mensaje a corregir",
        )
        self.client.force_login(self.planner)
        response = self.client.post(
            reverse("colaboracion_workspace_eliminar_mensaje", args=[mensaje.id])
        )
        self.assertEqual(response.status_code, 302)
        self.assertFalse(MensajeServicio.objects.filter(pk=mensaje.pk).exists())

    def test_cliente_no_puede_eliminar_mensaje_completo(self):
        mensaje = MensajeServicio.objects.create(
            conversacion=self.conv_cliente,
            autor=self.cliente,
            texto="Mi mensaje",
        )
        self.client.force_login(self.cliente)
        response = self.client.post(
            reverse("colaboracion_workspace_eliminar_mensaje", args=[mensaje.id])
        )
        self.assertEqual(response.status_code, 403)
        self.assertTrue(MensajeServicio.objects.filter(pk=mensaje.pk).exists())

    def test_mensaje_con_referencia_exige_retirarla_primero(self):
        mensaje = MensajeServicio.objects.create(
            conversacion=self.conv_cliente,
            autor=self.cliente,
            texto="Referencia",
        )
        adjunto = AdjuntoMensajeServicio.objects.create(
            mensaje=mensaje,
            archivo=SimpleUploadedFile("ref.pdf", b"%PDF-1.4", content_type="application/pdf"),
            nombre_original="ref.pdf",
        )
        referencia = ReferenciaServicio.objects.create(
            servicio_evento=self.servicio,
            mensaje_origen=mensaje,
            adjunto_origen=adjunto,
            titulo="Referencia protegida",
            creado_por=self.planner,
        )

        self.client.force_login(self.planner)
        response = self.client.post(
            reverse("colaboracion_workspace_eliminar_mensaje", args=[mensaje.id]),
            follow=True,
        )
        self.assertTrue(MensajeServicio.objects.filter(pk=mensaje.pk).exists())
        self.assertContains(response, "Elimina primero esas referencias")

        response = self.client.post(
            reverse("colaboracion_workspace_eliminar_referencia", args=[referencia.id])
        )
        self.assertEqual(response.status_code, 302)
        self.assertFalse(ReferenciaServicio.objects.filter(pk=referencia.pk).exists())

        response = self.client.post(
            reverse("colaboracion_workspace_eliminar_mensaje", args=[mensaje.id])
        )
        self.assertEqual(response.status_code, 302)
        self.assertFalse(MensajeServicio.objects.filter(pk=mensaje.pk).exists())

    def test_limpiar_historial_afecta_solo_canal_actual_y_conserva_decision(self):
        msg_cliente = MensajeServicio.objects.create(
            conversacion=self.conv_cliente,
            autor=self.cliente,
            texto="Cliente chat",
        )
        adjunto = AdjuntoMensajeServicio.objects.create(
            mensaje=msg_cliente,
            archivo=SimpleUploadedFile("idea.pdf", b"%PDF-1.4", content_type="application/pdf"),
            nombre_original="idea.pdf",
        )
        ReferenciaServicio.objects.create(
            servicio_evento=self.servicio,
            mensaje_origen=msg_cliente,
            adjunto_origen=adjunto,
            titulo="Idea cliente",
            creado_por=self.planner,
        )
        decision = DecisionServicio.objects.create(
            servicio_evento=self.servicio,
            mensaje_origen=msg_cliente,
            titulo="Decisión conservada",
            registrado_por=self.planner,
        )
        msg_proveedor = MensajeServicio.objects.create(
            conversacion=self.conv_proveedor,
            autor=self.proveedor_user,
            texto="Proveedor chat",
        )

        self.client.force_login(self.planner)
        response = self.client.post(
            reverse("colaboracion_workspace_limpiar_historial", args=[self.servicio.id]),
            {"canal": "CLIENTE_PLANNER"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertFalse(self.conv_cliente.mensajes.exists())
        self.assertTrue(MensajeServicio.objects.filter(pk=msg_proveedor.pk).exists())
        self.assertFalse(
            ReferenciaServicio.objects.filter(servicio_evento=self.servicio).exists()
        )
        decision.refresh_from_db()
        self.assertEqual(decision.titulo, "Decisión conservada")
        self.assertIsNone(decision.mensaje_origen)

    def test_cliente_no_puede_vaciar_historial(self):
        MensajeServicio.objects.create(
            conversacion=self.conv_cliente,
            autor=self.cliente,
            texto="No borrar",
        )
        self.client.force_login(self.cliente)
        response = self.client.post(
            reverse("colaboracion_workspace_limpiar_historial", args=[self.servicio.id]),
            {"canal": "CLIENTE_PLANNER"},
        )
        self.assertEqual(response.status_code, 403)
        self.assertTrue(self.conv_cliente.mensajes.exists())

    def test_planner_archiva_tema_sin_borrar_mensajes(self):
        tema = TemaServicio.objects.create(
            servicio_evento=self.servicio,
            nombre="Flores",
            creado_por=self.planner,
        )
        mensaje = MensajeServicio.objects.create(
            conversacion=self.conv_cliente,
            tema=tema,
            autor=self.cliente,
            texto="Sobre flores",
        )
        self.client.force_login(self.planner)
        response = self.client.post(
            reverse("colaboracion_workspace_archivar_tema", args=[tema.id]),
            {"canal": "CLIENTE_PLANNER"},
        )
        self.assertEqual(response.status_code, 302)
        tema.refresh_from_db()
        self.assertFalse(tema.activo)
        self.assertTrue(MensajeServicio.objects.filter(pk=mensaje.pk).exists())
