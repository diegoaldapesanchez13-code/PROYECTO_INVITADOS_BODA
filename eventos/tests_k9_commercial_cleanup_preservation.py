from django.test import TestCase
from django.urls import reverse

from catalogo.models import ServicioCatalogo
from invitaciones.models import AssetInvitacion, DisenoInvitacion, EventoBoda, Grupoinvitacion, Invitado
from organizaciones.models import EmpresaSuscriptora
from paquetes.models import PaqueteBoda, PaqueteServicio
from proveedores.models import ServicioEvento


class CommercialCleanupPreservationTests(TestCase):
    """La limpieza comercial nunca puede tocar la experiencia de invitacion."""

    def setUp(self):
        self.empresa = EmpresaSuscriptora.objects.create(
            nombre_comercial="Empresa preservacion K9",
            slug="empresa-preservacion-k9",
        )
        self.evento = EventoBoda.objects.create(
            empresa=self.empresa,
            nombre_evento="Evento protegido",
        )
        self.grupo = Grupoinvitacion.objects.create(
            evento=self.evento,
            nombre_grupo="Familia protegida",
            tipo="FAMILIAR",
            cantidad_maxima=2,
        )
        self.invitado = Invitado.objects.create(
            grupo=self.grupo,
            nombre="Invitado protegido",
            orden=1,
        )
        document = {
            "schemaVersion": 3,
            "page": {"name": "Invitacion protegida"},
            "sections": [],
            "nodes": [],
        }
        self.diseno = DisenoInvitacion.objects.create(
            evento=self.evento,
            nombre="Diseño protegido",
            estado="PUBLICADO",
            documento_builder_borrador=document,
            documento_builder_publicado=document,
        )
        self.asset = AssetInvitacion.objects.create(
            evento=self.evento,
            tipo="PORTADA",
            titulo="Asset protegido",
            archivo="editor_invitaciones/assets/protegido.png",
        )

        self.catalogo = ServicioCatalogo.objects.create(
            empresa=self.empresa,
            nombre="Servicio descartable",
            categoria="OTRO",
            unidad="EVENTO",
        )
        self.paquete = PaqueteBoda.objects.create(
            empresa=self.empresa,
            nombre="Paquete descartable",
            precio_base=1000,
        )
        PaqueteServicio.objects.create(
            paquete=self.paquete,
            servicio_catalogo=self.catalogo,
            cantidad=1,
        )
        self.servicio_evento = ServicioEvento.objects.create(
            evento=self.evento,
            servicio_catalogo_k9=self.catalogo,
            origen="CATALOGO",
            modalidad="ADICIONAL",
            nombre_servicio="Servicio operativo descartable",
        )

    def test_discarding_commercial_records_preserves_public_invitation(self):
        ids = {
            "evento": self.evento.pk,
            "grupo": self.grupo.pk,
            "codigo": self.grupo.codigo,
            "invitado": self.invitado.pk,
            "diseno": self.diseno.pk,
            "asset": self.asset.pk,
        }

        self.servicio_evento.delete()
        self.paquete.delete()
        self.catalogo.delete()

        self.assertTrue(EventoBoda.objects.filter(pk=ids["evento"]).exists())
        self.assertTrue(Grupoinvitacion.objects.filter(pk=ids["grupo"], codigo=ids["codigo"]).exists())
        self.assertTrue(Invitado.objects.filter(pk=ids["invitado"], grupo_id=ids["grupo"]).exists())
        self.assertTrue(DisenoInvitacion.objects.filter(pk=ids["diseno"], evento_id=ids["evento"]).exists())
        self.assertTrue(AssetInvitacion.objects.filter(pk=ids["asset"], evento_id=ids["evento"]).exists())

        response = self.client.get(reverse("ver_invitacion", args=[ids["codigo"]]))
        self.assertEqual(response.status_code, 200)
