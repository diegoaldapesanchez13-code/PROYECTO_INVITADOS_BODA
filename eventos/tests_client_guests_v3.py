from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from invitaciones.models import EventoBoda, Grupoinvitacion, Invitado
from organizaciones.models import EmpresaSuscriptora, MembresiaEmpresa


class ClientGuestsV3Tests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.empresa = EmpresaSuscriptora.objects.create(
            nombre_comercial="Empresa Guests V3",
            slug="empresa-guests-v3",
        )
        self.cliente = User.objects.create_user(username="cliente-guests-v3", password="test123")
        self.otro_cliente = User.objects.create_user(username="otro-cliente-guests-v3", password="test123")
        self.planner = User.objects.create_user(username="planner-guests-v3", password="test123")
        for user, rol in [
            (self.cliente, "CLIENTE"),
            (self.otro_cliente, "CLIENTE"),
            (self.planner, "WEDDING_PLANNER"),
        ]:
            MembresiaEmpresa.objects.create(empresa=self.empresa, usuario=user, rol=rol)
        now = timezone.now()
        self.evento = EventoBoda.objects.create(
            empresa=self.empresa,
            wedding_planner=self.planner,
            nombre_evento="Boda Guests V3",
            novio="A", novia="B",
            frase_portada="Test", mensaje_general="Test",
            fecha_misa=now + timedelta(days=20), lugar_misa="Ceremonia",
            fecha_fiesta=now + timedelta(days=20), lugar_fiesta="Recepción",
            capacidad_contratada=5,
        )
        self.evento.clientes.add(self.cliente)
        self.otro_evento = EventoBoda.objects.create(
            empresa=self.empresa,
            wedding_planner=self.planner,
            nombre_evento="Otro evento",
            novio="C", novia="D",
            frase_portada="Test", mensaje_general="Test",
            fecha_misa=now + timedelta(days=30), lugar_misa="Ceremonia",
            fecha_fiesta=now + timedelta(days=30), lugar_fiesta="Recepción",
            capacidad_contratada=10,
        )
        self.otro_evento.clientes.add(self.otro_cliente)
        self.client.force_login(self.cliente)

    def test_cliente_crea_invitacion_personal(self):
        response = self.client.post(
            reverse("cliente_grupo_crear", args=[self.evento.id]),
            {
                "nombre_grupo": "Diego Invitado",
                "tipo_grupo": "PERSONAL",
                "telefono_contacto": "4771234567",
            },
        )
        self.assertEqual(response.status_code, 302)
        grupo = Grupoinvitacion.objects.get(evento=self.evento)
        self.assertTrue(grupo.es_personal)
        self.assertEqual(grupo.invitados.count(), 1)
        self.assertEqual(grupo.invitados.first().nombre, "Diego Invitado")

    def test_cliente_crea_familia_con_personas(self):
        self.client.post(
            reverse("cliente_grupo_crear", args=[self.evento.id]),
            {
                "nombre_grupo": "Familia Flores",
                "tipo_grupo": "FAMILIAR",
                "integrantes": "María Flores\nJuan Flores",
                "permitir_acompanantes_extra": "on",
                "cantidad_extra_permitida": "1",
            },
        )
        grupo = Grupoinvitacion.objects.get(evento=self.evento)
        self.assertEqual(grupo.invitados.filter(es_acompanante_extra=False).count(), 2)
        self.assertEqual(grupo.invitados.filter(es_acompanante_extra=True).count(), 1)

    def test_capacidad_contratada_impide_exceder_lugares(self):
        self.client.post(
            reverse("cliente_grupo_crear", args=[self.evento.id]),
            {
                "nombre_grupo": "Familia Uno",
                "tipo_grupo": "FAMILIAR",
                "integrantes": "A\nB\nC\nD",
            },
        )
        response = self.client.post(
            reverse("cliente_grupo_crear", args=[self.evento.id]),
            {
                "nombre_grupo": "Familia Dos",
                "tipo_grupo": "FAMILIAR",
                "integrantes": "E\nF",
            },
            follow=True,
        )
        self.assertEqual(Grupoinvitacion.objects.filter(evento=self.evento).count(), 1)
        self.assertContains(response, "capacidad contratada")

    def test_cliente_no_puede_gestionar_invitados_de_otro_evento(self):
        grupo = Grupoinvitacion.objects.create(
            evento=self.otro_evento,
            nombre_grupo="Ajeno",
            tipo="PERSONAL",
        )
        response = self.client.post(
            reverse("cliente_grupo_editar", args=[grupo.id]),
            {"nombre_grupo": "Hack"},
        )
        self.assertEqual(response.status_code, 403)
        grupo.refresh_from_db()
        self.assertEqual(grupo.nombre_grupo, "Ajeno")

    def test_portal_muestra_enlace_uuid_y_whatsapp(self):
        grupo = Grupoinvitacion.objects.create(
            evento=self.evento,
            nombre_grupo="Familia Share",
            tipo="PERSONAL",
            telefono_contacto="4771234567",
        )
        Invitado.objects.create(grupo=grupo, nombre="Familia Share")
        response = self.client.get(reverse("cliente_dashboard"), {"evento": self.evento.id})
        self.assertContains(response, str(grupo.codigo))
        self.assertContains(response, "Copiar enlace")
        self.assertContains(response, "WhatsApp")
        self.assertContains(response, "Ver invitación")

    def test_cliente_agrega_persona_a_familia(self):
        grupo = Grupoinvitacion.objects.create(
            evento=self.evento,
            nombre_grupo="Familia X",
            tipo="FAMILIAR",
        )
        Invitado.objects.create(grupo=grupo, nombre="Persona 1")
        response = self.client.post(
            reverse("cliente_invitado_agregar", args=[grupo.id]),
            {"nombre": "Persona 2", "tipo_persona": "ADULTO"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(grupo.invitados.filter(nombre="Persona 2").exists())

    def test_no_elimina_persona_con_rsvp(self):
        grupo = Grupoinvitacion.objects.create(
            evento=self.evento,
            nombre_grupo="Familia RSVP",
            tipo="FAMILIAR",
        )
        invitado = Invitado.objects.create(grupo=grupo, nombre="Confirmado", asistira=True)
        response = self.client.post(
            reverse("cliente_invitado_eliminar", args=[invitado.id]),
            follow=True,
        )
        self.assertTrue(Invitado.objects.filter(pk=invitado.pk).exists())
        self.assertContains(response, "ya respondió RSVP")

    def test_portal_no_ofrece_builder_desde_gestion_invitados(self):
        response = self.client.get(reverse("cliente_dashboard"), {"evento": self.evento.id})
        self.assertContains(response, "Gestiona tus invitaciones")
        self.assertContains(response, "Mi invitación")
        self.assertNotContains(response, "Editar en Builder")
