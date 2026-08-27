from pathlib import Path

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from eventos.workspace_commercial import aceptar_propuesta
from invitaciones.models import EventoBoda
from organizaciones.models import EmpresaSuscriptora, MembresiaEmpresa
from paquetes.models import PaqueteBoda, PropuestaEvento


class D72BSmokeRuntimeTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.empresa = EmpresaSuscriptora.objects.create(
            nombre_comercial="Empresa D72B",
            slug="empresa-d72b",
        )
        self.admin = User.objects.create_user(
            username="admin-d72b",
            password="test12345",
        )
        MembresiaEmpresa.objects.create(
            empresa=self.empresa,
            usuario=self.admin,
            rol="ADMIN_EMPRESA",
            activo=True,
        )
        now = timezone.now()
        self.evento = EventoBoda.objects.create(
            empresa=self.empresa,
            nombre_evento="Evento D72B",
            novio="A",
            novia="B",
            frase_portada="D72B",
            mensaje_general="D72B",
            fecha_misa=now,
            lugar_misa="X",
            fecha_fiesta=now,
            lugar_fiesta="Y",
        )
        self.paquete = PaqueteBoda.objects.create(
            empresa=self.empresa,
            nombre="Paquete D72B",
            precio_base=1000,
        )
        self.propuesta = PropuestaEvento.objects.create(
            empresa=self.empresa,
            evento=self.evento,
            paquete=self.paquete,
            estado="BORRADOR",
        )
        self.client.force_login(self.admin)

    def test_server_accept_action_creates_snapshot(self):
        response = self.client.post(
            reverse(
                "k9_evento_comercial",
                kwargs={
                    "empresa_slug": self.empresa.slug,
                    "evento_id": self.evento.id,
                },
            ),
            {
                "accion": "aceptar_propuesta",
                "propuesta_id": self.propuesta.id,
            },
        )
        self.assertEqual(response.status_code, 302)
        self.propuesta.refresh_from_db()
        self.assertEqual(self.propuesta.estado, "ACEPTADO")
        self.assertTrue(self.propuesta.snapshot_aceptacion)

    def test_workspace_runtime_preserves_submitter_action(self):
        runtime = (
            Path(__file__).resolve().parent
            / "static"
            / "eventos"
            / "js"
            / "workspace_runtime.js"
        ).read_text(encoding="utf-8")
        self.assertIn("const submitter = event.submitter;", runtime)
        self.assertIn("data.set(submitter.name, submitter.value", runtime)

    def test_config_zip_links_use_native_navigation(self):
        template = (
            Path(__file__).resolve().parent
            / "templates"
            / "eventos"
            / "workspace"
            / "configuracion.html"
        ).read_text(encoding="utf-8")
        self.assertIn("k9_evento_exportar_expediente", template)
        self.assertIn("k9_evento_exportar_expediente_purge_ready", template)

        # Both binary endpoints must bypass workspace AJAX navigation.
        self.assertGreaterEqual(template.count("data-workspace-native"), 2)
