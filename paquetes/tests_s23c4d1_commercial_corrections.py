from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from catalogo.models import ServicioCatalogo
from invitaciones.models import EventoBoda
from organizaciones.models import EmpresaSuscriptora, MembresiaEmpresa, SedeEvento
from paquetes.models import PaqueteBoda, PaqueteServicio, PropuestaEvento, PropuestaLinea


def crear_evento(empresa, *, planner=None, nombre="Evento D1"):
    ahora = timezone.now()
    return EventoBoda.objects.create(
        empresa=empresa,
        nombre_evento=nombre,
        novio="Cliente",
        novia="Principal",
        frase_portada="Celebracion",
        mensaje_general="Evento",
        fecha_misa=ahora,
        lugar_misa="Ceremonia",
        fecha_fiesta=ahora,
        lugar_fiesta="Recepcion",
        wedding_planner=planner,
    )


class CommercialCorrectionS23C4D1Tests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.empresa = EmpresaSuscriptora.objects.create(
            nombre_comercial="Empresa C4D1",
            slug="empresa-c4d1",
        )
        self.admin = User.objects.create_user(
            username="admin-c4d1",
            password="test123",
        )
        MembresiaEmpresa.objects.create(
            empresa=self.empresa,
            usuario=self.admin,
            rol="ADMIN_EMPRESA",
        )
        self.sede = SedeEvento.objects.create(
            empresa=self.empresa,
            nombre="Salon C4D1",
        )
        self.evento = crear_evento(
            self.empresa,
            planner=self.admin,
        )
        self.paquete = PaqueteBoda.objects.create(
            empresa=self.empresa,
            nombre="Paquete editable",
            precio_adulto=Decimal("1000.00"),
            cargo_fijo=Decimal("500.00"),
        )
        self.catalogo = ServicioCatalogo.objects.create(
            empresa=self.empresa,
            nombre="DJ C4D1",
            categoria="MUSICA",
            unidad="EVENTO",
        )
        self.paquete_servicio = PaqueteServicio.objects.create(
            paquete=self.paquete,
            servicio_catalogo=self.catalogo,
            cantidad=1,
        )
        self.client.force_login(self.admin)

    def propuesta(self, estado="BORRADOR"):
        return PropuestaEvento.objects.create(
            empresa=self.empresa,
            evento=self.evento,
            sede=self.sede,
            paquete=self.paquete,
            adultos=10,
            ninos=0,
            estado=estado,
        )

    def test_package_editability_helper_accepts_package_object(self):
        from paquetes.views import _paquete_composicion_editable

        self.assertTrue(_paquete_composicion_editable(self.paquete))
        self.propuesta("BORRADOR")
        self.assertFalse(_paquete_composicion_editable(self.paquete))

    def test_cancelled_draft_history_does_not_lock_package(self):
        from paquetes.views import _paquete_composicion_editable

        propuesta = self.propuesta("BORRADOR")
        self.evento.estado = "CANCELADO"
        self.evento.activo = False
        self.evento.save(update_fields=["estado", "activo"])

        self.assertTrue(_paquete_composicion_editable(self.paquete))

        url = reverse(
            "paquetes_servicio_delete",
            args=[self.empresa.slug, self.paquete.id, self.paquete_servicio.id],
        )
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        self.assertFalse(PaqueteServicio.objects.filter(pk=self.paquete_servicio.id).exists())

    def test_cancelled_proposal_does_not_lock_package(self):
        from paquetes.views import _paquete_composicion_editable

        self.propuesta("CANCELADO")
        self.assertTrue(_paquete_composicion_editable(self.paquete))

    def test_accepted_history_still_locks_even_if_event_is_cancelled(self):
        from paquetes.views import _paquete_composicion_editable

        self.propuesta("ACEPTADO")
        self.evento.estado = "CANCELADO"
        self.evento.activo = False
        self.evento.save(update_fields=["estado", "activo"])

        self.assertFalse(_paquete_composicion_editable(self.paquete))

    def test_unused_package_service_can_be_deleted(self):
        url = reverse(
            "paquetes_servicio_delete",
            args=[self.empresa.slug, self.paquete.id, self.paquete_servicio.id],
        )
        response = self.client.post(url)

        self.assertRedirects(
            response,
            reverse(
                "paquetes_paquete_detail",
                args=[self.empresa.slug, self.paquete.id],
            ),
        )
        self.assertFalse(
            PaqueteServicio.objects.filter(pk=self.paquete_servicio.id).exists()
        )

    def test_package_service_is_protected_once_package_is_used(self):
        self.propuesta("BORRADOR")
        url = reverse(
            "paquetes_servicio_delete",
            args=[self.empresa.slug, self.paquete.id, self.paquete_servicio.id],
        )
        response = self.client.post(url)

        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            PaqueteServicio.objects.filter(pk=self.paquete_servicio.id).exists()
        )

    def test_canonical_additional_line_can_be_deleted_before_acceptance(self):
        propuesta = self.propuesta("EN_REVISION")
        linea = PropuestaLinea.objects.create(
            propuesta=propuesta,
            tipo="ADICIONAL",
            servicio_catalogo=self.catalogo,
            nombre="DJ adicional",
            modo_precio="FIJO",
            tarifa=Decimal("5000.00"),
            cantidad=1,
        )
        url = reverse(
            "k9_evento_comercial",
            kwargs={
                "empresa_slug": self.empresa.slug,
                "evento_id": self.evento.id,
            },
        )
        response = self.client.post(
            url,
            {
                "accion": "eliminar_linea",
                "propuesta_id": propuesta.id,
                "linea_id": linea.id,
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertFalse(PropuestaLinea.objects.filter(pk=linea.id).exists())

    def test_canonical_courtesy_line_cannot_be_deleted_after_acceptance(self):
        propuesta = self.propuesta("ACEPTADO")
        linea = PropuestaLinea.objects.create(
            propuesta=propuesta,
            tipo="CORTESIA",
            nombre="Cortesia C4D1",
            modo_precio="FIJO",
            tarifa=Decimal("0.00"),
            cantidad=1,
        )
        url = reverse(
            "k9_evento_comercial",
            kwargs={
                "empresa_slug": self.empresa.slug,
                "evento_id": self.evento.id,
            },
        )
        response = self.client.post(
            url,
            {
                "accion": "eliminar_linea",
                "propuesta_id": propuesta.id,
                "linea_id": linea.id,
            },
        )

        self.assertEqual(response.status_code, 403)
        self.assertTrue(PropuestaLinea.objects.filter(pk=linea.id).exists())

    def test_legacy_editor_line_delete_uses_same_acceptance_rule(self):
        propuesta = self.propuesta("BORRADOR")
        linea = PropuestaLinea.objects.create(
            propuesta=propuesta,
            tipo="ADICIONAL",
            nombre="Extra legacy C4D1",
            modo_precio="FIJO",
            tarifa=Decimal("1500.00"),
            cantidad=1,
        )
        url = reverse(
            "paquetes_propuesta_linea_delete",
            args=[
                self.empresa.slug,
                self.evento.id,
                propuesta.id,
                linea.id,
            ],
        )
        response = self.client.post(url)

        self.assertEqual(response.status_code, 302)
        self.assertFalse(PropuestaLinea.objects.filter(pk=linea.id).exists())
