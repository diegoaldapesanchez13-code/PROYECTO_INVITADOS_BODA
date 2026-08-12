from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from invitaciones.models import EventoBoda
from organizaciones.models import EmpresaSuscriptora

from .models import Proveedor, ServicioCatalogoProveedor, ServicioEvento


class ServicioEventoFoundationTests(TestCase):
    def setUp(self):
        self.empresa = EmpresaSuscriptora.objects.create(nombre_comercial='Tenant A', slug='tenant-a-k82')
        self.otra_empresa = EmpresaSuscriptora.objects.create(nombre_comercial='Tenant B', slug='tenant-b-k82')
        now = timezone.now()
        self.evento = EventoBoda.objects.create(
            empresa=self.empresa,
            nombre_evento='Evento K82',
            novio='A', novia='B', frase_portada='x', mensaje_general='x',
            fecha_misa=now, lugar_misa='x', fecha_fiesta=now, lugar_fiesta='x',
        )
        self.proveedor = Proveedor.objects.create(empresa=self.empresa, nombre_comercial='Proveedor A')
        self.proveedor_otro = Proveedor.objects.create(empresa=self.otra_empresa, nombre_comercial='Proveedor B')

    def test_rejects_cross_tenant_provider(self):
        servicio = ServicioEvento(evento=self.evento, proveedor=self.proveedor_otro, nombre_servicio='No valido')
        with self.assertRaises(ValidationError):
            servicio.full_clean()

    def test_catalog_snapshot_is_copied(self):
        catalogo = ServicioCatalogoProveedor.objects.create(
            empresa=self.empresa,
            proveedor=self.proveedor,
            nombre='Decoracion floral',
            descripcion='Base catalogo',
            categoria='DECORACION',
        )
        servicio = ServicioEvento(
            evento=self.evento,
            proveedor=self.proveedor,
            servicio_catalogo=catalogo,
            nombre_servicio='Decoracion F&D',
            origen='CATALOGO',
        )
        servicio.capturar_snapshot_catalogo()
        self.assertEqual(servicio.proveedor_nombre_snapshot, 'Proveedor A')
        self.assertEqual(servicio.catalogo_nombre_snapshot, 'Decoracion floral')
        self.assertEqual(servicio.categoria, 'DECORACION')
