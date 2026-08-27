from django.test import TestCase
from django.utils import timezone

from catalogo.models import ServicioCatalogo
from invitaciones.models import EventoBoda
from organizaciones.models import EmpresaSuscriptora
from paquetes.forms import PropuestaLineaForm
from paquetes.models import PaqueteBoda, PropuestaEvento, PropuestaLinea


class D72CCatalogLineNameTests(TestCase):
    def setUp(self):
        self.empresa = EmpresaSuscriptora.objects.create(
            nombre_comercial="Empresa D72C", slug="empresa-d72c"
        )
        now = timezone.now()
        self.evento = EventoBoda.objects.create(
            empresa=self.empresa,
            nombre_evento="Evento D72C",
            novio="A",
            novia="B",
            frase_portada="D72C",
            mensaje_general="D72C",
            fecha_misa=now,
            lugar_misa="X",
            fecha_fiesta=now,
            lugar_fiesta="Y",
        )
        self.paquete = PaqueteBoda.objects.create(
            empresa=self.empresa, nombre="Paquete D72C", precio_base=1000
        )
        self.propuesta = PropuestaEvento.objects.create(
            empresa=self.empresa,
            evento=self.evento,
            paquete=self.paquete,
            estado="BORRADOR",
        )
        self.catalogo = ServicioCatalogo.objects.create(
            empresa=self.empresa,
            nombre="DJ Premium",
            categoria="MUSICA",
            activo=True,
        )

    def payload(self, **extra):
        data = {
            "tipo": "ADICIONAL",
            "servicio_catalogo": "",
            "nombre": "",
            "descripcion": "",
            "modo_precio": "FIJO",
            "tarifa": "1500.00",
            "cantidad": "1.00",
            "valor_informativo": "0.00",
            "orden": "0",
        }
        data.update(extra)
        return data

    def test_catalog_service_does_not_require_duplicate_name(self):
        form = PropuestaLineaForm(
            self.payload(servicio_catalogo=str(self.catalogo.pk), nombre=""),
            propuesta=self.propuesta,
        )
        self.assertTrue(form.is_valid(), form.errors)
        linea = form.save()
        self.assertEqual(linea.nombre, "DJ Premium")
        self.assertEqual(linea.servicio_catalogo, self.catalogo)

    def test_catalog_name_cannot_be_overridden_by_post(self):
        form = PropuestaLineaForm(
            self.payload(
                servicio_catalogo=str(self.catalogo.pk),
                nombre="Nombre manipulado",
            ),
            propuesta=self.propuesta,
        )
        self.assertTrue(form.is_valid(), form.errors)
        linea = form.save()
        self.assertEqual(linea.nombre, "DJ Premium")

    def test_manual_service_requires_name(self):
        form = PropuestaLineaForm(self.payload(), propuesta=self.propuesta)
        self.assertFalse(form.is_valid())
        self.assertIn("nombre", form.errors)

    def test_manual_service_preserves_entered_name(self):
        form = PropuestaLineaForm(
            self.payload(nombre="Hora extra de fotografia"),
            propuesta=self.propuesta,
        )
        self.assertTrue(form.is_valid(), form.errors)
        linea = form.save()
        self.assertEqual(linea.nombre, "Hora extra de fotografia")
        self.assertIsNone(linea.servicio_catalogo)

    def test_model_also_enforces_catalog_canonical_name(self):
        linea = PropuestaLinea.objects.create(
            propuesta=self.propuesta,
            tipo="CORTESIA",
            servicio_catalogo=self.catalogo,
            nombre="Alias no permitido",
            modo_precio="FIJO",
            tarifa=0,
            cantidad=1,
        )
        self.assertEqual(linea.nombre, "DJ Premium")
