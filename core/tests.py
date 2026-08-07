from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase

from invitaciones.models import EventoBoda
from organizaciones.models import EmpresaSuscriptora, MembresiaEmpresa
from proveedores.models import Proveedor, ServicioEvento


def crear_evento_base(**overrides):
    from django.utils import timezone

    datos = {
        'novio': 'Diego',
        'novia': 'Wendy',
        'frase_portada': 'Nos casamos',
        'mensaje_general': 'Gracias por acompanarnos.',
        'fecha_misa': timezone.now(),
        'lugar_misa': 'Templo',
        'fecha_fiesta': timezone.now(),
        'lugar_fiesta': 'Salon',
    }
    datos.update(overrides)
    return EventoBoda.objects.create(**datos)


class LoginCentralSaasTests(TestCase):
    def test_login_central_redirige_dirtec_a_dashboard_dirtec(self):
        User = get_user_model()
        User.objects.create_superuser(username='dirtec', password='test123')

        response = self.client.post('/login/', {'username': 'dirtec', 'password': 'test123'})
        follow = self.client.get(response['Location'])

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], '/redirigir/')
        self.assertEqual(follow.status_code, 302)
        self.assertEqual(follow['Location'], '/dirtec/dashboard/')

    def test_login_central_redirige_admin_empresa_a_slug(self):
        User = get_user_model()
        user = User.objects.create_user(username='admin_cisneros', password='test123')
        empresa = EmpresaSuscriptora.objects.create(nombre_comercial='Casa Cisneros', slug='casa-cisneros')
        MembresiaEmpresa.objects.create(empresa=empresa, usuario=user, rol='ADMIN_EMPRESA')

        response = self.client.post('/login/', {'username': 'admin_cisneros', 'password': 'test123'})
        follow = self.client.get(response['Location'])

        self.assertEqual(response.status_code, 302)
        self.assertEqual(follow['Location'], '/empresa/casa-cisneros/dashboard/')

    def test_login_central_redirige_planner_a_slug(self):
        User = get_user_model()
        user = User.objects.create_user(username='planner_sofia', password='test123')
        empresa = EmpresaSuscriptora.objects.create(nombre_comercial='Casa Cisneros', slug='casa-cisneros')
        MembresiaEmpresa.objects.create(empresa=empresa, usuario=user, rol='WEDDING_PLANNER')

        response = self.client.post('/login/', {'username': 'planner_sofia', 'password': 'test123'})
        follow = self.client.get(response['Location'])

        self.assertEqual(response.status_code, 302)
        self.assertEqual(follow['Location'], '/empresa/casa-cisneros/wedding-planner/dashboard/')

    def test_recuperacion_password_renderiza_y_envia_en_desarrollo(self):
        User = get_user_model()
        User.objects.create_user(username='planner_reset', email='planner@example.com', password='test123')

        form = self.client.get('/password-reset/')
        response = self.client.post('/password-reset/', {'email': 'planner@example.com'})

        self.assertEqual(form.status_code, 200)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], '/password-reset/enviado/')

    def test_admin_django_solo_permite_dirtec_autorizado(self):
        User = get_user_model()
        dirtec = User.objects.create_superuser(username='dirtec_admin', password='test123')
        staff_empresa = User.objects.create_user(username='staff_empresa', password='test123', is_staff=True)
        empresa = EmpresaSuscriptora.objects.create(nombre_comercial='Casa Cisneros', slug='casa-cisneros')
        MembresiaEmpresa.objects.create(empresa=empresa, usuario=staff_empresa, rol='ADMIN_EMPRESA')

        self.client.force_login(staff_empresa)
        response_staff = self.client.get('/admin/')

        self.client.force_login(dirtec)
        response_dirtec = self.client.get('/admin/')

        self.assertEqual(response_staff.status_code, 302)
        self.assertIn('/admin/login/', response_staff['Location'])
        self.assertEqual(response_dirtec.status_code, 200)

    def test_admin_django_permite_staff_en_grupo_dirtec(self):
        User = get_user_model()
        grupo = Group.objects.create(name='DIRTEC')
        user = User.objects.create_user(username='dirtec_operativo', password='test123', is_staff=True)
        user.groups.add(grupo)

        self.client.force_login(user)
        response = self.client.get('/admin/')

        self.assertEqual(response.status_code, 200)

    def test_dashboard_dirtec_permite_grupo_dirtec(self):
        User = get_user_model()
        grupo = Group.objects.create(name='DIRTEC')
        user = User.objects.create_user(username='dirtec_dashboard', password='test123', is_staff=True)
        user.groups.add(grupo)
        self.client.force_login(user)

        response = self.client.get('/dirtec/dashboard/')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Control comercial SaaS')

    def test_ruta_empresa_slug_valida_membresia(self):
        User = get_user_model()
        user = User.objects.create_user(username='admin_cisneros', password='test123')
        empresa = EmpresaSuscriptora.objects.create(nombre_comercial='Casa Cisneros', slug='casa-cisneros')
        EmpresaSuscriptora.objects.create(nombre_comercial='Otra Empresa', slug='otra-empresa')
        MembresiaEmpresa.objects.create(empresa=empresa, usuario=user, rol='ADMIN_EMPRESA')
        self.client.force_login(user)

        response = self.client.get('/empresa/casa-cisneros/dashboard/')
        response_ajena = self.client.get('/empresa/otra-empresa/dashboard/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response_ajena.status_code, 404)

    def test_ruta_planner_alias_funciona(self):
        User = get_user_model()
        user = User.objects.create_user(username='planner_sofia', password='test123')
        empresa = EmpresaSuscriptora.objects.create(nombre_comercial='Casa Cisneros', slug='casa-cisneros')
        MembresiaEmpresa.objects.create(empresa=empresa, usuario=user, rol='WEDDING_PLANNER')
        self.client.force_login(user)

        response = self.client.get('/empresa/casa-cisneros/planner/dashboard/')

        self.assertEqual(response.status_code, 200)

    def test_rutas_cliente_y_proveedor_funcionan_como_alias(self):
        User = get_user_model()
        cliente = User.objects.create_user(username='cliente', password='test123')
        proveedor_user = User.objects.create_user(username='proveedor', password='test123')
        evento = crear_evento_base()
        evento.clientes.add(cliente)
        proveedor = Proveedor.objects.create(usuario=proveedor_user, nombre_comercial='Foto Luz')
        ServicioEvento.objects.create(evento=evento, proveedor=proveedor, nombre_servicio='Cobertura')

        self.client.force_login(cliente)
        response_cliente = self.client.get('/cliente/dashboard/')
        self.client.force_login(proveedor_user)
        response_proveedor = self.client.get('/proveedor/dashboard/')

        self.assertEqual(response_cliente.status_code, 200)
        self.assertEqual(response_proveedor.status_code, 200)
