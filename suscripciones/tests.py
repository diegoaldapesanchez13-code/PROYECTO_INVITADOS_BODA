from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.utils import timezone

from auditoria.models import RegistroAuditoria
from invitaciones.models import EventoBoda
from organizaciones.models import EmpresaSuscriptora, MembresiaEmpresa
from suscripciones.models import PlanSuscripcion, SuscripcionEmpresa


class SuscripcionSaasTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username='admin_cisneros', password='test123')
        self.empresa = EmpresaSuscriptora.objects.create(nombre_comercial='Casa Cisneros', slug='casa-cisneros')
        MembresiaEmpresa.objects.create(empresa=self.empresa, usuario=self.user, rol='ADMIN_EMPRESA')
        self.plan = PlanSuscripcion.objects.create(
            nombre='Profesional',
            precio_mensual=1500,
            limite_usuarios=10,
            limite_wedding_planners=3,
            limite_eventos_activos=20,
        )
        self.client.force_login(self.user)

    def crear_suscripcion(self, **overrides):
        hoy = timezone.localdate()
        datos = {
            'empresa': self.empresa,
            'plan': self.plan,
            'fecha_inicio': hoy,
            'fecha_vencimiento': hoy + timedelta(days=30),
            'estado': 'ACTIVA',
        }
        datos.update(overrides)
        return SuscripcionEmpresa.objects.create(**datos)

    @override_settings(SAAS_REQUIRE_SUBSCRIPTION=True)
    def test_suscripcion_activa_permita_operar_dashboard_empresa(self):
        self.crear_suscripcion()

        response = self.client.post('/dashboard/empresa/', {
            'accion': 'crear_evento',
            'empresa_id': self.empresa.id,
            'nombre_evento': 'XV Camila',
            'tipo_evento': 'XV',
            'nombre_principal': 'Camila',
            'fecha_evento': '2026-12-15T18:00',
            'capacidad_contratada': '180',
            'frase_portada': 'Mis XV',
        })

        self.assertEqual(response.status_code, 302)
        self.assertTrue(EventoBoda.objects.filter(empresa=self.empresa, nombre_evento='XV Camila').exists())

    @override_settings(SAAS_REQUIRE_SUBSCRIPTION=True)
    def test_empresa_sin_suscripcion_se_redirige_a_estado(self):
        response = self.client.get('/dashboard/empresa/')

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], '/suscripcion/estado/')

    @override_settings(SAAS_REQUIRE_SUBSCRIPTION=True)
    def test_suscripcion_vencida_fuera_de_gracia_bloquea_escritura(self):
        hoy = timezone.localdate()
        self.crear_suscripcion(
            fecha_vencimiento=hoy - timedelta(days=10),
            fecha_periodo_gracia=hoy - timedelta(days=1),
            estado='VENCIDA',
        )

        get_response = self.client.get('/dashboard/empresa/')
        post_response = self.client.post('/dashboard/empresa/', {
            'accion': 'crear_evento',
            'empresa_id': self.empresa.id,
            'nombre_evento': 'Boda Bloqueada',
            'tipo_evento': 'BODA',
            'nombre_principal': 'Wendy',
            'fecha_evento': '2026-12-15T18:00',
            'frase_portada': 'Nuestra Boda',
        })

        self.assertEqual(get_response.status_code, 200)
        self.assertEqual(post_response.status_code, 302)
        self.assertEqual(post_response['Location'], '/suscripcion/estado/')
        self.assertFalse(EventoBoda.objects.filter(empresa=self.empresa, nombre_evento='Boda Bloqueada').exists())

    @override_settings(SAAS_REQUIRE_SUBSCRIPTION=True)
    def test_suscripcion_en_gracia_permita_escritura_con_aviso(self):
        hoy = timezone.localdate()
        self.crear_suscripcion(
            fecha_vencimiento=hoy - timedelta(days=2),
            fecha_periodo_gracia=hoy + timedelta(days=5),
            estado='VENCIDA',
        )

        response = self.client.post('/dashboard/empresa/', {
            'accion': 'crear_evento',
            'empresa_id': self.empresa.id,
            'nombre_evento': 'Boda En Gracia',
            'tipo_evento': 'BODA',
            'nombre_principal': 'Wendy',
            'fecha_evento': '2026-12-15T18:00',
            'frase_portada': 'Nuestra Boda',
        })

        self.assertEqual(response.status_code, 302)
        self.assertTrue(EventoBoda.objects.filter(empresa=self.empresa, nombre_evento='Boda En Gracia').exists())

    @override_settings(SAAS_REQUIRE_SUBSCRIPTION=True)
    def test_suscripcion_suspendida_bloquea_dashboard_operativo(self):
        self.crear_suscripcion(estado='SUSPENDIDA')

        response = self.client.get('/dashboard/empresa/')

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], '/suscripcion/estado/')

    def test_limite_plan_bloquea_creacion_de_eventos_activos(self):
        self.plan.limite_eventos_activos = 1
        self.plan.save(update_fields=['limite_eventos_activos'])
        self.crear_suscripcion()
        EventoBoda.objects.create(
            empresa=self.empresa,
            novio='Diego',
            novia='Wendy',
            frase_portada='Nos casamos',
            mensaje_general='Gracias por acompanarnos.',
            fecha_misa=timezone.now(),
            lugar_misa='Templo',
            fecha_fiesta=timezone.now(),
            lugar_fiesta='Salon',
        )

        response = self.client.post('/dashboard/empresa/', {
            'accion': 'crear_evento',
            'empresa_id': self.empresa.id,
            'nombre_evento': 'Evento Bloqueado',
            'tipo_evento': 'BODA',
            'nombre_principal': 'Ana',
            'fecha_evento': '2026-12-15T18:00',
            'frase_portada': 'Nuestra Boda',
        })

        self.assertEqual(response.status_code, 302)
        self.assertFalse(EventoBoda.objects.filter(empresa=self.empresa, nombre_evento='Evento Bloqueado').exists())
        self.assertTrue(RegistroAuditoria.objects.filter(empresa=self.empresa, accion='LIMITE_PLAN_EXCEDIDO').exists())

    def test_limite_plan_bloquea_creacion_de_planners(self):
        User = get_user_model()
        self.plan.limite_usuarios = 10
        self.plan.limite_wedding_planners = 1
        self.plan.save(update_fields=['limite_usuarios', 'limite_wedding_planners'])
        self.crear_suscripcion()
        planner = User.objects.create_user(username='planner_existente', password='test123')
        MembresiaEmpresa.objects.create(
            empresa=self.empresa,
            usuario=planner,
            rol='WEDDING_PLANNER',
            activo=True,
        )

        response = self.client.post('/dashboard/empresa/', {
            'accion': 'crear_planner',
            'empresa_id': self.empresa.id,
            'username_usuario': 'planner_nuevo',
            'password_usuario': 'temporal123',
            'first_name_usuario': 'Sofia',
            'rol_usuario': 'WEDDING_PLANNER',
            'activo_usuario': 'on',
        })

        self.assertEqual(response.status_code, 302)
        self.assertFalse(MembresiaEmpresa.objects.filter(empresa=self.empresa, usuario__username='planner_nuevo').exists())
        self.assertTrue(RegistroAuditoria.objects.filter(empresa=self.empresa, accion='LIMITE_PLAN_EXCEDIDO').exists())

    def test_dashboard_empresa_crea_cliente_y_lo_asigna_a_evento(self):
        self.crear_suscripcion()
        evento = EventoBoda.objects.create(
            empresa=self.empresa,
            nombre_evento='Boda Wendy y Diego',
            novio='Diego',
            novia='Wendy',
            frase_portada='Nos casamos',
            mensaje_general='Gracias por acompanarnos.',
            fecha_misa=timezone.now(),
            lugar_misa='Templo',
            fecha_fiesta=timezone.now(),
            lugar_fiesta='Salon',
        )

        response = self.client.post('/dashboard/empresa/', {
            'accion': 'crear_cliente',
            'empresa_id': self.empresa.id,
            'username_usuario': 'cliente_wendy',
            'password_usuario': 'temporal123',
            'first_name_usuario': 'Wendy',
            'last_name_usuario': 'Lopez',
            'email_usuario': 'wendy@example.com',
            'rol_usuario': 'CLIENTE',
            'evento_cliente_id': evento.id,
            'activo_usuario': 'on',
        })

        evento.refresh_from_db()
        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            MembresiaEmpresa.objects.filter(
                empresa=self.empresa,
                usuario__username='cliente_wendy',
                rol='CLIENTE',
                activo=True,
            ).exists()
        )
        self.assertTrue(evento.clientes.filter(username='cliente_wendy').exists())
        self.assertTrue(RegistroAuditoria.objects.filter(empresa=self.empresa, accion='CREAR_CLIENTE_EMPRESA').exists())

    def test_limite_plan_bloquea_creacion_de_clientes(self):
        User = get_user_model()
        self.plan.limite_usuarios = 10
        self.plan.limite_clientes = 1
        self.plan.save(update_fields=['limite_usuarios', 'limite_clientes'])
        self.crear_suscripcion()
        cliente = User.objects.create_user(username='cliente_existente', password='test123')
        MembresiaEmpresa.objects.create(
            empresa=self.empresa,
            usuario=cliente,
            rol='CLIENTE',
            activo=True,
        )

        response = self.client.post('/dashboard/empresa/', {
            'accion': 'crear_cliente',
            'empresa_id': self.empresa.id,
            'username_usuario': 'cliente_nuevo',
            'password_usuario': 'temporal123',
            'first_name_usuario': 'Ana',
            'rol_usuario': 'CLIENTE',
            'activo_usuario': 'on',
        })

        self.assertEqual(response.status_code, 302)
        self.assertFalse(MembresiaEmpresa.objects.filter(empresa=self.empresa, usuario__username='cliente_nuevo').exists())
        self.assertTrue(RegistroAuditoria.objects.filter(empresa=self.empresa, accion='LIMITE_PLAN_EXCEDIDO').exists())

    def test_planner_crea_evento_y_queda_autoasignado(self):
        User = get_user_model()
        planner = User.objects.create_user(username='planner_sofia', password='test123')
        MembresiaEmpresa.objects.create(
            empresa=self.empresa,
            usuario=planner,
            rol='WEDDING_PLANNER',
            activo=True,
        )
        self.crear_suscripcion()
        self.client.force_login(planner)

        response = self.client.post(f'/dashboard/planner/?empresa={self.empresa.id}', {
            'accion': 'crear_evento_planner',
            'empresa_id': self.empresa.id,
            'nombre_evento': 'Boda Planner',
            'tipo_evento': 'BODA',
            'nombre_principal': 'Wendy',
            'nombre_secundario': 'Diego',
            'fecha_evento': '2026-12-15T18:00',
            'lugar_ceremonia': 'Templo',
            'lugar_recepcion': 'Salon',
            'capacidad_contratada': '180',
            'frase_portada': 'Nuestra Boda',
        })

        evento = EventoBoda.objects.get(empresa=self.empresa, nombre_evento='Boda Planner')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], '/empresa/casa-cisneros/planner/dashboard/#eventos')
        self.assertEqual(evento.wedding_planner, planner)
        self.assertTrue(RegistroAuditoria.objects.filter(empresa=self.empresa, evento=evento, accion='CREAR_EVENTO_PLANNER').exists())

    def test_planner_no_puede_crear_evento_si_plan_llego_al_limite(self):
        User = get_user_model()
        self.plan.limite_eventos_activos = 1
        self.plan.save(update_fields=['limite_eventos_activos'])
        planner = User.objects.create_user(username='planner_sofia', password='test123')
        MembresiaEmpresa.objects.create(
            empresa=self.empresa,
            usuario=planner,
            rol='WEDDING_PLANNER',
            activo=True,
        )
        self.crear_suscripcion()
        EventoBoda.objects.create(
            empresa=self.empresa,
            wedding_planner=planner,
            nombre_evento='Evento Existente',
            novio='Diego',
            novia='Wendy',
            frase_portada='Nos casamos',
            mensaje_general='Gracias por acompanarnos.',
            fecha_misa=timezone.now(),
            lugar_misa='Templo',
            fecha_fiesta=timezone.now(),
            lugar_fiesta='Salon',
        )
        self.client.force_login(planner)

        response = self.client.post(f'/dashboard/planner/?empresa={self.empresa.id}', {
            'accion': 'crear_evento_planner',
            'empresa_id': self.empresa.id,
            'nombre_evento': 'Evento Bloqueado Planner',
            'tipo_evento': 'BODA',
            'nombre_principal': 'Ana',
            'fecha_evento': '2026-12-15T18:00',
            'frase_portada': 'Nuestra Boda',
        })

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], '/empresa/casa-cisneros/planner/dashboard/#eventos')
        self.assertFalse(EventoBoda.objects.filter(empresa=self.empresa, nombre_evento='Evento Bloqueado Planner').exists())
        self.assertTrue(RegistroAuditoria.objects.filter(empresa=self.empresa, accion='LIMITE_PLAN_EXCEDIDO').exists())
