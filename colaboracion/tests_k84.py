from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from invitaciones.models import EventoBoda
from eventos.models import ContratoEvento
from organizaciones.models import EmpresaSuscriptora, MembresiaEmpresa
from proveedores.models import Proveedor, ServicioEvento

from .models import (
    AdjuntoMensajeServicio,
    ConversacionServicio,
    MensajeServicio,
    ReferenciaServicio,
    TemaServicio,
)


@override_settings(MEDIA_ROOT="media/test/dirtec_k84_test_media")
class ServiceWorkspaceK84Tests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.empresa = EmpresaSuscriptora.objects.create(
            nombre_comercial="Empresa K84",
            slug="empresa-k84",
        )
        self.planner = User.objects.create_user(username="planner-k84", password="test123")
        self.cliente = User.objects.create_user(username="cliente-k84", password="test123")
        self.proveedor_user = User.objects.create_user(username="proveedor-k84", password="test123")
        self.otro_cliente = User.objects.create_user(username="otro-cliente-k84", password="test123")
        for user, rol in [
            (self.planner, "WEDDING_PLANNER"),
            (self.cliente, "CLIENTE"),
            (self.proveedor_user, "PROVEEDOR"),
            (self.otro_cliente, "CLIENTE"),
        ]:
            MembresiaEmpresa.objects.create(empresa=self.empresa, usuario=user, rol=rol)

        now = timezone.now()
        self.evento = EventoBoda.objects.create(
            empresa=self.empresa,
            wedding_planner=self.planner,
            nombre_evento="Boda K84",
            novio="A",
            novia="B",
            frase_portada="Test",
            mensaje_general="Test",
            fecha_misa=now,
            lugar_misa="Ceremonia",
            fecha_fiesta=now,
            lugar_fiesta="Recepcion",
        )
        self.evento.clientes.add(self.cliente)
        self.proveedor = Proveedor.objects.create(
            empresa=self.empresa,
            usuario=self.proveedor_user,
            nombre_comercial="Proveedor K84",
            tipo_proveedor="DECORACION",
        )
        self.servicio = ServicioEvento.objects.create(
            evento=self.evento,
            proveedor=self.proveedor,
            nombre_servicio="Decoracion",
            origen="MANUAL",
            modalidad="ADICIONAL",
        )

    def _workspace(self, canal=None):
        url = reverse("colaboracion_workspace_servicio", args=[self.servicio.id])
        return f"{url}?canal={canal}" if canal else url

    def test_planner_ve_los_tres_canales(self):
        self.client.force_login(self.planner)
        response = self.client.get(self._workspace())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Cliente ↔ Planner")
        self.assertContains(response, "Planner ↔ Proveedor")
        self.assertContains(response, "Notas internas")

    def test_cliente_solo_ve_canal_cliente_planner(self):
        self.client.force_login(self.cliente)
        response = self.client.get(self._workspace("CLIENTE_PLANNER"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Cliente ↔ Planner")
        self.assertNotContains(response, "Planner ↔ Proveedor")
        self.assertNotContains(response, "Notas internas")

    def test_proveedor_solo_ve_su_canal(self):
        self.client.force_login(self.proveedor_user)
        response = self.client.get(self._workspace("PLANNER_PROVEEDOR"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Planner ↔ Proveedor")
        self.assertNotContains(response, "Cliente ↔ Planner")
        self.assertNotContains(response, "Notas internas")

    def test_usuario_ajeno_no_puede_entrar(self):
        self.client.force_login(self.otro_cliente)
        response = self.client.get(self._workspace())
        self.assertEqual(response.status_code, 403)

    def test_cliente_no_puede_escribir_canal_proveedor(self):
        self.client.force_login(self.cliente)
        response = self.client.post(
            reverse("colaboracion_workspace_enviar_mensaje", args=[self.servicio.id]),
            {"canal": "PLANNER_PROVEEDOR", "texto": "No debo entrar"},
        )
        self.assertEqual(response.status_code, 403)
        self.assertFalse(MensajeServicio.objects.exists())

    def test_tema_mensaje_y_multiples_adjuntos(self):
        self.client.force_login(self.planner)
        response = self.client.post(
            reverse("colaboracion_workspace_crear_tema", args=[self.servicio.id]),
            {"nombre": "Centro de mesa", "canal": "CLIENTE_PLANNER"},
        )
        self.assertEqual(response.status_code, 302)
        tema = TemaServicio.objects.get(servicio_evento=self.servicio)

        archivo1 = SimpleUploadedFile("ref1.pdf", b"%PDF-1.4 test", content_type="application/pdf")
        archivo2 = SimpleUploadedFile("ref2.pdf", b"%PDF-1.4 test2", content_type="application/pdf")
        response = self.client.post(
            reverse("colaboracion_workspace_enviar_mensaje", args=[self.servicio.id]),
            {
                "canal": "CLIENTE_PLANNER",
                "tema_id": str(tema.id),
                "texto": "Estas son las referencias.",
                "archivos": [archivo1, archivo2],
            },
        )
        self.assertEqual(response.status_code, 302)
        mensaje = MensajeServicio.objects.get()
        self.assertEqual(mensaje.tema, tema)
        self.assertEqual(mensaje.adjuntos.count(), 2)
        self.assertEqual(ConversacionServicio.objects.count(), 1)

    def test_planner_puede_promover_adjunto_a_referencia(self):
        conversacion = ConversacionServicio.objects.create(
            servicio_evento=self.servicio,
            canal="CLIENTE_PLANNER",
            creada_por=self.planner,
        )
        mensaje = MensajeServicio.objects.create(
            conversacion=conversacion,
            autor=self.cliente,
            texto="Me gusta esta idea",
        )
        adjunto = AdjuntoMensajeServicio.objects.create(
            mensaje=mensaje,
            archivo=SimpleUploadedFile("idea.pdf", b"%PDF-1.4 idea", content_type="application/pdf"),
            nombre_original="idea.pdf",
        )
        self.client.force_login(self.planner)
        response = self.client.post(
            reverse("colaboracion_workspace_guardar_referencia", args=[adjunto.id]),
            {"tipo": "INSPIRACION", "titulo": "Centro de mesa referencia"},
        )
        self.assertEqual(response.status_code, 302)
        referencia = ReferenciaServicio.objects.get()
        self.assertEqual(referencia.servicio_evento, self.servicio)
        self.assertEqual(referencia.adjunto_origen, adjunto)
        self.assertEqual(referencia.tipo, "INSPIRACION")

    def test_cliente_portal_muestra_servicio_workspace_sin_expediente_legacy(self):
        self.client.force_login(self.cliente)
        response = self.client.get(reverse("portal_cliente"))
        self.assertEqual(response.status_code, 200)
        workspace_url = reverse("colaboracion_workspace_servicio", args=[self.servicio.id])
        self.assertContains(response, f"{workspace_url}?canal=CLIENTE_PLANNER")
        self.assertContains(response, "Decoracion")

    def test_autor_puede_eliminar_su_adjunto(self):
        conversacion = ConversacionServicio.objects.create(
            servicio_evento=self.servicio,
            canal="CLIENTE_PLANNER",
            creada_por=self.cliente,
        )
        mensaje = MensajeServicio.objects.create(
            conversacion=conversacion,
            autor=self.cliente,
            texto="Archivo equivocado",
        )
        adjunto = AdjuntoMensajeServicio.objects.create(
            mensaje=mensaje,
            archivo=SimpleUploadedFile("equivocado.pdf", b"%PDF-1.4", content_type="application/pdf"),
            nombre_original="equivocado.pdf",
            tipo_mime="application/pdf",
        )
        self.client.force_login(self.cliente)
        response = self.client.post(
            reverse("colaboracion_workspace_eliminar_adjunto", args=[adjunto.id])
        )
        self.assertEqual(response.status_code, 302)
        self.assertFalse(AdjuntoMensajeServicio.objects.filter(id=adjunto.id).exists())
        self.assertTrue(MensajeServicio.objects.filter(id=mensaje.id).exists())

    def test_usuario_no_autor_no_puede_eliminar_adjunto(self):
        conversacion = ConversacionServicio.objects.create(
            servicio_evento=self.servicio,
            canal="CLIENTE_PLANNER",
            creada_por=self.planner,
        )
        mensaje = MensajeServicio.objects.create(
            conversacion=conversacion,
            autor=self.planner,
            texto="Documento",
        )
        adjunto = AdjuntoMensajeServicio.objects.create(
            mensaje=mensaje,
            archivo=SimpleUploadedFile("doc.pdf", b"%PDF-1.4", content_type="application/pdf"),
            nombre_original="doc.pdf",
            tipo_mime="application/pdf",
        )
        self.client.force_login(self.cliente)
        response = self.client.post(
            reverse("colaboracion_workspace_eliminar_adjunto", args=[adjunto.id])
        )
        self.assertEqual(response.status_code, 403)
        self.assertTrue(AdjuntoMensajeServicio.objects.filter(id=adjunto.id).exists())

    def test_no_se_elimina_adjunto_promovido_a_referencia(self):
        conversacion = ConversacionServicio.objects.create(
            servicio_evento=self.servicio,
            canal="CLIENTE_PLANNER",
            creada_por=self.planner,
        )
        mensaje = MensajeServicio.objects.create(
            conversacion=conversacion,
            autor=self.planner,
            texto="Referencia",
        )
        adjunto = AdjuntoMensajeServicio.objects.create(
            mensaje=mensaje,
            archivo=SimpleUploadedFile("ref.pdf", b"%PDF-1.4", content_type="application/pdf"),
            nombre_original="ref.pdf",
            tipo_mime="application/pdf",
        )
        ReferenciaServicio.objects.create(
            servicio_evento=self.servicio,
            mensaje_origen=mensaje,
            adjunto_origen=adjunto,
            titulo="Referencia protegida",
            creado_por=self.planner,
        )
        self.client.force_login(self.planner)
        response = self.client.post(
            reverse("colaboracion_workspace_eliminar_adjunto", args=[adjunto.id]),
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(AdjuntoMensajeServicio.objects.filter(id=adjunto.id).exists())
        self.assertContains(response, "ya fue guardado como referencia")

    def test_workspace_renderiza_miniatura_para_imagen(self):
        conversacion = ConversacionServicio.objects.create(
            servicio_evento=self.servicio,
            canal="CLIENTE_PLANNER",
            creada_por=self.cliente,
        )
        mensaje = MensajeServicio.objects.create(
            conversacion=conversacion,
            autor=self.cliente,
            texto="Imagen",
        )
        AdjuntoMensajeServicio.objects.create(
            mensaje=mensaje,
            archivo=SimpleUploadedFile("foto.jpg", b"fake-jpg", content_type="image/jpeg"),
            nombre_original="foto.jpg",
            tipo_mime="image/jpeg",
        )
        self.client.force_login(self.cliente)
        response = self.client.get(self._workspace("CLIENTE_PLANNER"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "ws-attachment-preview")
        self.assertContains(response, "<img", html=False)

    def test_cliente_no_ve_referencia_del_canal_proveedor(self):
        conversacion = ConversacionServicio.objects.create(
            servicio_evento=self.servicio,
            canal="PLANNER_PROVEEDOR",
            creada_por=self.planner,
        )
        mensaje = MensajeServicio.objects.create(
            conversacion=conversacion,
            autor=self.proveedor_user,
            texto="Referencia privada proveedor",
        )
        adjunto = AdjuntoMensajeServicio.objects.create(
            mensaje=mensaje,
            archivo=SimpleUploadedFile("privado.pdf", b"%PDF-1.4", content_type="application/pdf"),
            nombre_original="privado.pdf",
            tipo_mime="application/pdf",
        )
        ReferenciaServicio.objects.create(
            servicio_evento=self.servicio,
            mensaje_origen=mensaje,
            adjunto_origen=adjunto,
            titulo="Referencia solo proveedor",
            creado_por=self.planner,
        )
        self.client.force_login(self.cliente)
        response = self.client.get(self._workspace("CLIENTE_PLANNER"))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Referencia solo proveedor")
        self.assertNotContains(response, "privado.pdf")


    def test_k85_decision_directa_al_servicio(self):
        from .models import DecisionServicio
        self.client.force_login(self.planner)
        response = self.client.post(
            reverse("colaboracion_k85_decision_crear", args=[self.servicio.id]),
            {"titulo": "Flores blancas aprobadas", "descripcion": "Usar referencia final."},
        )
        self.assertEqual(response.status_code, 302)
        decision = DecisionServicio.objects.get()
        self.assertEqual(decision.servicio_evento, self.servicio)
        self.assertEqual(decision.titulo, "Flores blancas aprobadas")

    def test_k85_cotizacion_versionada_y_aceptacion_actualiza_costo(self):
        from .models import CotizacionServicio
        self.client.force_login(self.proveedor_user)
        response = self.client.post(
            reverse("colaboracion_k85_cotizacion_crear", args=[self.servicio.id]),
            {"costo_proveedor": "12500.00", "descripcion": "Primera cotizacion"},
        )
        self.assertEqual(response.status_code, 302)
        c1 = CotizacionServicio.objects.get(version=1)
        self.client.force_login(self.planner)
        response = self.client.post(reverse("colaboracion_k85_cotizacion_decidir", args=[c1.id]), {"estado": "ACEPTADA"})
        self.assertEqual(response.status_code, 302)
        self.servicio.refresh_from_db()
        self.assertEqual(str(self.servicio.costo_proveedor), "12500.00")

    def test_k85_propuesta_cliente_aprobada_actualiza_cargo(self):
        from .models import PropuestaServicioCliente
        ContratoEvento.objects.create(
            evento=self.evento,
            version=1,
            estado="CONTRATADO",
            monto_base=0,
            snapshot_version=2,
            snapshot_comercial={
                "version": 2,
                "totales": {"total_final": "0.00"},
            },
        )
        self.client.force_login(self.planner)
        response = self.client.post(
            reverse("colaboracion_k85_propuesta_crear", args=[self.servicio.id]),
            {"modalidad": "UPGRADE", "cargo_adicional_cliente": "4500.00", "descripcion": "Upgrade decoracion"},
        )
        self.assertEqual(response.status_code, 302)
        propuesta = PropuestaServicioCliente.objects.get()
        self.client.force_login(self.cliente)
        response = self.client.post(reverse("colaboracion_k85_propuesta_responder", args=[propuesta.id]), {"estado": "APROBADA"})
        self.assertEqual(response.status_code, 302)
        self.servicio.refresh_from_db()
        self.assertEqual(self.servicio.modalidad, "UPGRADE")
        self.assertEqual(str(self.servicio.cargo_adicional_cliente), "4500.00")

    def test_k85_proveedor_no_puede_ver_responder_aprobacion_cliente(self):
        from .models import AprobacionServicio
        aprobacion = AprobacionServicio.objects.create(servicio_evento=self.servicio, titulo="Aprobar montaje", solicitado_por=self.planner)
        self.client.force_login(self.proveedor_user)
        response = self.client.post(reverse("colaboracion_k85_aprobacion_responder", args=[aprobacion.id]), {"estado": "APROBADA"})
        self.assertEqual(response.status_code, 403)
        aprobacion.refresh_from_db()
        self.assertEqual(aprobacion.estado, "PENDIENTE")
