from datetime import timedelta
import json

from django.test import TestCase
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command

from aprobaciones.models import AprobacionEvento
from catering.models import Alimento, CateringEvento, CategoriaAlimento, PaqueteBuffet
from decoracion.models import ElementoDecoracion
from documentos.models import DocumentoEvento
from entretenimiento.models import CancionEvento, EntretenimientoEvento
from itinerario.models import ActividadItinerario
from notificaciones.models import Notificacion
from organizaciones.models import EmpresaSuscriptora, MembresiaEmpresa, SedeEvento
from paquetes.models import PaqueteBoda, PaqueteEvento
from presupuesto.models import CategoriaGasto, GastoEvento, PagoEvento
from proveedores.models import PersonalEvento, Proveedor, ServicioEvento
from mesas.models import AsignacionMesa, Mesa
from suscripciones.models import PagoSuscripcion, PlanSuscripcion, SuscripcionEmpresa
from tareas.models import TareaEvento
from auditoria.models import RegistroAuditoria
from .models import AssetInvitacion, DetalleProduccionEvento, DisenoInvitacion, EnlaceRegalo, EventoBoda, FotoEvento, Grupoinvitacion, Invitado, ItinerarioEvento, MenuBoda, PersonaCeremonia, SeccionInvitacion, VersionDisenoInvitacion


def crear_evento():
    ahora = timezone.now()
    return EventoBoda.objects.create(
        novio='Diego',
        novia='Wendy',
        frase_portada='Nos casamos',
        mensaje_general='Gracias por acompanarnos.',
        fecha_misa=ahora,
        lugar_misa='Templo',
        fecha_fiesta=ahora,
        lugar_fiesta='Salon',
    )


class InvitadoTests(TestCase):
    def test_invitado_muestra_nombre_completo(self):
        grupo = Grupoinvitacion.objects.create(
            evento=crear_evento(),
            nombre_grupo='Familia Perez',
            tipo='FAMILIAR',
        )
        invitado = Invitado.objects.create(
            grupo=grupo,
            nombre='Ana',
            apellidos='Perez Lopez',
            tipo_persona='ADULTO',
        )

        self.assertEqual(str(invitado), 'Ana Perez Lopez')

    def test_confirmacion_personal_guarda_notas_de_alimentos(self):
        grupo = Grupoinvitacion.objects.create(
            evento=crear_evento(),
            nombre_grupo='Carlos',
            tipo='PERSONAL',
            cantidad_extra_permitida=1,
        )

        response = self.client.post(f'/invitacion/{grupo.codigo}/', {
            'asistira': 'si',
            'acompanantes_adultos': '1',
            'acompanantes_ninos': '0',
            'restricciones_alimentarias': 'Vegetariano',
            'alergias': 'Nueces',
            'requiere_menu_infantil': 'on',
        })

        grupo.refresh_from_db()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(grupo.restricciones_alimentarias, 'Vegetariano')
        self.assertEqual(grupo.alergias, 'Nueces')
        self.assertTrue(grupo.requiere_menu_infantil)

    def test_confirmacion_personal_usa_acompanantes_capturados_por_planner(self):
        grupo = Grupoinvitacion.objects.create(
            evento=crear_evento(),
            nombre_grupo='Carlos',
            tipo='PERSONAL',
            cantidad_extra_permitida=1,
        )
        extra = Invitado.objects.create(
            grupo=grupo,
            nombre='Acompanante 1',
            tipo_persona='NINO',
        )

        response = self.client.post(f'/invitacion/{grupo.codigo}/', {
            'asistira': 'si',
            f'asistira_extra_{extra.id}': 'si',
            f'menu_infantil_extra_{extra.id}': 'on',
            f'comentario_extra_{extra.id}': 'Prefiere nuggets',
        })

        grupo.refresh_from_db()
        extra.refresh_from_db()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(grupo.cantidad_confirmada, 2)
        self.assertEqual(grupo.adultos_confirmados, 1)
        self.assertEqual(grupo.ninos_confirmados, 1)
        self.assertTrue(extra.asistira)
        self.assertTrue(extra.menu_infantil)
        self.assertEqual(extra.comentario, 'Prefiere nuggets')

    def test_invitacion_no_muestra_iconos_de_seccion(self):
        grupo = Grupoinvitacion.objects.create(
            evento=crear_evento(),
            nombre_grupo='Carlos',
            tipo='PERSONAL',
        )

        response = self.client.get(f'/invitacion/{grupo.codigo}/')

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'section-icon')
        self.assertNotContains(response, 'place-icon')
        self.assertNotContains(response, 'itinerary-icon')

    def test_invitacion_permite_iframe_del_mismo_sitio_para_editor(self):
        grupo = Grupoinvitacion.objects.create(
            evento=crear_evento(),
            nombre_grupo='Carlos',
            tipo='PERSONAL',
        )

        response = self.client.get(f'/invitacion/{grupo.codigo}/?preview=1')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers.get('X-Frame-Options'), 'SAMEORIGIN')

    def test_confirmacion_familiar_guarda_notas_por_invitado(self):
        grupo = Grupoinvitacion.objects.create(
            evento=crear_evento(),
            nombre_grupo='Familia Perez',
            tipo='FAMILIAR',
        )
        invitado = Invitado.objects.create(
            grupo=grupo,
            nombre='Ana',
            tipo_persona='NINO',
        )

        response = self.client.post(f'/invitacion/{grupo.codigo}/', {
            f'asistira_{invitado.id}': 'si',
            f'restricciones_{invitado.id}': 'Sin lactosa',
            f'alergias_{invitado.id}': 'Mariscos',
            f'menu_infantil_{invitado.id}': 'on',
        })

        invitado.refresh_from_db()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(invitado.restricciones_alimentarias, 'Sin lactosa')
        self.assertEqual(invitado.alergias, 'Mariscos')
        self.assertTrue(invitado.menu_infantil)

    def test_invitacion_usa_titulo_y_descripcion_de_seccion_editable(self):
        evento = crear_evento()
        grupo = Grupoinvitacion.objects.create(
            evento=evento,
            nombre_grupo='Familia Perez',
            tipo='FAMILIAR',
        )
        SeccionInvitacion.objects.create(
            evento=evento,
            tipo='DETALLES',
            titulo='Ubicaciones importantes',
            descripcion='Templo, recepcion y dress code en una sola seccion.',
            orden=15,
            activa=True,
        )

        response = self.client.get(f'/invitacion/{grupo.codigo}/')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Ubicaciones importantes')
        self.assertContains(response, 'Templo, recepcion y dress code en una sola seccion.')

    def test_dress_code_es_seccion_independiente(self):
        evento = crear_evento()
        evento.dress_code = 'Formal oscuro'
        evento.dress_code_descripcion = 'Evitar blanco y tonos muy claros.'
        evento.save()
        grupo = Grupoinvitacion.objects.create(
            evento=evento,
            nombre_grupo='Familia Perez',
            tipo='FAMILIAR',
        )
        SeccionInvitacion.objects.create(
            evento=evento,
            tipo='DRESS_CODE',
            titulo='Codigo de vestimenta',
            descripcion='Etiqueta fina para la celebracion.',
            orden=35,
            activa=True,
        )

        response = self.client.get(f'/invitacion/{grupo.codigo}/')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="dress-code"')
        self.assertContains(response, 'dress-section-card', count=1)
        self.assertContains(response, 'Codigo de vestimenta')
        self.assertContains(response, 'Formal oscuro')

    def test_invitacion_muestra_portadas_de_ceremonia_y_fiesta(self):
        evento = crear_evento()
        evento.foto_ceremonia = SimpleUploadedFile('templo.gif', b'gif-templo', content_type='image/gif')
        evento.foto_recepcion = SimpleUploadedFile('fiesta.gif', b'gif-fiesta', content_type='image/gif')
        evento.save()
        grupo = Grupoinvitacion.objects.create(
            evento=evento,
            nombre_grupo='Familia Perez',
            tipo='FAMILIAR',
        )

        response = self.client.get(f'/invitacion/{grupo.codigo}/')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'place-media')
        self.assertContains(response, 'templo')
        self.assertContains(response, 'fiesta')

    def test_dashboard_actualiza_seccion_editable(self):
        User = get_user_model()
        admin = User.objects.create_superuser(username='dirtec_secciones', password='test123')
        evento = crear_evento()
        grupo = Grupoinvitacion.objects.create(
            evento=evento,
            nombre_grupo='Familia Perez',
            tipo='FAMILIAR',
        )
        self.client.force_login(admin)
        self.client.get(f'/dashboard/?evento={evento.id}')
        seccion = SeccionInvitacion.objects.get(evento=evento, tipo='REGALOS')

        response = self.client.post('/dashboard/', {
            'accion': 'editar_seccion_invitacion',
            'evento_id': evento.id,
            'seccion_id': seccion.id,
            'titulo_seccion': 'Detalles para regalar',
            'descripcion_seccion': 'Elige tienda o deposito.',
            'orden_seccion': '33',
            'posicion_fondo': 'top center',
            'opacidad_fondo': '0.25',
            'activa_seccion': 'on',
            'mostrar_titulo_texto': 'on',
            'color_texto_seccion': '#1e2b44',
        })

        seccion.refresh_from_db()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], f'/dashboard/?evento={evento.id}#secciones-invitacion')
        self.assertEqual(seccion.titulo, 'Detalles para regalar')
        self.assertEqual(seccion.orden, 33)
        self.assertTrue(seccion.activa)
        self.assertEqual(seccion.posicion_fondo, 'top center')

    def test_dashboard_elimina_fondo_de_seccion_editable(self):
        User = get_user_model()
        admin = User.objects.create_superuser(username='dirtec_seccion_fondo', password='test123')
        evento = crear_evento()
        self.client.force_login(admin)
        self.client.get(f'/dashboard/?evento={evento.id}')
        seccion = SeccionInvitacion.objects.get(evento=evento, tipo='DETALLES')
        seccion.fondo = SimpleUploadedFile('detalles.gif', b'gif-detalles', content_type='image/gif')
        seccion.imagen_titulo = SimpleUploadedFile('titulo.gif', b'gif-titulo', content_type='image/gif')
        seccion.save()

        response = self.client.post('/dashboard/', {
            'accion': 'editar_seccion_invitacion',
            'evento_id': evento.id,
            'seccion_id': seccion.id,
            'titulo_seccion': seccion.titulo,
            'descripcion_seccion': seccion.descripcion,
            'orden_seccion': str(seccion.orden),
            'posicion_fondo': seccion.posicion_fondo,
            'opacidad_fondo': str(seccion.opacidad_fondo),
            'activa_seccion': 'on',
            'mostrar_titulo_texto': 'on',
            'eliminar_fondo': 'on',
            'eliminar_imagen_titulo': 'on',
        })

        seccion.refresh_from_db()
        self.assertEqual(response.status_code, 302)
        self.assertFalse(seccion.fondo)
        self.assertFalse(seccion.imagen_titulo)

    def test_editor_visual_crea_diseno_y_abre_para_dirtec(self):
        User = get_user_model()
        admin = User.objects.create_superuser(username='dirtec_editor', password='test123')
        evento = crear_evento()
        self.client.force_login(admin)

        response = self.client.get(f'/dashboard/editor-invitacion/{evento.id}/')

        self.assertEqual(response.status_code, 200)
        self.assertTrue(DisenoInvitacion.objects.filter(evento=evento).exists())
        self.assertContains(response, 'Editor visual de invitacion')

    def test_editor_visual_permite_acceso_a_planner_asignado(self):
        User = get_user_model()
        empresa = EmpresaSuscriptora.objects.create(nombre_comercial='Casa Cisneros', slug='casa-cisneros')
        planner = User.objects.create_user(username='planner_editor', password='test123')
        MembresiaEmpresa.objects.create(empresa=empresa, usuario=planner, rol='WEDDING_PLANNER')
        evento = crear_evento()
        evento.empresa = empresa
        evento.wedding_planner = planner
        evento.save()
        self.client.force_login(planner)

        response = self.client.get(f'/dashboard/editor-invitacion/{evento.id}/')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Editor visual de invitacion')

    def test_guardar_borrador_editor_no_publica_cambios_en_evento(self):
        User = get_user_model()
        admin = User.objects.create_superuser(username='dirtec_borrador_editor', password='test123')
        evento = crear_evento()
        self.client.force_login(admin)
        self.client.get(f'/dashboard/editor-invitacion/{evento.id}/')
        seccion = SeccionInvitacion.objects.get(evento=evento, tipo='DETALLES')
        payload = {
            'theme': {
                'palette': 'ROSA',
                'envelopePalette': 'ROSA',
                'fontStyle': 'MODERNA',
                'primary': '#6f3448',
                'secondary': '#fff4f6',
                'accent': '#c77d92',
                'background': '#fff4f6',
            },
            'layout': {'maxWidth': 430, 'sectionSpacing': 'soft', 'animation': 'fade'},
            'sections': [{
                'sectionId': seccion.id,
                'type': seccion.tipo,
                'title': 'Ubicaciones finas',
                'description': 'Nueva descripcion en borrador.',
                'visible': False,
                'order': 9,
                'config': {
                    'textAlign': 'center',
                    'titleSize': 'small',
                    'backgroundOpacity': '0.20',
                    'backgroundPosition': 'center center',
                    'textColor': '#6f3448',
                    'showTextTitle': True,
                },
            }],
        }

        response = self.client.post(
            f'/dashboard/editor-invitacion/{evento.id}/guardar/',
            data=json.dumps(payload),
            content_type='application/json',
        )

        evento.refresh_from_db()
        seccion.refresh_from_db()
        diseno = DisenoInvitacion.objects.get(evento=evento)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(evento.paleta_colores, 'BOSQUE')
        self.assertNotEqual(seccion.titulo, 'Ubicaciones finas')
        self.assertEqual(diseno.configuracion_borrador['theme']['palette'], 'ROSA')
        self.assertEqual(VersionDisenoInvitacion.objects.filter(diseno=diseno, publicado=False).count(), 1)

    def test_publicar_editor_sincroniza_invitacion_real(self):
        User = get_user_model()
        admin = User.objects.create_superuser(username='dirtec_publicar_editor', password='test123')
        evento = crear_evento()
        self.client.force_login(admin)
        self.client.get(f'/dashboard/editor-invitacion/{evento.id}/')
        seccion = SeccionInvitacion.objects.get(evento=evento, tipo='DETALLES')
        asset_libre = AssetInvitacion.objects.create(
            evento=evento,
            tipo='DECORACION',
            titulo='Flor libre',
            archivo=SimpleUploadedFile('flor-libre.webp', b'webp-flor', content_type='image/webp'),
            creado_por=admin,
        )
        payload = {
            'theme': {
                'palette': 'ROSA',
                'envelopePalette': 'ROSA',
                'fontStyle': 'MODERNA',
                'primary': '#6f3448',
                'secondary': '#fff4f6',
                'accent': '#c77d92',
                'background': '#fff4f6',
            },
            'layout': {'maxWidth': 430, 'sectionSpacing': 'soft', 'animation': 'fade'},
            'sections': [{
                'sectionId': seccion.id,
                'type': seccion.tipo,
                'title': 'Ubicaciones finas',
                'description': 'Ceremonia y fiesta organizadas.',
                'visible': True,
                'order': 11,
                'config': {
                    'textAlign': 'center',
                    'titleSize': 'small',
                    'backgroundOpacity': '0.20',
                    'backgroundPosition': 'top center',
                    'backgroundFit': 'free',
                    'backgroundX': 72,
                    'backgroundY': 24,
                    'backgroundScale': 1.45,
                    'backgroundBrightness': 0.85,
                    'backgroundBlur': 2,
                    'sectionHeight': 360,
                    'titleX': -12,
                    'titleY': 34,
                    'titleScale': 1.15,
                    'titleOpacity': 0.9,
                    'titleRotation': -6,
                    'titleZ': 4,
                    'titleWidth': 48,
                    'titleAlign': 'left',
                    'textX': 118,
                    'textY': 66,
                    'textScale': 0.85,
                    'textOpacity': 0.75,
                    'textRotation': 2,
                    'textZ': 3,
                    'textWidth': 42,
                    'textAlignLayer': 'right',
                    'decorX': 132,
                    'decorY': 12,
                    'decorScale': 1.1,
                    'decorOpacity': 0.5,
                    'decorRotation': 8,
                    'decorZ': 1,
                    'decorWidth': 30,
                    'decorAlign': 'left',
                    'decorVisible': True,
                    'decorStyle': 'dots',
                    'activeLayer': 'custom:capa-frase',
                    'customLayers': [{
                        'id': 'capa-frase',
                        'kind': 'text',
                        'name': 'Frase libre',
                        'text': 'Texto colocado libremente',
                        'x': 132,
                        'y': -10,
                        'scale': 1.2,
                        'opacity': 0.8,
                        'rotation': 12,
                        'z': 8,
                        'width': 44,
                        'align': 'left',
                        'visible': True,
                    }, {
                        'id': 'capa-imagen',
                        'kind': 'image',
                        'name': 'Flor libre',
                        'asset': {'id': asset_libre.id},
                        'x': 12,
                        'y': 88,
                        'scale': 0.75,
                        'opacity': 0.72,
                        'rotation': -18,
                        'z': 7,
                        'width': 28,
                        'fit': 'cover',
                        'visible': True,
                    }],
                    'textColor': '#6f3448',
                    'showTextTitle': True,
                },
            }],
        }

        response = self.client.post(
            f'/dashboard/editor-invitacion/{evento.id}/publicar/',
            data=json.dumps(payload),
            content_type='application/json',
        )

        evento.refresh_from_db()
        seccion.refresh_from_db()
        diseno = DisenoInvitacion.objects.get(evento=evento)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(evento.paleta_colores, 'ROSA')
        self.assertEqual(evento.estilo_letra, 'MODERNA')
        self.assertEqual(seccion.titulo, 'Ubicaciones finas')
        self.assertEqual(seccion.orden, 11)
        self.assertEqual(seccion.posicion_fondo, 'top center')
        self.assertTrue(diseno.tiene_publicacion)
        self.assertEqual(VersionDisenoInvitacion.objects.filter(diseno=diseno, publicado=True).count(), 1)
        grupo = Grupoinvitacion.objects.create(evento=evento, nombre_grupo='Preview publicado', tipo='PERSONAL')
        public_response = self.client.get(f'/invitacion/{grupo.codigo}/')
        self.assertContains(public_response, '--section-height:360px')
        self.assertContains(public_response, '--section-bg-position:72% 24%')
        self.assertContains(public_response, '--section-bg-blur:2.0px')
        self.assertContains(public_response, '--section-title-x:-12%')
        self.assertContains(public_response, '--section-title-rotation:-6deg')
        self.assertContains(public_response, '--section-title-z:4')
        self.assertContains(public_response, '--section-title-width:48%')
        self.assertContains(public_response, '--section-title-align:left')
        self.assertContains(public_response, '--section-text-opacity:0.75')
        self.assertContains(public_response, '--section-text-rotation:2deg')
        self.assertContains(public_response, '--section-text-x:118%')
        self.assertContains(public_response, '--section-text-width:42%')
        self.assertContains(public_response, '--section-text-align:right')
        self.assertContains(public_response, '--section-decor-display:block')
        self.assertContains(public_response, '--section-decor-rotation:8deg')
        self.assertContains(public_response, '--section-decor-x:132%')
        self.assertContains(public_response, '--section-decor-width:30%')
        self.assertContains(public_response, '--section-decor-align:left')
        self.assertContains(public_response, '--section-decor-content:&quot;. . .&quot;')
        self.assertContains(public_response, 'custom-public-layer')
        self.assertContains(public_response, 'Texto colocado libremente')
        self.assertContains(public_response, '--layer-x:132%')
        self.assertContains(public_response, '--layer-y:-10%')
        self.assertContains(public_response, '--layer-scale:1.2')
        self.assertContains(public_response, '--layer-opacity:0.8')
        self.assertContains(public_response, '--layer-rotation:12deg')
        self.assertContains(public_response, '--layer-z:8')
        self.assertContains(public_response, '--layer-width:44%')
        self.assertContains(public_response, '--layer-align:left')
        self.assertContains(public_response, 'custom-public-layer-image')
        self.assertContains(public_response, 'flor-libre')
        self.assertContains(public_response, '--layer-fit:cover')

    def test_editor_restaura_version_a_borrador(self):
        User = get_user_model()
        admin = User.objects.create_superuser(username='dirtec_restore_editor', password='test123')
        evento = crear_evento()
        self.client.force_login(admin)
        self.client.get(f'/dashboard/editor-invitacion/{evento.id}/')
        seccion = SeccionInvitacion.objects.get(evento=evento, tipo='DETALLES')
        diseno = DisenoInvitacion.objects.get(evento=evento)
        version = VersionDisenoInvitacion.objects.create(
            diseno=diseno,
            nombre='Version anterior',
            configuracion={
                'theme': {'palette': 'ROSA', 'envelopePalette': 'ROSA', 'fontStyle': 'MODERNA'},
                'layout': {'maxWidth': 430, 'sectionSpacing': 'soft', 'animation': 'fade'},
                'sections': [{
                    'sectionId': seccion.id,
                    'type': seccion.tipo,
                    'title': 'Restaurado desde historial',
                    'description': 'Descripcion anterior.',
                    'visible': True,
                    'order': 10,
                    'config': {
                        'textAlign': 'center',
                        'titleSize': 'medium',
                        'backgroundOpacity': '0.15',
                        'backgroundPosition': 'center center',
                        'textColor': '#6f3448',
                        'showTextTitle': True,
                    },
                }],
            },
            publicado=True,
            creado_por=admin,
        )

        response = self.client.post(
            f'/dashboard/editor-invitacion/{evento.id}/versiones/restaurar/',
            data=json.dumps({'versionId': version.id}),
            content_type='application/json',
        )

        diseno.refresh_from_db()
        seccion.refresh_from_db()
        seccion_restaurada = next(
            item for item in diseno.configuracion_borrador['sections'] if item['sectionId'] == seccion.id
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(diseno.estado, 'BORRADOR')
        self.assertEqual(seccion_restaurada['title'], 'Restaurado desde historial')
        self.assertNotEqual(seccion.titulo, 'Restaurado desde historial')
        self.assertGreaterEqual(len(response.json()['versions']), 2)

    def test_editor_aplica_plantilla_completa_de_cumpleanos(self):
        User = get_user_model()
        admin = User.objects.create_superuser(username='dirtec_template_editor', password='test123')
        evento = crear_evento()
        self.client.force_login(admin)
        self.client.get(f'/dashboard/editor-invitacion/{evento.id}/')

        response = self.client.post(
            f'/dashboard/editor-invitacion/{evento.id}/plantilla/aplicar/',
            data=json.dumps({'template': 'CUMPLEANOS'}),
            content_type='application/json',
        )

        evento.refresh_from_db()
        diseno = DisenoInvitacion.objects.get(evento=evento)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(evento.tipo_evento, 'CUMPLEANOS')
        self.assertEqual(evento.frase_portada, 'Mi Cumpleanos')
        self.assertEqual(diseno.estado, 'BORRADOR')
        self.assertEqual(diseno.configuracion_borrador['theme']['palette'], 'TERRACOTA')
        self.assertTrue(any(item['type'] == 'ITINERARIO' and item['visible'] for item in response.json()['config']['sections']))

    def test_editor_asigna_asset_a_fondo_de_seccion_en_borrador(self):
        User = get_user_model()
        admin = User.objects.create_superuser(username='dirtec_asset_editor', password='test123')
        evento = crear_evento()
        self.client.force_login(admin)
        self.client.get(f'/dashboard/editor-invitacion/{evento.id}/')
        seccion = SeccionInvitacion.objects.get(evento=evento, tipo='DETALLES')
        asset = AssetInvitacion.objects.create(
            evento=evento,
            tipo='FONDO',
            titulo='Fondo detalles',
            archivo=SimpleUploadedFile('fondo.webp', b'webp-fondo', content_type='image/webp'),
            creado_por=admin,
        )

        response = self.client.post(
            f'/dashboard/editor-invitacion/{evento.id}/assets/asignar/',
            data=json.dumps({
                'assetId': asset.id,
                'destino': 'FONDO_SECCION',
                'sectionId': seccion.id,
            }),
            content_type='application/json',
        )

        seccion.refresh_from_db()
        diseno = DisenoInvitacion.objects.get(evento=evento)
        detalles = next(item for item in diseno.configuracion_borrador['sections'] if item['sectionId'] == seccion.id)
        self.assertEqual(response.status_code, 200)
        self.assertIn('fondo', seccion.fondo.name)
        self.assertEqual(detalles['config']['backgroundAsset']['id'], asset.id)

    def test_preview_real_puede_mostrar_borrador_sin_publicar(self):
        User = get_user_model()
        admin = User.objects.create_superuser(username='dirtec_preview_draft', password='test123')
        evento = crear_evento()
        grupo = Grupoinvitacion.objects.create(evento=evento, nombre_grupo='Preview', tipo='PERSONAL')
        self.client.force_login(admin)
        self.client.get(f'/dashboard/editor-invitacion/{evento.id}/')
        seccion = SeccionInvitacion.objects.get(evento=evento, tipo='DETALLES')
        payload = {
            'theme': {
                'palette': 'BOSQUE',
                'envelopePalette': 'BOSQUE',
                'fontStyle': 'MODERNA',
                'primary': '#123456',
                'secondary': '#ffffff',
                'accent': '#abcdef',
                'background': '#f8f8f8',
            },
            'layout': {'maxWidth': 430, 'sectionSpacing': 'soft', 'animation': 'fade'},
            'sections': [{
                'sectionId': seccion.id,
                'type': seccion.tipo,
                'title': 'Titulo solo borrador',
                'description': 'Texto visible solo en preview.',
                'visible': True,
                'order': 10,
                'config': {
                    'textAlign': 'center',
                    'titleSize': 'medium',
                    'backgroundOpacity': '0.15',
                    'backgroundPosition': 'center center',
                    'textColor': '#123456',
                    'showTextTitle': True,
                },
            }],
        }
        self.client.post(
            f'/dashboard/editor-invitacion/{evento.id}/guardar/',
            data=json.dumps(payload),
            content_type='application/json',
        )

        response = self.client.get(f'/invitacion/{grupo.codigo}/?preview=1&draft=1')

        seccion.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Titulo solo borrador')
        self.assertContains(response, '#123456')
        self.assertNotEqual(seccion.titulo, 'Titulo solo borrador')

    def test_publicar_editor_aplica_asset_de_fondo(self):
        User = get_user_model()
        admin = User.objects.create_superuser(username='dirtec_publica_asset', password='test123')
        evento = crear_evento()
        self.client.force_login(admin)
        self.client.get(f'/dashboard/editor-invitacion/{evento.id}/')
        seccion = SeccionInvitacion.objects.get(evento=evento, tipo='DETALLES')
        asset = AssetInvitacion.objects.create(
            evento=evento,
            tipo='FONDO',
            titulo='Fondo detalles',
            archivo=SimpleUploadedFile('detalles.webp', b'webp-detalles', content_type='image/webp'),
            creado_por=admin,
        )
        payload = {
            'theme': {'palette': 'BOSQUE', 'envelopePalette': 'BOSQUE', 'fontStyle': 'CLASICA'},
            'layout': {'maxWidth': 430, 'sectionSpacing': 'soft', 'animation': 'fade'},
            'sections': [{
                'sectionId': seccion.id,
                'type': seccion.tipo,
                'title': 'Detalles',
                'description': '',
                'visible': True,
                'order': 10,
                'config': {
                    'textAlign': 'center',
                    'titleSize': 'medium',
                    'backgroundOpacity': '0.15',
                    'backgroundPosition': 'center center',
                    'textColor': '',
                    'showTextTitle': True,
                    'backgroundAsset': {'id': asset.id},
                },
            }],
        }

        response = self.client.post(
            f'/dashboard/editor-invitacion/{evento.id}/publicar/',
            data=json.dumps(payload),
            content_type='application/json',
        )

        seccion.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertIn('detalles', seccion.fondo.name)

    def test_editor_guarda_contenido_rapido_del_evento(self):
        User = get_user_model()
        admin = User.objects.create_superuser(username='dirtec_contenido_editor', password='test123')
        evento = crear_evento()
        self.client.force_login(admin)
        payload = {
            'eventName': 'Boda actualizada',
            'mainName': 'Fernanda',
            'secondaryName': 'Diego',
            'mainLabel': 'Novia',
            'secondaryLabel': 'Novio',
            'showSecondaryName': True,
            'coverPhrase': 'Nuestra boda',
            'generalMessage': 'Gracias por acompanarnos.',
            'invitationTitle': 'Con mucho amor',
            'invitationText': 'Nos encantara verte.',
            'detailsTitle': 'Ceremonia y fiesta',
            'detailsText': 'Todo en un mismo lugar.',
            'rsvpTitle': 'Confirma',
            'rsvpText': 'Tu respuesta nos ayuda.',
            'ceremonyDate': '2026-11-21T17:30',
            'ceremonyPlace': 'Parroquia San Francisco',
            'ceremonyAddress': 'Calle templo 123',
            'ceremonyMapUrl': 'https://maps.google.com/',
            'ceremonyMapEmbed': '<iframe src="https://www.google.com/maps/embed?pb=test"></iframe>',
            'receptionDate': '2026-11-21T20:00',
            'receptionPlace': 'Jardin Cisneros',
            'receptionAddress': 'Salon 456',
            'receptionMapUrl': 'https://maps.google.com/',
            'receptionMapEmbed': '<iframe src="https://www.google.com/maps/embed?pb=test"></iframe>',
            'dressCode': 'Formal',
            'dressCodeText': 'Evitar blanco.',
            'sharedAlbumTitle': 'Comparte tus fotos',
            'sharedAlbumText': 'Sube tus recuerdos.',
            'sharedAlbumUrl': 'https://drive.google.com/',
            'showAlbum': True,
            'showMenu': True,
            'showGifts': True,
            'showMaps': True,
            'showSharedAlbum': True,
        }

        response = self.client.post(
            f'/dashboard/editor-invitacion/{evento.id}/contenido/guardar/',
            data=json.dumps(payload),
            content_type='application/json',
        )

        evento.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(evento.nombre_evento, 'Boda actualizada')
        self.assertEqual(evento.nombre_principal, 'Fernanda')
        self.assertEqual(evento.lugar_fiesta, 'Jardin Cisneros')
        self.assertTrue(evento.mostrar_album_compartido)
        self.assertIn('content', response.json())

    def test_editor_crea_y_elimina_items_de_contenido_rapido(self):
        User = get_user_model()
        admin = User.objects.create_superuser(username='dirtec_items_editor', password='test123')
        evento = crear_evento()
        self.client.force_login(admin)

        persona_response = self.client.post(
            f'/dashboard/editor-invitacion/{evento.id}/contenido/item/',
            data=json.dumps({
                'collection': 'people',
                'section': 'PADRES_NOVIA',
                'label': 'Mama',
                'name': 'Maria Lopez',
                'order': 1,
                'visible': True,
            }),
            content_type='application/json',
        )
        regalo_response = self.client.post(
            f'/dashboard/editor-invitacion/{evento.id}/contenido/item/',
            data=json.dumps({
                'collection': 'gifts',
                'type': 'DEPOSITO',
                'name': 'Deposito bancario',
                'bank': 'BBVA',
                'holder': 'Fernanda Flores',
                'account': '123',
                'clabe': '456',
                'visible': True,
            }),
            content_type='application/json',
        )
        itinerario_response = self.client.post(
            f'/dashboard/editor-invitacion/{evento.id}/contenido/item/',
            data=json.dumps({
                'collection': 'itinerary',
                'time': '18:00',
                'title': 'Ceremonia',
                'description': 'Templo',
                'icon': 'ceremonia',
                'order': 1,
                'visible': True,
            }),
            content_type='application/json',
        )

        self.assertEqual(persona_response.status_code, 200)
        self.assertEqual(regalo_response.status_code, 200)
        self.assertEqual(itinerario_response.status_code, 200)
        self.assertEqual(PersonaCeremonia.objects.filter(evento=evento).count(), 1)
        self.assertEqual(EnlaceRegalo.objects.filter(evento=evento).count(), 1)
        self.assertEqual(ItinerarioEvento.objects.filter(evento=evento).count(), 1)

        persona_id = PersonaCeremonia.objects.get(evento=evento).id
        delete_response = self.client.post(
            f'/dashboard/editor-invitacion/{evento.id}/contenido/item/',
            data=json.dumps({'collection': 'people', 'id': persona_id, 'action': 'delete'}),
            content_type='application/json',
        )

        self.assertEqual(delete_response.status_code, 200)
        self.assertFalse(PersonaCeremonia.objects.filter(evento=evento).exists())

    def test_editor_crea_grupo_personal_con_mesa_y_qr(self):
        User = get_user_model()
        admin = User.objects.create_superuser(username='dirtec_guest_group_editor', password='test123')
        evento = crear_evento()
        mesa = Mesa.objects.create(evento=evento, nombre='Mesa 1', capacidad=8)
        self.client.force_login(admin)

        response = self.client.post(
            f'/dashboard/editor-invitacion/{evento.id}/invitados/grupo/',
            data=json.dumps({
                'name': 'Carlos Perez',
                'type': 'PERSONAL',
                'maxGuests': 1,
                'extraAllowed': 2,
                'phone': '3312345678',
                'email': 'carlos@example.com',
                'tableId': mesa.id,
            }),
            content_type='application/json',
        )

        grupo = Grupoinvitacion.objects.get(evento=evento, nombre_grupo='Carlos Perez')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(grupo.tipo, 'PERSONAL')
        self.assertEqual(grupo.cantidad_extra_permitida, 2)
        self.assertTrue(AsignacionMesa.objects.filter(mesa=mesa, grupo_invitacion=grupo).exists())
        grupo_json = response.json()['guests']['groups'][0]
        self.assertIn('/invitacion/', grupo_json['link'])
        self.assertIn('api.qrserver.com', grupo_json['qrUrl'])

    def test_editor_crea_familia_e_invitado_con_tipo_y_mesa(self):
        User = get_user_model()
        admin = User.objects.create_superuser(username='dirtec_family_editor', password='test123')
        evento = crear_evento()
        mesa = Mesa.objects.create(evento=evento, nombre='Mesa Familia', capacidad=8)
        self.client.force_login(admin)

        grupo_response = self.client.post(
            f'/dashboard/editor-invitacion/{evento.id}/invitados/grupo/',
            data=json.dumps({
                'name': 'Perez',
                'type': 'FAMILIAR',
                'maxGuests': 3,
                'extraAllowed': 0,
                'familyGuests': 'Ana Perez | ADULTO\nLuis Perez | NINO',
            }),
            content_type='application/json',
        )
        grupo = Grupoinvitacion.objects.get(evento=evento, nombre_grupo='Perez')
        invitado = grupo.invitados.get(nombre='Luis Perez')

        edit_response = self.client.post(
            f'/dashboard/editor-invitacion/{evento.id}/invitados/persona/',
            data=json.dumps({
                'id': invitado.id,
                'groupId': grupo.id,
                'name': 'Luis',
                'lastName': 'Perez',
                'type': 'NINO',
                'tableId': mesa.id,
                'menuInfantil': True,
            }),
            content_type='application/json',
        )

        invitado.refresh_from_db()
        self.assertEqual(grupo_response.status_code, 200)
        self.assertEqual(edit_response.status_code, 200)
        self.assertEqual(grupo.invitados.count(), 2)
        self.assertEqual(invitado.tipo_persona, 'NINO')
        self.assertTrue(invitado.menu_infantil)
        self.assertTrue(AsignacionMesa.objects.filter(mesa=mesa, invitado=invitado).exists())

    def test_editor_importa_invitados_desde_csv(self):
        User = get_user_model()
        admin = User.objects.create_superuser(username='dirtec_import_editor', password='test123')
        evento = crear_evento()
        self.client.force_login(admin)
        archivo = SimpleUploadedFile(
            'invitados.csv',
            (
                'grupo,tipo_grupo,nombre,tipo_persona,extras,extra,telefono,correo\n'
                'Perez,FAMILIAR,Ana Perez,ADULTO,0,,3311111111,ana@example.com\n'
                'Perez,FAMILIAR,Luis Perez,NINO,0,,3311111111,luis@example.com\n'
                'Carlos,PERSONAL,Carlos,ADULTO,1,,3322222222,carlos@example.com\n'
                'Carlos,PERSONAL,Acompanante Carlos,NINO,1,si,,\n'
            ).encode('utf-8'),
            content_type='text/csv',
        )

        response = self.client.post(
            f'/dashboard/editor-invitacion/{evento.id}/invitados/importar/',
            data={'archivo': archivo},
        )

        familia = Grupoinvitacion.objects.get(evento=evento, nombre_grupo='Perez')
        personal = Grupoinvitacion.objects.get(evento=evento, nombre_grupo='Carlos')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(familia.invitados.count(), 2)
        self.assertEqual(familia.invitados.get(nombre='Luis Perez').tipo_persona, 'NINO')
        self.assertEqual(personal.tipo, 'PERSONAL')
        self.assertEqual(personal.cantidad_extra_permitida, 1)
        self.assertEqual(personal.invitados.get(nombre='Acompanante Carlos').tipo_persona, 'NINO')
        personal_json = next(item for item in response.json()['guests']['groups'] if item['name'] == 'Carlos')
        self.assertEqual(personal_json['places'], 2)

    def test_dashboard_guarda_portadas_de_ceremonia_y_fiesta(self):
        User = get_user_model()
        admin = User.objects.create_superuser(username='dirtec_lugares', password='test123')
        evento = crear_evento()
        self.client.force_login(admin)

        response = self.client.post('/dashboard/', {
            'accion': 'personalizar_evento',
            'evento_id': evento.id,
            'lugar_misa': 'Parroquia central',
            'lugar_fiesta': 'Salon principal',
            'mostrar_mapa': 'on',
            'foto_ceremonia': SimpleUploadedFile('ceremonia.gif', b'gif-ceremonia', content_type='image/gif'),
            'foto_recepcion': SimpleUploadedFile('recepcion.gif', b'gif-recepcion', content_type='image/gif'),
        })

        evento.refresh_from_db()
        self.assertEqual(response.status_code, 302)
        self.assertTrue(evento.foto_ceremonia.name.endswith('.gif'))
        self.assertTrue(evento.foto_recepcion.name.endswith('.gif'))

    def test_dashboard_elimina_portadas_de_ceremonia_y_fiesta(self):
        User = get_user_model()
        admin = User.objects.create_superuser(username='dirtec_lugares_eliminar', password='test123')
        evento = crear_evento()
        evento.foto_ceremonia = SimpleUploadedFile('ceremonia.gif', b'gif-ceremonia', content_type='image/gif')
        evento.foto_recepcion = SimpleUploadedFile('recepcion.gif', b'gif-recepcion', content_type='image/gif')
        evento.save()
        self.client.force_login(admin)

        response = self.client.post('/dashboard/', {
            'accion': 'personalizar_evento',
            'evento_id': evento.id,
            'eliminar_foto_ceremonia': 'on',
            'eliminar_foto_recepcion': 'on',
        })

        evento.refresh_from_db()
        self.assertEqual(response.status_code, 302)
        self.assertFalse(evento.foto_ceremonia)
        self.assertFalse(evento.foto_recepcion)

    def test_dashboard_elimina_medios_y_fondos_opcionales(self):
        User = get_user_model()
        admin = User.objects.create_superuser(username='dirtec_media_eliminar', password='test123')
        evento = crear_evento()
        evento.foto_portada = SimpleUploadedFile('portada.gif', b'gif-portada', content_type='image/gif')
        evento.logo_portada = SimpleUploadedFile('logo.png', b'png-logo', content_type='image/png')
        evento.sello_sobre = SimpleUploadedFile('sello.png', b'png-sello', content_type='image/png')
        evento.cancion = SimpleUploadedFile('cancion.mp3', b'mp3-cancion', content_type='audio/mpeg')
        evento.dress_code_permitido_imagen = SimpleUploadedFile('permitido.png', b'png-permitido', content_type='image/png')
        evento.dress_code_prohibido_imagen = SimpleUploadedFile('prohibido.png', b'png-prohibido', content_type='image/png')
        evento.fondo_detalles = SimpleUploadedFile('detalles.png', b'png-detalles', content_type='image/png')
        evento.fondo_rsvp = SimpleUploadedFile('rsvp.png', b'png-rsvp', content_type='image/png')
        evento.save()
        self.client.force_login(admin)

        response = self.client.post('/dashboard/', {
            'accion': 'personalizar_evento',
            'evento_id': evento.id,
            'eliminar_foto_portada': 'on',
            'eliminar_logo_portada': 'on',
            'eliminar_sello_sobre': 'on',
            'eliminar_cancion': 'on',
            'eliminar_dress_code_permitido_imagen': 'on',
            'eliminar_dress_code_prohibido_imagen': 'on',
            'eliminar_fondo_detalles': 'on',
            'eliminar_fondo_rsvp': 'on',
        })

        evento.refresh_from_db()
        self.assertEqual(response.status_code, 302)
        self.assertFalse(evento.foto_portada)
        self.assertFalse(evento.logo_portada)
        self.assertFalse(evento.sello_sobre)
        self.assertFalse(evento.cancion)
        self.assertFalse(evento.dress_code_permitido_imagen)
        self.assertFalse(evento.dress_code_prohibido_imagen)
        self.assertFalse(evento.fondo_detalles)
        self.assertFalse(evento.fondo_rsvp)

    def test_invitacion_renderiza_fondo_de_seccion_video(self):
        evento = crear_evento()
        grupo = Grupoinvitacion.objects.create(
            evento=evento,
            nombre_grupo='Familia Perez',
            tipo='FAMILIAR',
        )
        seccion = SeccionInvitacion.objects.create(
            evento=evento,
            tipo='DETALLES',
            titulo='Detalles del evento',
            descripcion='Ubicaciones y horarios.',
            orden=30,
            activa=True,
        )
        seccion.fondo = SimpleUploadedFile('detalles.mp4', b'video-detalles', content_type='video/mp4')
        seccion.imagen_titulo = SimpleUploadedFile('titulo.mp4', b'video-titulo', content_type='video/mp4')
        seccion.save()

        response = self.client.get(f'/invitacion/{grupo.codigo}/')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'panel-bg-video')
        self.assertContains(response, '/media/secciones/fondos/')
        self.assertContains(response, '/media/secciones/titulos/')
        self.assertContains(response, '.mp4', count=2)
        self.assertNotContains(response, "background-image: url('/media/secciones/fondos/")

    def test_personalizacion_activa_album_compartido_desde_switch(self):
        User = get_user_model()
        admin = User.objects.create_superuser(username='dirtec_album_compartido', password='test123')
        evento = crear_evento()
        self.client.force_login(admin)

        response = self.client.post('/dashboard/', {
            'accion': 'personalizar_evento',
            'evento_id': evento.id,
            'mostrar_album_compartido': 'on',
            'titulo_album_compartido': 'Comparte la fiesta',
            'texto_album_compartido': 'Sube tus fotos y videos aqui.',
            'link_album_compartido': 'https://drive.google.com/drive/folders/demo',
        })

        evento.refresh_from_db()
        seccion = SeccionInvitacion.objects.get(evento=evento, tipo='ALBUM_COMPARTIDO')
        self.assertEqual(response.status_code, 302)
        self.assertTrue(evento.mostrar_album_compartido)
        self.assertTrue(seccion.activa)
        self.assertEqual(seccion.titulo, 'Comparte la fiesta')


class DashboardReportesTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.dashboard_user = User.objects.create_superuser(username='dashboard_admin', password='test123')
        self.client.force_login(self.dashboard_user)

    def test_dashboard_requiere_login(self):
        self.client.logout()
        response = self.client.get('/dashboard/')

        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response['Location'])

    def test_planner_solo_ve_eventos_asignados_de_su_empresa(self):
        User = get_user_model()
        user = User.objects.create_user(username='planner_cisneros', password='test123')
        empresa = EmpresaSuscriptora.objects.create(nombre_comercial='Casa Cisneros', slug='casa-cisneros')
        otra_empresa = EmpresaSuscriptora.objects.create(nombre_comercial='Otro Salon', slug='otro-salon')
        MembresiaEmpresa.objects.create(empresa=empresa, usuario=user, rol='WEDDING_PLANNER')
        evento_visible = crear_evento()
        evento_visible.nombre_evento = 'Evento Casa Cisneros'
        evento_visible.empresa = empresa
        evento_visible.wedding_planner = user
        evento_visible.save()
        evento_no_asignado = crear_evento()
        evento_no_asignado.nombre_evento = 'Evento Casa No Asignado'
        evento_no_asignado.empresa = empresa
        evento_no_asignado.save()
        evento_oculto = crear_evento()
        evento_oculto.nombre_evento = 'Evento Ajeno'
        evento_oculto.empresa = otra_empresa
        evento_oculto.save()
        self.client.force_login(user)

        response = self.client.get('/dashboard/')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Evento Casa Cisneros')
        self.assertNotContains(response, 'Evento Casa No Asignado')
        self.assertNotContains(response, 'Evento Ajeno')

    def test_dashboard_crea_catalogos_de_empresa(self):
        User = get_user_model()
        empresa = EmpresaSuscriptora.objects.create(nombre_comercial='Casa Cisneros', slug='casa-cisneros')
        admin_empresa = User.objects.create_user(username='admin_cisneros', password='test123')
        MembresiaEmpresa.objects.create(
            empresa=empresa,
            usuario=admin_empresa,
            rol='ADMIN_EMPRESA',
            puede_gestionar_catalogos=True,
        )
        evento = crear_evento()
        evento.empresa = empresa
        evento.save()
        self.client.force_login(admin_empresa)

        self.client.post('/dashboard/', {
            'accion': 'agregar_sede_empresa',
            'evento_id': evento.id,
            'nombre_sede': 'Jardin Cisneros',
            'tipo_sede': 'JARDIN',
            'capacidad_minima': '80',
            'capacidad_maxima': '250',
            'precio_base_sede': '50000',
        })
        self.client.post('/dashboard/', {
            'accion': 'agregar_proveedor_empresa',
            'evento_id': evento.id,
            'nombre_proveedor': 'Banquetes Cisneros',
            'tipo_proveedor': 'BANQUETE',
            'telefono_proveedor': '555',
        })
        response = self.client.post('/dashboard/', {
            'accion': 'agregar_paquete_empresa',
            'evento_id': evento.id,
            'nombre_paquete': 'Paquete Jardín',
            'personas_paquete': '150',
            'precio_base_paquete': '120000',
        })

        self.assertEqual(response.status_code, 302)
        self.assertTrue(SedeEvento.objects.filter(empresa=empresa, nombre='Jardin Cisneros').exists())
        self.assertTrue(Proveedor.objects.filter(empresa=empresa, nombre_comercial='Banquetes Cisneros').exists())
        self.assertTrue(PaqueteBoda.objects.filter(empresa=empresa, nombre='Paquete Jardín').exists())

    def test_dashboard_avanzado_edita_y_elimina_catalogos_de_empresa(self):
        User = get_user_model()
        empresa = EmpresaSuscriptora.objects.create(nombre_comercial='Casa Cisneros', slug='casa-cisneros')
        admin_empresa = User.objects.create_user(username='admin_catalogos_avanzado', password='test123')
        MembresiaEmpresa.objects.create(
            empresa=empresa,
            usuario=admin_empresa,
            rol='ADMIN_EMPRESA',
            puede_gestionar_catalogos=True,
        )
        evento = crear_evento()
        evento.empresa = empresa
        evento.save()
        sede = SedeEvento.objects.create(empresa=empresa, nombre='Salon Norte', capacidad_maxima=120)
        proveedor = Proveedor.objects.create(empresa=empresa, nombre_comercial='Foto Luz', tipo_proveedor='FOTOGRAFIA')
        paquete = PaqueteBoda.objects.create(empresa=empresa, nombre='Paquete Basico', numero_personas_incluidas=80)
        self.client.force_login(admin_empresa)

        response = self.client.get(f'/dashboard/?evento={evento.id}')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Editar sede')
        self.assertContains(response, 'Editar proveedor')
        self.assertContains(response, 'Editar paquete')

        self.client.post('/dashboard/', {
            'accion': 'editar_sede_empresa',
            'evento_id': evento.id,
            'sede_id': sede.id,
            'nombre_sede': 'Jardin Norte',
            'tipo_sede': 'JARDIN',
            'capacidad_minima': '60',
            'capacidad_maxima': '180',
            'precio_base_sede': '70000',
            'direccion_sede': 'Av Norte',
            'descripcion_sede': 'Jardin remodelado',
            'activa_sede': 'on',
        })
        self.client.post('/dashboard/', {
            'accion': 'editar_proveedor_empresa',
            'evento_id': evento.id,
            'proveedor_id': proveedor.id,
            'nombre_proveedor': 'Foto Luz Premium',
            'tipo_proveedor': 'VIDEO',
            'contacto_proveedor': 'Luis',
            'telefono_proveedor': '555',
            'correo_proveedor': 'luis@example.com',
            'visible_wedding_planners_proveedor': 'on',
            'activo_proveedor': 'on',
        })
        self.client.post('/dashboard/', {
            'accion': 'editar_paquete_empresa',
            'evento_id': evento.id,
            'paquete_id': paquete.id,
            'nombre_paquete': 'Paquete Premium',
            'personas_paquete': '160',
            'precio_base_paquete': '150000',
            'descripcion_paquete': 'Salon y coordinacion',
            'activo_paquete': 'on',
        })

        sede.refresh_from_db()
        proveedor.refresh_from_db()
        paquete.refresh_from_db()
        self.assertEqual(sede.nombre, 'Jardin Norte')
        self.assertEqual(sede.capacidad_maxima, 180)
        self.assertEqual(proveedor.nombre_comercial, 'Foto Luz Premium')
        self.assertEqual(proveedor.tipo_proveedor, 'VIDEO')
        self.assertEqual(paquete.nombre, 'Paquete Premium')
        self.assertEqual(paquete.numero_personas_incluidas, 160)

        self.client.post('/dashboard/', {'accion': 'eliminar_sede_empresa', 'evento_id': evento.id, 'sede_id': sede.id})
        self.client.post('/dashboard/', {'accion': 'eliminar_proveedor_empresa', 'evento_id': evento.id, 'proveedor_id': proveedor.id})
        self.client.post('/dashboard/', {'accion': 'eliminar_paquete_empresa', 'evento_id': evento.id, 'paquete_id': paquete.id})
        self.assertFalse(SedeEvento.objects.filter(id=sede.id).exists())
        self.assertFalse(Proveedor.objects.filter(id=proveedor.id).exists())
        self.assertFalse(PaqueteBoda.objects.filter(id=paquete.id).exists())

    def test_dashboard_empresa_bloquea_catalogos_sin_permiso(self):
        User = get_user_model()
        empresa = EmpresaSuscriptora.objects.create(nombre_comercial='Casa Cisneros', slug='casa-cisneros')
        ventas = User.objects.create_user(username='ventas_catalogos', password='test123')
        MembresiaEmpresa.objects.create(empresa=empresa, usuario=ventas, rol='VENTAS')
        self.client.force_login(ventas)
        self.client.raise_request_exception = False

        response = self.client.post('/dashboard/empresa/', {
            'accion': 'crear_sede',
            'empresa_id': empresa.id,
            'nombre_sede': 'Jardin sin permiso',
        })

        self.assertEqual(response.status_code, 403)
        self.assertFalse(SedeEvento.objects.filter(empresa=empresa, nombre='Jardin sin permiso').exists())
        self.assertTrue(
            RegistroAuditoria.objects.filter(
                usuario=ventas,
                empresa=empresa,
                accion='ACCESO_DENEGADO_DASHBOARD',
                valores_nuevos__accion_solicitada='crear_sede',
            ).exists()
        )

    def test_dashboard_empresa_bloquea_usuarios_sin_permiso(self):
        User = get_user_model()
        empresa = EmpresaSuscriptora.objects.create(nombre_comercial='Casa Cisneros', slug='casa-cisneros')
        ventas = User.objects.create_user(username='ventas_usuarios', password='test123')
        MembresiaEmpresa.objects.create(empresa=empresa, usuario=ventas, rol='VENTAS')
        self.client.force_login(ventas)
        self.client.raise_request_exception = False

        response = self.client.post('/dashboard/empresa/', {
            'accion': 'crear_cliente',
            'empresa_id': empresa.id,
            'username_usuario': 'cliente_sin_permiso',
            'password_usuario': 'test123',
        })

        self.assertEqual(response.status_code, 403)
        self.assertFalse(User.objects.filter(username='cliente_sin_permiso').exists())
        self.assertTrue(
            RegistroAuditoria.objects.filter(
                usuario=ventas,
                empresa=empresa,
                accion='ACCESO_DENEGADO_DASHBOARD',
                valores_nuevos__accion_solicitada='crear_cliente',
            ).exists()
        )

    def test_usuario_empresa_no_ve_enlaces_admin_en_vistas_operativas(self):
        User = get_user_model()
        empresa = EmpresaSuscriptora.objects.create(nombre_comercial='Casa Cisneros', slug='casa-cisneros')
        admin_empresa = User.objects.create_user(username='admin_sin_adminlink', password='test123')
        MembresiaEmpresa.objects.create(empresa=empresa, usuario=admin_empresa, rol='ADMIN_EMPRESA')
        evento = crear_evento()
        evento.empresa = empresa
        evento.save()
        self.client.force_login(admin_empresa)

        urls = [
            f'/dashboard/?evento={evento.id}',
            f'/dashboard/empresa/?empresa={empresa.id}',
            f'/dashboard/calendario/?evento={evento.id}',
            f'/dashboard/mesas/?evento={evento.id}',
        ]
        for url in urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)
                self.assertNotContains(response, 'href="/admin')
                self.assertNotContains(response, '/admin/')

    def test_admin_empresa_gestiona_mesas_sin_admin_django(self):
        User = get_user_model()
        empresa = EmpresaSuscriptora.objects.create(nombre_comercial='Casa Cisneros', slug='casa-cisneros')
        admin_empresa = User.objects.create_user(username='admin_mesas', password='test123')
        MembresiaEmpresa.objects.create(empresa=empresa, usuario=admin_empresa, rol='ADMIN_EMPRESA')
        evento = crear_evento()
        evento.empresa = empresa
        evento.save()
        grupo = Grupoinvitacion.objects.create(evento=evento, nombre_grupo='Familia Perez', tipo='FAMILIAR')
        invitado = Invitado.objects.create(grupo=grupo, nombre='Ana', tipo_persona='ADULTO')
        self.client.force_login(admin_empresa)

        response = self.client.post('/dashboard/mesas/', {
            'accion': 'crear_mesa',
            'evento_id': evento.id,
            'nombre_mesa': 'Mesa Familia',
            'numero_mesa': '1',
            'tipo_mesa': 'RECTANGULAR',
            'capacidad_mesa': '8',
        })
        mesa = Mesa.objects.get(evento=evento, nombre='Mesa Familia')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(mesa.tipo, 'RECTANGULAR')

        response = self.client.post('/dashboard/mesas/', {
            'accion': 'asignar_mesa',
            'evento_id': evento.id,
            'mesa_id': mesa.id,
            'invitado_id': invitado.id,
            'numero_asiento': '2',
        })
        asignacion = AsignacionMesa.objects.get(mesa=mesa, invitado=invitado)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(asignacion.numero_asiento, 2)

        response = self.client.get(f'/dashboard/mesas/?evento={evento.id}')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Mesa Familia')
        self.assertNotContains(response, '/admin/')

        self.client.post('/dashboard/mesas/', {
            'accion': 'eliminar_asignacion',
            'evento_id': evento.id,
            'asignacion_id': asignacion.id,
        })
        self.assertFalse(AsignacionMesa.objects.filter(id=asignacion.id).exists())

        self.client.post('/dashboard/mesas/', {
            'accion': 'eliminar_mesa',
            'evento_id': evento.id,
            'mesa_id': mesa.id,
        })
        self.assertFalse(Mesa.objects.filter(id=mesa.id).exists())

    def test_dashboard_avanzado_bloquea_catalogos_sin_permiso(self):
        User = get_user_model()
        empresa = EmpresaSuscriptora.objects.create(nombre_comercial='Casa Cisneros', slug='casa-cisneros')
        ventas = User.objects.create_user(username='ventas_avanzado', password='test123')
        MembresiaEmpresa.objects.create(empresa=empresa, usuario=ventas, rol='VENTAS')
        evento = crear_evento()
        evento.empresa = empresa
        evento.save()
        self.client.force_login(ventas)
        self.client.raise_request_exception = False

        response = self.client.post('/dashboard/', {
            'accion': 'agregar_sede_empresa',
            'evento_id': evento.id,
            'nombre_sede': 'Sede avanzada sin permiso',
        })

        self.assertEqual(response.status_code, 403)
        self.assertFalse(SedeEvento.objects.filter(empresa=empresa, nombre='Sede avanzada sin permiso').exists())
        self.assertTrue(
            RegistroAuditoria.objects.filter(
                usuario=ventas,
                empresa=empresa,
                evento=evento,
                accion='ACCESO_DENEGADO_DASHBOARD',
                valores_nuevos__accion_solicitada='agregar_sede_empresa',
            ).exists()
        )

    def test_dashboard_avanzado_bloquea_edicion_catalogos_sin_permiso(self):
        User = get_user_model()
        empresa = EmpresaSuscriptora.objects.create(nombre_comercial='Casa Cisneros', slug='casa-cisneros')
        planner = User.objects.create_user(username='planner_sin_catalogos', password='test123')
        MembresiaEmpresa.objects.create(empresa=empresa, usuario=planner, rol='WEDDING_PLANNER')
        evento = crear_evento()
        evento.empresa = empresa
        evento.wedding_planner = planner
        evento.save()
        sede = SedeEvento.objects.create(empresa=empresa, nombre='Salon protegido')
        self.client.force_login(planner)
        self.client.raise_request_exception = False

        response = self.client.post('/dashboard/', {
            'accion': 'editar_sede_empresa',
            'evento_id': evento.id,
            'sede_id': sede.id,
            'nombre_sede': 'Cambio no permitido',
        })

        sede.refresh_from_db()
        self.assertEqual(response.status_code, 403)
        self.assertEqual(sede.nombre, 'Salon protegido')

    def test_admin_empresa_crea_usuario_y_asigna_planner(self):
        User = get_user_model()
        empresa = EmpresaSuscriptora.objects.create(nombre_comercial='Casa Cisneros', slug='casa-cisneros')
        admin_empresa = User.objects.create_user(username='admin_cisneros', password='test123')
        MembresiaEmpresa.objects.create(empresa=empresa, usuario=admin_empresa, rol='ADMIN_EMPRESA')
        evento = crear_evento()
        evento.empresa = empresa
        evento.save()
        self.client.force_login(admin_empresa)

        response = self.client.post('/dashboard/', {
            'accion': 'crear_usuario_empresa',
            'evento_id': evento.id,
            'username_usuario': 'planner_ana',
            'password_usuario': 'temporal123',
            'first_name_usuario': 'Ana',
            'last_name_usuario': 'Lopez',
            'email_usuario': 'ana@example.com',
            'rol_usuario': 'WEDDING_PLANNER',
            'activo_usuario': 'on',
        })

        planner = User.objects.get(username='planner_ana')
        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            MembresiaEmpresa.objects.filter(
                empresa=empresa,
                usuario=planner,
                rol='WEDDING_PLANNER',
                activo=True,
            ).exists()
        )

        response = self.client.post('/dashboard/', {
            'accion': 'asignar_planner_evento',
            'evento_id': evento.id,
            'planner_id': planner.id,
        })

        evento.refresh_from_db()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(evento.wedding_planner, planner)

    def test_admin_empresa_crea_planner_con_login_funcional(self):
        User = get_user_model()
        empresa = EmpresaSuscriptora.objects.create(nombre_comercial='Casa Cisneros', slug='casa-cisneros')
        admin_empresa = User.objects.create_user(username='admin_cisneros_login', password='test123')
        MembresiaEmpresa.objects.create(empresa=empresa, usuario=admin_empresa, rol='ADMIN_EMPRESA')
        self.client.force_login(admin_empresa)

        response = self.client.post('/empresa/casa-cisneros/dashboard/', {
            'accion': 'crear_planner',
            'username_usuario': 'planner_login',
            'password_usuario': 'temporal123',
            'first_name_usuario': 'Fer',
            'last_name_usuario': 'Lopez',
            'email_usuario': 'planner@example.com',
            'rol_usuario': 'WEDDING_PLANNER',
            'activo_usuario': 'on',
        })

        planner = User.objects.get(username='planner_login')
        self.assertEqual(response.status_code, 302)
        self.assertTrue(planner.check_password('temporal123'))
        self.assertTrue(
            MembresiaEmpresa.objects.filter(
                empresa=empresa,
                usuario=planner,
                rol='WEDDING_PLANNER',
                activo=True,
            ).exists()
        )

        self.client.logout()
        self.assertTrue(self.client.login(username='planner_login', password='temporal123'))
        follow = self.client.get('/redirigir/')
        self.assertEqual(follow.status_code, 302)
        self.assertEqual(follow['Location'], '/empresa/casa-cisneros/wedding-planner/dashboard/')

    def test_admin_empresa_elimina_acceso_desde_dashboard_avanzado(self):
        User = get_user_model()
        empresa = EmpresaSuscriptora.objects.create(nombre_comercial='Casa Cisneros', slug='casa-cisneros')
        admin_empresa = User.objects.create_user(username='admin_elimina', password='test123')
        planner = User.objects.create_user(username='planner_eliminar', password='test123')
        MembresiaEmpresa.objects.create(empresa=empresa, usuario=admin_empresa, rol='ADMIN_EMPRESA')
        membresia = MembresiaEmpresa.objects.create(empresa=empresa, usuario=planner, rol='WEDDING_PLANNER')
        evento = crear_evento()
        evento.empresa = empresa
        evento.save()
        self.client.force_login(admin_empresa)

        response = self.client.post('/dashboard/', {
            'accion': 'eliminar_membresia_empresa',
            'evento_id': evento.id,
            'membresia_id': membresia.id,
        })

        self.assertEqual(response.status_code, 302)
        self.assertFalse(MembresiaEmpresa.objects.filter(id=membresia.id).exists())
        self.assertFalse(User.objects.filter(username='planner_eliminar').exists())

    def test_dashboards_por_rol_muestran_panel_correcto(self):
        User = get_user_model()
        dirtec = User.objects.create_superuser(username='dirtec', password='test123')
        empresa = EmpresaSuscriptora.objects.create(nombre_comercial='Casa Cisneros', slug='casa-cisneros')
        admin_empresa = User.objects.create_user(username='admin_cisneros', password='test123')
        planner = User.objects.create_user(username='planner_cisneros', password='test123')
        MembresiaEmpresa.objects.create(empresa=empresa, usuario=admin_empresa, rol='ADMIN_EMPRESA')
        MembresiaEmpresa.objects.create(empresa=empresa, usuario=planner, rol='WEDDING_PLANNER')
        evento_asignado = crear_evento()
        evento_asignado.nombre_evento = 'Evento Planner Visible'
        evento_asignado.empresa = empresa
        evento_asignado.wedding_planner = planner
        evento_asignado.save()
        evento_no_asignado = crear_evento()
        evento_no_asignado.nombre_evento = 'Evento Planner Oculto'
        evento_no_asignado.empresa = empresa
        evento_no_asignado.save()

        self.client.force_login(dirtec)
        response = self.client.get('/dashboard/dirtec/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Control comercial SaaS')

        self.client.force_login(admin_empresa)
        response = self.client.get('/dashboard/profesional/')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], '/empresa/casa-cisneros/dashboard/')
        response = self.client.get('/dashboard/empresa/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Dashboard empresarial')

        self.client.force_login(planner)
        response = self.client.get('/dashboard/profesional/')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], '/empresa/casa-cisneros/wedding-planner/dashboard/')
        response = self.client.get('/dashboard/planner/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Evento Planner Visible')
        self.assertNotContains(response, 'Evento Planner Oculto')

    def test_planner_asigna_proveedor_visible_a_evento_asignado(self):
        User = get_user_model()
        empresa = EmpresaSuscriptora.objects.create(nombre_comercial='Casa Cisneros', slug='casa-cisneros')
        planner = User.objects.create_user(username='planner_proveedor', password='test123')
        MembresiaEmpresa.objects.create(empresa=empresa, usuario=planner, rol='WEDDING_PLANNER')
        evento = crear_evento()
        evento.empresa = empresa
        evento.wedding_planner = planner
        evento.save()
        proveedor = Proveedor.objects.create(
            empresa=empresa,
            nombre_comercial='Banquetes Cisneros',
            tipo_proveedor='BANQUETE',
            contacto_operativo='Laura Operacion',
            telefono_operativo='555123',
            visible_para_wedding_planners=True,
        )
        self.client.force_login(planner)

        response = self.client.post('/empresa/casa-cisneros/wedding-planner/dashboard/', {
            'accion': 'asignar_proveedor_evento',
            'evento_id': evento.id,
            'proveedor_id': proveedor.id,
            'nombre_servicio': 'Banquete cena',
            'fecha_servicio': '2026-12-15',
            'hora_inicio_servicio': '20:00',
            'hora_fin_servicio': '23:00',
            'lugar_servicio': 'Salon principal',
            'descripcion_servicio': 'Cena para 180 personas',
        })

        servicio = ServicioEvento.objects.get(evento=evento, proveedor=proveedor)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], '/empresa/casa-cisneros/wedding-planner/dashboard/#proveedores')
        self.assertEqual(servicio.nombre_servicio, 'Banquete cena')
        self.assertEqual(servicio.estado, 'SOLICITADO')
        self.assertEqual(servicio.costo_total, 0)
        self.assertTrue(
            RegistroAuditoria.objects.filter(
                empresa=empresa,
                evento=evento,
                accion='ASIGNAR_PROVEEDOR_PLANNER',
            ).exists()
        )

    def test_planner_no_asigna_proveedor_oculto_o_de_otra_empresa(self):
        User = get_user_model()
        empresa = EmpresaSuscriptora.objects.create(nombre_comercial='Casa Cisneros', slug='casa-cisneros')
        otra_empresa = EmpresaSuscriptora.objects.create(nombre_comercial='Otro Salon', slug='otro-salon')
        planner = User.objects.create_user(username='planner_proveedor_seguro', password='test123')
        MembresiaEmpresa.objects.create(empresa=empresa, usuario=planner, rol='WEDDING_PLANNER')
        evento = crear_evento()
        evento.empresa = empresa
        evento.wedding_planner = planner
        evento.save()
        proveedor_oculto = Proveedor.objects.create(
            empresa=empresa,
            nombre_comercial='Proveedor privado',
            visible_para_wedding_planners=False,
        )
        proveedor_ajeno = Proveedor.objects.create(
            empresa=otra_empresa,
            nombre_comercial='Proveedor ajeno',
            visible_para_wedding_planners=True,
        )
        self.client.force_login(planner)

        response_oculto = self.client.post('/empresa/casa-cisneros/wedding-planner/dashboard/', {
            'accion': 'asignar_proveedor_evento',
            'evento_id': evento.id,
            'proveedor_id': proveedor_oculto.id,
            'nombre_servicio': 'Servicio oculto',
        })
        response_ajeno = self.client.post('/empresa/casa-cisneros/wedding-planner/dashboard/', {
            'accion': 'asignar_proveedor_evento',
            'evento_id': evento.id,
            'proveedor_id': proveedor_ajeno.id,
            'nombre_servicio': 'Servicio ajeno',
        })

        self.assertEqual(response_oculto.status_code, 404)
        self.assertEqual(response_ajeno.status_code, 404)
        self.assertFalse(ServicioEvento.objects.filter(evento=evento).exists())

    def test_planner_actualiza_control_operativo_de_servicio(self):
        User = get_user_model()
        empresa = EmpresaSuscriptora.objects.create(nombre_comercial='Casa Cisneros', slug='casa-cisneros')
        planner = User.objects.create_user(username='planner_servicio_operativo', password='test123')
        MembresiaEmpresa.objects.create(empresa=empresa, usuario=planner, rol='WEDDING_PLANNER')
        evento = crear_evento()
        evento.empresa = empresa
        evento.wedding_planner = planner
        evento.save()
        proveedor = Proveedor.objects.create(
            empresa=empresa,
            nombre_comercial='Foto Luz',
            visible_para_wedding_planners=True,
        )
        servicio = ServicioEvento.objects.create(
            evento=evento,
            proveedor=proveedor,
            nombre_servicio='Fotografia',
        )
        self.client.force_login(planner)

        response = self.client.post('/empresa/casa-cisneros/wedding-planner/dashboard/', {
            'accion': 'actualizar_servicio_evento',
            'servicio_id': servicio.id,
            'nombre_servicio': 'Fotografia y video',
            'estado_servicio': 'CONTRATADO',
            'fecha_servicio': '2026-12-15',
            'hora_inicio_servicio': '16:00',
            'hora_fin_servicio': '23:30',
            'lugar_servicio': 'Jardin',
            'costo_total_servicio': '25000',
            'anticipo_servicio': '10000',
            'fecha_limite_pago_servicio': '2026-12-01',
            'descripcion_servicio': 'Cobertura completa',
            'notas_servicio': 'Llevar dron',
            'cotizacion': SimpleUploadedFile('cotizacion.pdf', b'PDF', content_type='application/pdf'),
        })

        servicio.refresh_from_db()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], '/empresa/casa-cisneros/wedding-planner/dashboard/#proveedores')
        self.assertEqual(servicio.nombre_servicio, 'Fotografia y video')
        self.assertEqual(servicio.estado, 'CONTRATADO')
        self.assertEqual(servicio.costo_total, 25000)
        self.assertEqual(servicio.anticipo, 10000)
        self.assertEqual(servicio.saldo_pendiente, 15000)
        self.assertTrue(servicio.cotizacion.name.endswith('.pdf'))
        self.assertTrue(
            RegistroAuditoria.objects.filter(
                empresa=empresa,
                evento=evento,
                accion='ACTUALIZAR_SERVICIO_PLANNER',
            ).exists()
        )

    def test_planner_no_actualiza_servicio_de_evento_no_asignado(self):
        User = get_user_model()
        empresa = EmpresaSuscriptora.objects.create(nombre_comercial='Casa Cisneros', slug='casa-cisneros')
        planner = User.objects.create_user(username='planner_sin_servicio', password='test123')
        MembresiaEmpresa.objects.create(empresa=empresa, usuario=planner, rol='WEDDING_PLANNER')
        evento = crear_evento()
        evento.empresa = empresa
        evento.save()
        proveedor = Proveedor.objects.create(empresa=empresa, nombre_comercial='Audio Pro')
        servicio = ServicioEvento.objects.create(
            evento=evento,
            proveedor=proveedor,
            nombre_servicio='Audio',
            costo_total=10000,
        )
        self.client.force_login(planner)

        response = self.client.post('/empresa/casa-cisneros/wedding-planner/dashboard/', {
            'accion': 'actualizar_servicio_evento',
            'servicio_id': servicio.id,
            'nombre_servicio': 'Audio editado',
            'estado_servicio': 'CONTRATADO',
            'costo_total_servicio': '20000',
        })

        servicio.refresh_from_db()
        self.assertEqual(response.status_code, 404)
        self.assertEqual(servicio.nombre_servicio, 'Audio')
        self.assertEqual(servicio.costo_total, 10000)

    def test_dashboard_planner_bloquea_creacion_sin_rol_planner(self):
        User = get_user_model()
        empresa = EmpresaSuscriptora.objects.create(nombre_comercial='Casa Cisneros', slug='casa-cisneros')
        admin_empresa = User.objects.create_user(username='admin_no_planner', password='test123')
        MembresiaEmpresa.objects.create(empresa=empresa, usuario=admin_empresa, rol='ADMIN_EMPRESA')
        self.client.force_login(admin_empresa)
        self.client.raise_request_exception = False

        response = self.client.post('/dashboard/planner/', {
            'accion': 'crear_evento_planner',
            'empresa_id': empresa.id,
            'nombre_evento': 'Evento no permitido',
        })

        self.assertEqual(response.status_code, 403)
        self.assertFalse(EventoBoda.objects.filter(empresa=empresa, nombre_evento='Evento no permitido').exists())
        self.assertTrue(
            RegistroAuditoria.objects.filter(
                usuario=admin_empresa,
                empresa=empresa,
                accion='ACCESO_DENEGADO_DASHBOARD',
                valores_nuevos__accion_solicitada='crear_evento_planner',
            ).exists()
        )

    def test_dashboard_empresa_crea_evento_desde_panel_profesional(self):
        User = get_user_model()
        empresa = EmpresaSuscriptora.objects.create(nombre_comercial='Casa Cisneros', slug='casa-cisneros')
        admin_empresa = User.objects.create_user(username='admin_cisneros', password='test123')
        MembresiaEmpresa.objects.create(empresa=empresa, usuario=admin_empresa, rol='ADMIN_EMPRESA')
        self.client.force_login(admin_empresa)

        response = self.client.post('/dashboard/empresa/', {
            'accion': 'crear_evento',
            'empresa_id': empresa.id,
            'nombre_evento': 'XV Camila',
            'tipo_evento': 'XV',
            'nombre_principal': 'Camila',
            'nombre_secundario': 'Familia Cisneros',
            'fecha_evento': '2026-12-15T18:00',
            'capacidad_contratada': '180',
            'frase_portada': 'Mis XV',
        })

        self.assertEqual(response.status_code, 302)
        self.assertTrue(EventoBoda.objects.filter(empresa=empresa, nombre_evento='XV Camila', tipo_evento='XV').exists())

    def test_dirtec_crea_plan_empresa_suscripcion_pago_y_admin(self):
        response = self.client.post('/dirtec/dashboard/', {
            'accion': 'crear_plan_suscripcion',
            'nombre_plan': 'Profesional',
            'descripcion_plan': 'Plan para salones medianos',
            'precio_mensual_plan': '1500',
            'precio_anual_plan': '15000',
            'limite_usuarios_plan': '10',
            'limite_planners_plan': '4',
            'limite_eventos_plan': '25',
            'limite_clientes_plan': '100',
            'limite_almacenamiento_plan': '2048',
            'permite_proveedores_plan': 'on',
            'permite_reportes_plan': 'on',
            'permite_personalizacion_plan': 'on',
            'activo_plan': 'on',
        })
        self.assertEqual(response.status_code, 302)
        plan = PlanSuscripcion.objects.get(nombre='Profesional')

        response = self.client.post('/dirtec/dashboard/', {
            'accion': 'crear_empresa',
            'nombre_empresa': 'Casa Cisneros',
            'razon_social': 'Casa Cisneros SA de CV',
            'rfc_empresa': 'CCI010101AAA',
            'plan_suscripcion_id': plan.id,
            'fecha_inicio_suscripcion': '2026-07-01',
            'fecha_vencimiento_suscripcion': '2026-08-01',
            'fecha_periodo_gracia_suscripcion': '2026-08-07',
            'estado_suscripcion': 'ACTIVA',
            'contacto_nombre': 'Laura Cisneros',
            'contacto_email': 'contacto@cisneros.com',
            'contacto_telefono': '555',
            'direccion_empresa': 'Av. Central 123',
            'empresa_activa': 'on',
            'monto_pago_inicial': '1500',
            'estado_pago_inicial': 'PAGADO',
            'fecha_pago_inicial': '2026-07-01',
            'fecha_vencimiento_pago': '2026-07-01',
            'metodo_pago_inicial': 'Transferencia',
            'referencia_pago_inicial': 'DIRTEC-001',
            'username_usuario': 'admin_cisneros',
            'password_usuario': 'temporal123',
            'first_name_usuario': 'Laura',
            'last_name_usuario': 'Cisneros',
            'email_usuario': 'laura@cisneros.com',
        })

        self.assertEqual(response.status_code, 302)
        empresa = EmpresaSuscriptora.objects.get(slug='casa-cisneros')
        self.assertEqual(empresa.rfc, 'CCI010101AAA')
        self.assertEqual(empresa.max_eventos_activos, 25)
        self.assertTrue(SuscripcionEmpresa.objects.filter(empresa=empresa, plan=plan, estado='ACTIVA').exists())
        self.assertTrue(PagoSuscripcion.objects.filter(empresa=empresa, estado='PAGADO', monto='1500').exists())
        self.assertTrue(MembresiaEmpresa.objects.filter(empresa=empresa, usuario__username='admin_cisneros', rol='ADMIN_EMPRESA').exists())
        self.assertTrue(RegistroAuditoria.objects.filter(empresa=empresa, accion='CREAR_EMPRESA_SAAS').exists())

    def test_dirtec_bloquea_suscripcion_y_pago_pagado_reactiva_empresa(self):
        plan = PlanSuscripcion.objects.create(nombre='Profesional', precio_mensual=1500)
        empresa = EmpresaSuscriptora.objects.create(nombre_comercial='Casa Cisneros', slug='casa-cisneros')
        suscripcion = SuscripcionEmpresa.objects.create(
            empresa=empresa,
            plan=plan,
            fecha_inicio=timezone.localdate(),
            fecha_vencimiento=timezone.localdate() + timedelta(days=30),
            estado='ACTIVA',
        )

        response = self.client.post('/dirtec/dashboard/', {
            'accion': 'actualizar_suscripcion',
            'suscripcion_id': suscripcion.id,
            'plan_suscripcion_id': plan.id,
            'estado_suscripcion': 'SUSPENDIDA',
            'fecha_inicio_suscripcion': '2026-07-01',
            'fecha_vencimiento_suscripcion': '2026-08-01',
            'bloqueada_manualmente': 'on',
            'motivo_bloqueo': 'Pago vencido',
        })
        empresa.refresh_from_db()
        suscripcion.refresh_from_db()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(empresa.estado, 'BLOQUEADA')
        self.assertFalse(empresa.activo)
        self.assertTrue(suscripcion.bloqueada_manualmente)

        response = self.client.post('/dirtec/dashboard/', {
            'accion': 'registrar_pago_suscripcion',
            'suscripcion_id': suscripcion.id,
            'monto_pago': '1500',
            'estado_pago': 'PAGADO',
            'fecha_vencimiento_pago': '2026-08-01',
            'fecha_pago': '2026-07-20',
            'metodo_pago': 'Transferencia',
            'referencia_pago': 'DIRTEC-002',
        })
        empresa.refresh_from_db()
        suscripcion.refresh_from_db()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(empresa.estado, 'ACTIVA')
        self.assertTrue(empresa.activo)
        self.assertEqual(suscripcion.estado, 'ACTIVA')
        self.assertFalse(suscripcion.bloqueada_manualmente)
        self.assertTrue(RegistroAuditoria.objects.filter(empresa=empresa, accion='REGISTRAR_PAGO_SUSCRIPCION').exists())

    def test_dirtec_edita_y_elimina_planes_desde_dashboard(self):
        plan = PlanSuscripcion.objects.create(nombre='Basico', precio_mensual=800, limite_usuarios=3)
        plan_con_historial = PlanSuscripcion.objects.create(nombre='Profesional', precio_mensual=1500)
        empresa = EmpresaSuscriptora.objects.create(nombre_comercial='Casa Cisneros', slug='casa-cisneros')
        SuscripcionEmpresa.objects.create(
            empresa=empresa,
            plan=plan_con_historial,
            fecha_inicio=timezone.localdate(),
            fecha_vencimiento=timezone.localdate() + timedelta(days=30),
            estado='ACTIVA',
        )

        response = self.client.post('/dirtec/dashboard/', {
            'accion': 'editar_plan_suscripcion',
            'plan_id': plan.id,
            'nombre_plan': 'Basico Plus',
            'precio_mensual_plan': '950',
            'precio_anual_plan': '9500',
            'limite_usuarios_plan': '6',
            'limite_planners_plan': '2',
            'limite_eventos_plan': '8',
            'limite_clientes_plan': '40',
            'limite_almacenamiento_plan': '900',
            'permite_reportes_plan': 'on',
            'activo_plan': 'on',
        })
        plan.refresh_from_db()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(plan.nombre, 'Basico Plus')
        self.assertEqual(plan.limite_usuarios, 6)

        self.client.post('/dirtec/dashboard/', {
            'accion': 'eliminar_plan_suscripcion',
            'plan_id': plan.id,
        })
        self.assertFalse(PlanSuscripcion.objects.filter(id=plan.id).exists())

        self.client.post('/dirtec/dashboard/', {
            'accion': 'eliminar_plan_suscripcion',
            'plan_id': plan_con_historial.id,
        })
        plan_con_historial.refresh_from_db()
        self.assertFalse(plan_con_historial.activo)

    def test_dirtec_edita_y_desactiva_empresa_y_usuario(self):
        User = get_user_model()
        empresa = EmpresaSuscriptora.objects.create(nombre_comercial='Casa Cisneros', slug='casa-cisneros')
        usuario = User.objects.create_user(username='admin_cisneros', password='test123')
        membresia = MembresiaEmpresa.objects.create(empresa=empresa, usuario=usuario, rol='ADMIN_EMPRESA')

        self.client.post('/dirtec/dashboard/', {
            'accion': 'editar_empresa',
            'empresa_id': empresa.id,
            'nombre_empresa': 'Casa Cisneros Premium',
            'razon_social': 'Casa Cisneros SA',
            'rfc_empresa': 'CCI010101AAA',
            'estado_empresa': 'ACTIVA',
            'plan_empresa': 'ENTERPRISE',
            'max_eventos_activos': '50',
            'max_usuarios': '25',
            'contacto_nombre': 'Laura',
            'contacto_email': 'laura@cisneros.com',
            'contacto_telefono': '555',
            'direccion_empresa': 'Av Central',
            'empresa_activa': 'on',
        })
        empresa.refresh_from_db()
        self.assertEqual(empresa.nombre_comercial, 'Casa Cisneros Premium')
        self.assertEqual(empresa.plan, 'ENTERPRISE')
        self.assertEqual(empresa.max_usuarios, 25)

        self.client.post('/dirtec/dashboard/', {
            'accion': 'editar_usuario_empresa',
            'empresa_id': empresa.id,
            'membresia_id': membresia.id,
            'first_name_usuario': 'Laura',
            'last_name_usuario': 'Cisneros',
            'email_usuario': 'laura@cisneros.com',
            'rol_usuario': 'ADMIN_EMPRESA',
            'activo_usuario': 'on',
            'puede_gestionar_catalogos_usuario': 'on',
        })
        usuario.refresh_from_db()
        membresia.refresh_from_db()
        self.assertEqual(usuario.first_name, 'Laura')
        self.assertTrue(membresia.puede_gestionar_catalogos)

        self.client.post('/dirtec/dashboard/', {'accion': 'desactivar_empresa', 'empresa_id': empresa.id})
        empresa.refresh_from_db()
        membresia.refresh_from_db()
        self.assertFalse(empresa.activo)
        self.assertFalse(membresia.activo)

    def test_dirtec_elimina_empresa_con_datos_relacionados(self):
        User = get_user_model()
        empresa = EmpresaSuscriptora.objects.create(nombre_comercial='Casa Cisneros', slug='casa-cisneros')
        usuario = User.objects.create_user(username='admin_cisneros', password='test123')
        MembresiaEmpresa.objects.create(empresa=empresa, usuario=usuario, rol='ADMIN_EMPRESA')
        evento = crear_evento()
        evento.empresa = empresa
        evento.save()
        proveedor = Proveedor.objects.create(empresa=empresa, nombre_comercial='Banquetes Cisneros')
        paquete = PaqueteBoda.objects.create(empresa=empresa, nombre='Paquete Jardin')

        response = self.client.post('/dirtec/dashboard/', {
            'accion': 'eliminar_empresa',
            'empresa_id': empresa.id,
        })

        self.assertEqual(response.status_code, 302)
        self.assertFalse(EmpresaSuscriptora.objects.filter(id=empresa.id).exists())
        self.assertFalse(EventoBoda.objects.filter(id=evento.id).exists())
        self.assertFalse(Proveedor.objects.filter(id=proveedor.id).exists())
        self.assertFalse(PaqueteBoda.objects.filter(id=paquete.id).exists())
        self.assertFalse(MembresiaEmpresa.objects.filter(empresa_id=empresa.id).exists())

    def test_dashboard_empresa_edita_registros_operativos(self):
        User = get_user_model()
        empresa = EmpresaSuscriptora.objects.create(nombre_comercial='Casa Cisneros', slug='casa-cisneros')
        admin_empresa = User.objects.create_user(username='admin_cisneros', password='test123')
        planner = User.objects.create_user(username='planner_ana', password='test123')
        cliente = User.objects.create_user(username='cliente_wendy', password='test123')
        membresia_planner = MembresiaEmpresa.objects.create(
            empresa=empresa,
            usuario=planner,
            rol='WEDDING_PLANNER',
            activo=True,
        )
        membresia_cliente = MembresiaEmpresa.objects.create(
            empresa=empresa,
            usuario=cliente,
            rol='CLIENTE',
            activo=True,
        )
        MembresiaEmpresa.objects.create(
            empresa=empresa,
            usuario=admin_empresa,
            rol='ADMIN_EMPRESA',
            puede_gestionar_catalogos=True,
        )
        sede = SedeEvento.objects.create(empresa=empresa, nombre='Salon Imperial', tipo='SALON', capacidad_maxima=200)
        proveedor = Proveedor.objects.create(empresa=empresa, nombre_comercial='Banquetes Cisneros', tipo_proveedor='BANQUETE')
        paquete = PaqueteBoda.objects.create(empresa=empresa, nombre='Paquete Jardin', numero_personas_incluidas=150, precio_base=120000)
        evento = crear_evento()
        evento.empresa = empresa
        evento.save()
        self.client.force_login(admin_empresa)

        response = self.client.post('/dashboard/empresa/', {
            'accion': 'editar_evento',
            'empresa_id': empresa.id,
            'evento_id': evento.id,
            'nombre_evento': 'Boda Casa Cisneros',
            'tipo_evento': 'BODA',
            'estado': 'CONFIRMADO',
            'planner_id': planner.id,
            'sede_id': sede.id,
            'nombre_principal': 'Wendy',
            'nombre_secundario': 'Diego',
            'fecha_evento': '2026-12-15T20:00',
            'fecha_ceremonia': '2026-12-15T18:00',
            'lugar_ceremonia': 'Templo San Jose',
            'lugar_recepcion': 'Salon Imperial',
            'capacidad_contratada': '180',
            'frase_portada': 'Nuestra Boda',
            'activo_evento': 'on',
        })
        evento.refresh_from_db()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(evento.nombre_evento, 'Boda Casa Cisneros')
        self.assertEqual(evento.estado, 'CONFIRMADO')
        self.assertEqual(evento.wedding_planner, planner)
        self.assertEqual(evento.sede, sede)
        self.assertEqual(evento.capacidad_contratada, 180)

        self.client.post('/dashboard/empresa/', {
            'accion': 'editar_usuario_empresa',
            'empresa_id': empresa.id,
            'membresia_id': membresia_planner.id,
            'first_name_usuario': 'Ana',
            'last_name_usuario': 'Lopez',
            'email_usuario': 'ana@example.com',
            'rol_usuario': 'WEDDING_PLANNER',
            'activo_usuario': 'on',
            'puede_gestionar_catalogos_usuario': 'on',
        })
        planner.refresh_from_db()
        membresia_planner.refresh_from_db()
        self.assertEqual(planner.first_name, 'Ana')
        self.assertTrue(membresia_planner.puede_gestionar_catalogos)

        self.client.post('/dashboard/empresa/', {
            'accion': 'editar_usuario_empresa',
            'empresa_id': empresa.id,
            'membresia_id': membresia_cliente.id,
            'first_name_usuario': 'Wendy',
            'last_name_usuario': 'Perez',
            'email_usuario': 'wendy@example.com',
            'rol_usuario': 'CLIENTE',
            'activo_usuario': 'on',
            'origen': 'clientes',
        })
        cliente.refresh_from_db()
        membresia_cliente.refresh_from_db()
        self.assertEqual(cliente.first_name, 'Wendy')
        self.assertTrue(membresia_cliente.activo)

        self.client.post('/dashboard/empresa/', {
            'accion': 'editar_sede',
            'empresa_id': empresa.id,
            'sede_id': sede.id,
            'nombre_sede': 'Jardin Imperial',
            'tipo_sede': 'JARDIN',
            'capacidad_minima': '80',
            'capacidad_maxima': '250',
            'precio_base_sede': '50000',
            'direccion_sede': 'Av. Principal 123',
            'descripcion_sede': 'Jardin principal',
            'activa_sede': 'on',
        })
        self.client.post('/dashboard/empresa/', {
            'accion': 'editar_proveedor',
            'empresa_id': empresa.id,
            'proveedor_id': proveedor.id,
            'nombre_proveedor': 'Banquetes Premium',
            'tipo_proveedor': 'BUFFET',
            'contacto_proveedor': 'Laura',
            'telefono_proveedor': '555',
            'correo_proveedor': 'laura@example.com',
            'descripcion_proveedor': 'Buffet completo',
            'activo_proveedor': 'on',
        })
        self.client.post('/dashboard/empresa/', {
            'accion': 'editar_paquete',
            'empresa_id': empresa.id,
            'paquete_id': paquete.id,
            'nombre_paquete': 'Paquete Premium',
            'personas_paquete': '200',
            'precio_base_paquete': '180000',
            'descripcion_paquete': 'Banquete, salon y musica',
            'activo_paquete': 'on',
        })
        sede.refresh_from_db()
        proveedor.refresh_from_db()
        paquete.refresh_from_db()
        self.assertEqual(sede.nombre, 'Jardin Imperial')
        self.assertEqual(sede.capacidad_maxima, 250)
        self.assertEqual(proveedor.nombre_comercial, 'Banquetes Premium')
        self.assertEqual(proveedor.tipo_proveedor, 'BUFFET')
        self.assertEqual(paquete.nombre, 'Paquete Premium')
        self.assertEqual(paquete.numero_personas_incluidas, 200)

    def test_dashboard_empresa_desactiva_sin_borrar_registros(self):
        User = get_user_model()
        empresa = EmpresaSuscriptora.objects.create(nombre_comercial='Casa Cisneros', slug='casa-cisneros')
        admin_empresa = User.objects.create_user(username='admin_cisneros', password='test123')
        planner = User.objects.create_user(username='planner_ana', password='test123')
        membresia = MembresiaEmpresa.objects.create(empresa=empresa, usuario=planner, rol='WEDDING_PLANNER')
        MembresiaEmpresa.objects.create(
            empresa=empresa,
            usuario=admin_empresa,
            rol='ADMIN_EMPRESA',
            puede_gestionar_catalogos=True,
        )
        evento = crear_evento()
        evento.empresa = empresa
        evento.save()
        sede = SedeEvento.objects.create(empresa=empresa, nombre='Salon Imperial')
        proveedor = Proveedor.objects.create(empresa=empresa, nombre_comercial='Banquetes Cisneros')
        paquete = PaqueteBoda.objects.create(empresa=empresa, nombre='Paquete Jardin')
        self.client.force_login(admin_empresa)

        self.client.post('/dashboard/empresa/', {'accion': 'desactivar_evento', 'empresa_id': empresa.id, 'evento_id': evento.id})
        self.client.post('/dashboard/empresa/', {'accion': 'desactivar_usuario_empresa', 'empresa_id': empresa.id, 'membresia_id': membresia.id})
        self.client.post('/dashboard/empresa/', {'accion': 'desactivar_sede', 'empresa_id': empresa.id, 'sede_id': sede.id})
        self.client.post('/dashboard/empresa/', {'accion': 'desactivar_proveedor', 'empresa_id': empresa.id, 'proveedor_id': proveedor.id})
        self.client.post('/dashboard/empresa/', {'accion': 'desactivar_paquete', 'empresa_id': empresa.id, 'paquete_id': paquete.id})

        evento.refresh_from_db()
        membresia.refresh_from_db()
        sede.refresh_from_db()
        proveedor.refresh_from_db()
        paquete.refresh_from_db()
        self.assertFalse(evento.activo)
        self.assertFalse(membresia.activo)
        self.assertFalse(sede.activa)
        self.assertFalse(proveedor.activo)
        self.assertFalse(paquete.activo)
        self.assertTrue(EventoBoda.objects.filter(id=evento.id).exists())
        self.assertTrue(SedeEvento.objects.filter(id=sede.id).exists())

    def test_dashboard_empresa_elimina_registros_operativos(self):
        User = get_user_model()
        empresa = EmpresaSuscriptora.objects.create(nombre_comercial='Casa Cisneros', slug='casa-cisneros')
        admin_empresa = User.objects.create_user(username='admin_cisneros', password='test123')
        planner = User.objects.create_user(username='planner_ana', password='test123')
        membresia = MembresiaEmpresa.objects.create(empresa=empresa, usuario=planner, rol='WEDDING_PLANNER')
        MembresiaEmpresa.objects.create(
            empresa=empresa,
            usuario=admin_empresa,
            rol='ADMIN_EMPRESA',
            puede_gestionar_catalogos=True,
        )
        evento = crear_evento()
        evento.empresa = empresa
        evento.save()
        sede = SedeEvento.objects.create(empresa=empresa, nombre='Salon Imperial')
        proveedor = Proveedor.objects.create(empresa=empresa, nombre_comercial='Banquetes Cisneros')
        paquete = PaqueteBoda.objects.create(empresa=empresa, nombre='Paquete Jardin')
        self.client.force_login(admin_empresa)

        self.client.post('/dashboard/empresa/', {'accion': 'eliminar_evento', 'empresa_id': empresa.id, 'evento_id': evento.id})
        self.client.post('/dashboard/empresa/', {'accion': 'eliminar_usuario_empresa', 'empresa_id': empresa.id, 'membresia_id': membresia.id})
        self.client.post('/dashboard/empresa/', {'accion': 'eliminar_sede', 'empresa_id': empresa.id, 'sede_id': sede.id})
        self.client.post('/dashboard/empresa/', {'accion': 'eliminar_proveedor', 'empresa_id': empresa.id, 'proveedor_id': proveedor.id})
        self.client.post('/dashboard/empresa/', {'accion': 'eliminar_paquete', 'empresa_id': empresa.id, 'paquete_id': paquete.id})

        self.assertFalse(EventoBoda.objects.filter(id=evento.id).exists())
        self.assertFalse(MembresiaEmpresa.objects.filter(id=membresia.id).exists())
        self.assertFalse(User.objects.filter(id=planner.id).exists())
        self.assertFalse(SedeEvento.objects.filter(id=sede.id).exists())
        self.assertFalse(Proveedor.objects.filter(id=proveedor.id).exists())
        self.assertFalse(PaqueteBoda.objects.filter(id=paquete.id).exists())

    def test_dashboard_avanzado_empresa_crea_operacion_sin_admin(self):
        User = get_user_model()
        empresa = EmpresaSuscriptora.objects.create(nombre_comercial='Casa Cisneros', slug='casa-cisneros')
        admin_empresa = User.objects.create_user(username='admin_operacion', password='test123')
        MembresiaEmpresa.objects.create(empresa=empresa, usuario=admin_empresa, rol='ADMIN_EMPRESA')
        proveedor = Proveedor.objects.create(empresa=empresa, nombre_comercial='Banquetes Cisneros')
        categoria = CategoriaGasto.objects.create(nombre='Banquete')
        evento = crear_evento()
        evento.empresa = empresa
        evento.save()
        self.client.force_login(admin_empresa)

        response = self.client.get(f'/dashboard/?evento={evento.id}')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Gestion operativa del evento')
        self.assertNotContains(response, '/admin/proveedores/servicioevento/')

        self.client.post('/dashboard/', {
            'accion': 'agregar_servicio_evento',
            'evento_id': evento.id,
            'proveedor_id': proveedor.id,
            'nombre_servicio': 'Banquete premium',
            'estado_servicio': 'CONTRATADO',
            'fecha_servicio': '2026-12-15',
            'hora_inicio_servicio': '19:00',
            'costo_total_servicio': '45000',
            'anticipo_servicio': '10000',
        })
        servicio = ServicioEvento.objects.get(evento=evento)
        self.assertEqual(servicio.proveedor, proveedor)
        self.assertEqual(servicio.estado, 'CONTRATADO')

        self.client.post('/dashboard/', {
            'accion': 'agregar_tarea_evento',
            'evento_id': evento.id,
            'titulo_tarea': 'Confirmar menu',
            'estado_tarea': 'EN_PROCESO',
            'prioridad_tarea': 'ALTA',
            'categoria_tarea': 'CATERING',
            'fecha_limite_tarea': '2026-12-01',
            'porcentaje_avance_tarea': '40',
        })
        tarea = TareaEvento.objects.get(evento=evento)
        self.assertEqual(tarea.titulo, 'Confirmar menu')
        self.assertEqual(tarea.porcentaje_avance, 40)

        self.client.post('/dashboard/', {
            'accion': 'agregar_gasto_evento',
            'evento_id': evento.id,
            'concepto_gasto': 'Anticipo banquete',
            'categoria_gasto_id': categoria.id,
            'proveedor_id': proveedor.id,
            'monto_estimado_gasto': '50000',
            'monto_real_gasto': '45000',
            'fecha_limite_gasto': '2026-11-20',
            'estado_gasto': 'PARCIAL',
        })
        gasto = GastoEvento.objects.get(evento=evento)
        self.assertEqual(gasto.categoria, categoria)
        self.assertEqual(gasto.proveedor, proveedor)

        self.client.post('/dashboard/', {
            'accion': 'agregar_pago_evento',
            'evento_id': evento.id,
            'gasto_id': gasto.id,
            'monto_pago': '10000',
            'fecha_pago': '2026-10-15',
            'metodo_pago': 'TRANSFERENCIA',
            'referencia_pago': 'TRX-1',
        })
        pago = PagoEvento.objects.get(gasto=gasto)
        self.assertEqual(pago.monto, 10000)

        self.client.post('/dashboard/', {
            'accion': 'agregar_documento_evento',
            'evento_id': evento.id,
            'tipo_documento': 'CONTRATO',
            'titulo_documento': 'Contrato banquete',
            'proveedor_id': proveedor.id,
            'visible_cliente_documento': 'on',
            'archivo_documento': SimpleUploadedFile('contrato.pdf', b'%PDF-1.4', content_type='application/pdf'),
        })
        documento = DocumentoEvento.objects.get(evento=evento)
        self.assertTrue(documento.visible_cliente)

        self.client.post('/dashboard/', {
            'accion': 'agregar_aprobacion_evento',
            'evento_id': evento.id,
            'tipo_aprobacion': 'MENU',
            'titulo_aprobacion': 'Aprobar menu',
            'descripcion_aprobacion': 'Menu de tres tiempos',
            'estado_aprobacion': 'PENDIENTE',
            'comentario_aprobacion': 'Esperando cliente',
        })
        aprobacion = AprobacionEvento.objects.get(evento=evento)
        self.assertEqual(aprobacion.solicitado_por, admin_empresa)
        self.assertEqual(aprobacion.comentario, 'Esperando cliente')

    def test_dashboard_guarda_detalle_produccion_de_contrato_y_sincroniza_menu(self):
        User = get_user_model()
        empresa = EmpresaSuscriptora.objects.create(nombre_comercial='Casa Cisneros', slug='casa-cisneros')
        admin_empresa = User.objects.create_user(username='admin_contrato_evento', password='test123')
        MembresiaEmpresa.objects.create(empresa=empresa, usuario=admin_empresa, rol='ADMIN_EMPRESA')
        evento = crear_evento()
        evento.empresa = empresa
        evento.save()
        self.client.force_login(admin_empresa)

        response = self.client.post('/dashboard/', {
            'accion': 'guardar_detalle_produccion',
            'evento_id': evento.id,
            'folio_contrato': 'Jardin Cisneros 2026',
            'cliente_contrato': 'Maria Fernanda Flores Hernandez',
            'arrendador': 'Quinta Cisneros',
            'lugar_contrato': 'Jardin Cisneros',
            'adultos_contratados': '300',
            'ninos_contratados': '85',
            'horas_evento': '7',
            'recepcion_hora': '17:00',
            'inicio_evento': '17:30',
            'fin_evento': '00:30',
            'minutos_desalojo': '30',
            'costo_hora_extra': '5000',
            'precio_renta_salon': '300000',
            'deposito_apartado': '5000',
            'anticipo_recibido': '20000',
            'saldo_contrato': '285000',
            'dias_antes_liquidacion': '22',
            'banco': 'Bancomer',
            'numero_cuenta': '1134429060',
            'clabe': '012225013442906004',
            'tarjeta': '4152 3136 1389 1162',
            'color_mantel': 'Por definir',
            'tipo_mesa': 'Redonda y rectangular segun layout',
            'tamano_mesa': 'Mesa de 10 pax',
            'diseno_carpa': 'Carpa elegante para jardin',
            'tamano_carpa': 'Por definir en plano',
            'menu_entrada': 'Entrada de dos tiempos',
            'menu_plato_fuerte': 'Banquete adulto',
            'menu_postre': 'Mesa de postres',
            'menu_trasnochado': 'Trasnochado incluido',
            'menu_infantil': 'Banquete infantil',
            'bebidas': 'Refresco y hielo ilimitado',
            'servicios_incluidos': 'Valet parking, mobiliario, manteleria, meseros, loza, DJ de lujo, pista, planta de luz.',
        })

        detalle = DetalleProduccionEvento.objects.get(evento=evento)
        evento.refresh_from_db()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(detalle.total_personas_contratadas, 385)
        self.assertEqual(detalle.saldo_contrato, 285000)
        self.assertEqual(evento.capacidad_contratada, 385)
        self.assertEqual(evento.presupuesto_total, 300000)
        self.assertEqual(evento.monto_pagado, 20000)
        self.assertTrue(MenuBoda.objects.filter(evento=evento, nombre='Entrada', descripcion='Entrada de dos tiempos').exists())
        self.assertTrue(MenuBoda.objects.filter(evento=evento, nombre='Postre', descripcion='Mesa de postres').exists())
        self.assertTrue(MenuBoda.objects.filter(evento=evento, nombre='Trasnochado', descripcion='Trasnochado incluido').exists())

    def test_dashboard_genera_pendientes_desde_detalle_de_contrato(self):
        User = get_user_model()
        empresa = EmpresaSuscriptora.objects.create(nombre_comercial='Casa Cisneros', slug='casa-cisneros')
        admin_empresa = User.objects.create_user(username='admin_pendientes_contrato', password='test123')
        MembresiaEmpresa.objects.create(empresa=empresa, usuario=admin_empresa, rol='ADMIN_EMPRESA')
        evento = crear_evento()
        evento.empresa = empresa
        evento.save()
        DetalleProduccionEvento.objects.create(
            evento=evento,
            adultos_contratados=300,
            ninos_contratados=85,
            color_mantel='Por definir',
            color_servilleta='Por definir',
            tipo_mesa='Por definir',
            tamano_mesa='Pendiente segun layout',
            diseno_carpa='Por definir',
            menu_plato_fuerte='Detallar platillo final',
            menu_postre='Mesa de postres incluida',
            menu_trasnochado='Trasnochado incluido',
        )
        self.client.force_login(admin_empresa)

        response = self.client.post('/dashboard/', {
            'accion': 'generar_pendientes_contrato',
            'evento_id': evento.id,
        })

        titulos = set(TareaEvento.objects.filter(evento=evento).values_list('titulo', flat=True))
        self.assertEqual(response.status_code, 302)
        self.assertIn('Definir colores de manteleria', titulos)
        self.assertIn('Definir tipo y tamano de mesas', titulos)
        self.assertIn('Definir carpa del jardin', titulos)
        self.assertIn('Cerrar entrada y plato fuerte', titulos)
        self.assertNotIn('Cerrar postre o mesa de postres', titulos)

    def test_dashboard_avanzado_gestiona_paquetes_y_personal_evento(self):
        User = get_user_model()
        empresa = EmpresaSuscriptora.objects.create(nombre_comercial='Casa Cisneros', slug='casa-cisneros')
        admin_empresa = User.objects.create_user(username='admin_paquetes_personal', password='test123')
        MembresiaEmpresa.objects.create(empresa=empresa, usuario=admin_empresa, rol='ADMIN_EMPRESA')
        proveedor = Proveedor.objects.create(empresa=empresa, nombre_comercial='Staff Cisneros', tipo_proveedor='MESEROS')
        paquete = PaqueteBoda.objects.create(
            empresa=empresa,
            nombre='Paquete Jardin',
            precio_base=120000,
            numero_personas_incluidas=150,
        )
        evento = crear_evento()
        evento.empresa = empresa
        evento.save()
        self.client.force_login(admin_empresa)

        response = self.client.get(f'/dashboard/?evento={evento.id}')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Asignar paquete al evento')
        self.assertContains(response, 'Agregar personal operativo')

        self.client.post('/dashboard/', {
            'accion': 'agregar_paquete_evento',
            'evento_id': evento.id,
            'paquete_id': paquete.id,
            'estado_paquete': 'APROBADO',
            'precio_acordado_paquete': '118000',
            'descuento_paquete': '8000',
            'servicios_adicionales_paquete': 'Barra extra',
            'notas_paquete': 'Cliente pidio ajuste',
        })
        paquete_evento = PaqueteEvento.objects.get(evento=evento)
        self.assertEqual(paquete_evento.estado, 'APROBADO')
        self.assertEqual(paquete_evento.total, 110000)

        self.client.post('/dashboard/', {
            'accion': 'agregar_personal_evento',
            'evento_id': evento.id,
            'proveedor_id': proveedor.id,
            'nombre_personal': 'Carlos Mesero',
            'tipo_personal': 'MESERO',
            'estado_personal': 'CONFIRMADO',
            'telefono_personal': '555',
            'hora_entrada_personal': '17:00',
            'hora_salida_personal': '02:00',
            'area_personal': 'Salon',
            'mesas_personal': '1-6',
            'costo_personal': '900',
            'uniforme_personal': 'Negro formal',
        })
        personal = PersonalEvento.objects.get(evento=evento)
        self.assertEqual(personal.proveedor, proveedor)
        self.assertEqual(personal.estado, 'CONFIRMADO')

        self.client.post('/dashboard/', {
            'accion': 'editar_paquete_evento',
            'evento_id': evento.id,
            'paquete_evento_id': paquete_evento.id,
            'paquete_id': paquete.id,
            'estado_paquete': 'CONTRATADO',
            'precio_acordado_paquete': '120000',
            'descuento_paquete': '5000',
            'total_paquete': '115000',
        })
        self.client.post('/dashboard/', {
            'accion': 'editar_personal_evento',
            'evento_id': evento.id,
            'personal_id': personal.id,
            'proveedor_id': proveedor.id,
            'nombre_personal': 'Carlos Capitan',
            'tipo_personal': 'CAPITAN',
            'estado_personal': 'EN_SITIO',
            'costo_personal': '1500',
        })
        paquete_evento.refresh_from_db()
        personal.refresh_from_db()
        self.assertEqual(paquete_evento.estado, 'CONTRATADO')
        self.assertEqual(paquete_evento.total, 115000)
        self.assertEqual(personal.nombre, 'Carlos Capitan')
        self.assertEqual(personal.tipo_personal, 'CAPITAN')

        self.client.post('/dashboard/', {'accion': 'eliminar_paquete_evento', 'evento_id': evento.id, 'paquete_evento_id': paquete_evento.id})
        self.client.post('/dashboard/', {'accion': 'eliminar_personal_evento', 'evento_id': evento.id, 'personal_id': personal.id})
        self.assertFalse(PaqueteEvento.objects.filter(id=paquete_evento.id).exists())
        self.assertFalse(PersonalEvento.objects.filter(id=personal.id).exists())

    def test_dashboard_avanzado_gestiona_banquete_decoracion_musica_y_canciones(self):
        User = get_user_model()
        empresa = EmpresaSuscriptora.objects.create(nombre_comercial='Casa Cisneros', slug='casa-cisneros')
        admin_empresa = User.objects.create_user(username='admin_banquete_musica', password='test123')
        MembresiaEmpresa.objects.create(empresa=empresa, usuario=admin_empresa, rol='ADMIN_EMPRESA')
        proveedor_banquete = Proveedor.objects.create(
            empresa=empresa,
            nombre_comercial='Banquetes Cisneros',
            tipo_proveedor='BANQUETE',
        )
        proveedor_musica = Proveedor.objects.create(
            empresa=empresa,
            nombre_comercial='DJ Elegante',
            tipo_proveedor='DJ',
        )
        categoria_alimento = CategoriaAlimento.objects.create(nombre='Plato fuerte')
        alimento = Alimento.objects.create(categoria=categoria_alimento, nombre='Filete en salsa')
        paquete_buffet = PaqueteBuffet.objects.create(
            proveedor=proveedor_banquete,
            nombre='Buffet premium',
            personas_incluidas=120,
            precio_base=85000,
        )
        evento = crear_evento()
        evento.empresa = empresa
        evento.save()
        self.client.force_login(admin_empresa)

        response = self.client.get(f'/dashboard/?evento={evento.id}')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Agregar banquete')
        self.assertContains(response, 'Agregar decoracion')
        self.assertContains(response, 'Agregar entretenimiento')

        self.client.post('/dashboard/', {
            'accion': 'agregar_catering_evento',
            'evento_id': evento.id,
            'proveedor_id': proveedor_banquete.id,
            'paquete_buffet_id': paquete_buffet.id,
            'cantidad_adultos_catering': '110',
            'cantidad_ninos_catering': '12',
            'cantidad_proveedores_catering': '8',
            'precio_total_catering': '92000',
            'fecha_degustacion_catering': '2026-11-10',
            'hora_servicio_catering': '20:30',
            'horario_montaje_catering': '16:00',
            'duracion_servicio_catering': '4 horas',
            'alimentos_catering': [alimento.id],
            'observaciones_catering': 'Menu sin picante',
        })
        catering = CateringEvento.objects.get(evento=evento)
        self.assertEqual(catering.proveedor, proveedor_banquete)
        self.assertEqual(catering.paquete_buffet, paquete_buffet)
        self.assertEqual(catering.total_personas, 130)
        self.assertEqual(list(catering.alimentos_seleccionados.all()), [alimento])

        self.client.post('/dashboard/', {
            'accion': 'agregar_decoracion_evento',
            'evento_id': evento.id,
            'proveedor_id': proveedor_banquete.id,
            'nombre_decoracion': 'Arco floral',
            'categoria_decoracion': 'CEREMONIA',
            'estado_decoracion': 'APROBADO',
            'cantidad_decoracion': '1',
            'costo_decoracion': '6500',
            'color_decoracion': 'Blanco',
            'material_decoracion': 'Flores naturales',
            'aprobado_cliente_decoracion': 'on',
            'descripcion_decoracion': 'Entrada del templo',
        })
        decoracion = ElementoDecoracion.objects.get(evento=evento)
        self.assertEqual(decoracion.nombre, 'Arco floral')
        self.assertEqual(decoracion.categoria, 'CEREMONIA')
        self.assertTrue(decoracion.aprobado_cliente)

        self.client.post('/dashboard/', {
            'accion': 'agregar_entretenimiento_evento',
            'evento_id': evento.id,
            'proveedor_id': proveedor_musica.id,
            'tipo_entretenimiento': 'DJ',
            'nombre_artista': 'DJ Elegante',
            'estado_entretenimiento': 'CONTRATADO',
            'hora_inicio_entretenimiento': '21:00',
            'hora_fin_entretenimiento': '02:00',
            'duracion_entretenimiento': '5 horas',
            'costo_entretenimiento': '18000',
            'anticipo_entretenimiento': '5000',
            'requerimientos_entretenimiento': 'Contacto electrico y mesa',
        })
        entretenimiento = EntretenimientoEvento.objects.get(evento=evento)
        self.assertEqual(entretenimiento.proveedor, proveedor_musica)
        self.assertEqual(entretenimiento.estado, 'CONTRATADO')
        self.assertEqual(entretenimiento.saldo_pendiente, 13000)

        self.client.post('/dashboard/', {
            'accion': 'agregar_cancion_evento',
            'evento_id': evento.id,
            'entretenimiento_id': entretenimiento.id,
            'tipo_momento': 'PRIMER_BAILE',
            'nombre_cancion': 'Perfect',
            'artista_cancion': 'Ed Sheeran',
            'enlace_cancion': 'https://example.com/cancion',
            'orden_cancion': '1',
            'notas_cancion': 'Version acustica',
        })
        cancion = CancionEvento.objects.get(evento=evento)
        self.assertEqual(cancion.entretenimiento, entretenimiento)
        self.assertEqual(cancion.tipo_momento, 'PRIMER_BAILE')

        response = self.client.get(f'/dashboard/?evento={evento.id}')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Buffet premium')
        self.assertContains(response, 'Arco floral')
        self.assertContains(response, 'DJ Elegante')
        self.assertContains(response, 'Perfect')

        self.client.post('/dashboard/', {
            'accion': 'editar_catering_evento',
            'evento_id': evento.id,
            'catering_id': catering.id,
            'cantidad_adultos_catering': '100',
            'cantidad_ninos_catering': '10',
            'cantidad_proveedores_catering': '5',
            'precio_total_catering': '88000',
        })
        self.client.post('/dashboard/', {
            'accion': 'editar_decoracion_evento',
            'evento_id': evento.id,
            'decoracion_id': decoracion.id,
            'nombre_decoracion': 'Arco floral minimal',
            'categoria_decoracion': 'CEREMONIA',
            'estado_decoracion': 'LISTO_MONTAJE',
            'cantidad_decoracion': '1',
            'costo_decoracion': '6000',
        })
        self.client.post('/dashboard/', {
            'accion': 'editar_entretenimiento_evento',
            'evento_id': evento.id,
            'entretenimiento_id': entretenimiento.id,
            'tipo_entretenimiento': 'DJ',
            'nombre_artista': 'DJ Elegante Live',
            'estado_entretenimiento': 'LIQUIDADO',
            'costo_entretenimiento': '18000',
            'anticipo_entretenimiento': '18000',
        })
        self.client.post('/dashboard/', {
            'accion': 'editar_cancion_evento',
            'evento_id': evento.id,
            'cancion_id': cancion.id,
            'entretenimiento_id': entretenimiento.id,
            'tipo_momento': 'ENTRADA',
            'nombre_cancion': 'Canon',
            'artista_cancion': 'Pachelbel',
            'orden_cancion': '0',
        })
        catering.refresh_from_db()
        decoracion.refresh_from_db()
        entretenimiento.refresh_from_db()
        cancion.refresh_from_db()
        self.assertEqual(catering.total_personas, 115)
        self.assertEqual(decoracion.nombre, 'Arco floral minimal')
        self.assertEqual(entretenimiento.nombre_artista, 'DJ Elegante Live')
        self.assertEqual(cancion.nombre_cancion, 'Canon')

        self.client.post('/dashboard/', {'accion': 'eliminar_cancion_evento', 'evento_id': evento.id, 'cancion_id': cancion.id})
        self.client.post('/dashboard/', {'accion': 'eliminar_entretenimiento_evento', 'evento_id': evento.id, 'entretenimiento_id': entretenimiento.id})
        self.client.post('/dashboard/', {'accion': 'eliminar_decoracion_evento', 'evento_id': evento.id, 'decoracion_id': decoracion.id})
        self.client.post('/dashboard/', {'accion': 'eliminar_catering_evento', 'evento_id': evento.id, 'catering_id': catering.id})
        self.assertFalse(CancionEvento.objects.filter(id=cancion.id).exists())
        self.assertFalse(EntretenimientoEvento.objects.filter(id=entretenimiento.id).exists())
        self.assertFalse(ElementoDecoracion.objects.filter(id=decoracion.id).exists())
        self.assertFalse(CateringEvento.objects.filter(id=catering.id).exists())

    def test_planner_asignado_edita_y_elimina_operacion_del_evento(self):
        User = get_user_model()
        empresa = EmpresaSuscriptora.objects.create(nombre_comercial='Casa Cisneros', slug='casa-cisneros')
        planner = User.objects.create_user(username='planner_operacion', password='test123')
        MembresiaEmpresa.objects.create(empresa=empresa, usuario=planner, rol='WEDDING_PLANNER')
        proveedor = Proveedor.objects.create(empresa=empresa, nombre_comercial='DJ Eventos')
        categoria = CategoriaGasto.objects.create(nombre='Musica')
        evento = crear_evento()
        evento.empresa = empresa
        evento.wedding_planner = planner
        evento.save()
        servicio = ServicioEvento.objects.create(evento=evento, proveedor=proveedor, nombre_servicio='DJ', estado='SOLICITADO')
        tarea = TareaEvento.objects.create(evento=evento, titulo='Enviar playlist')
        gasto = GastoEvento.objects.create(evento=evento, categoria=categoria, proveedor=proveedor, concepto='DJ', monto_estimado=12000)
        pago = PagoEvento.objects.create(gasto=gasto, monto=1000)
        documento = DocumentoEvento.objects.create(
            evento=evento,
            titulo='Cotizacion DJ',
            tipo_documento='COTIZACION',
            archivo=SimpleUploadedFile('cotizacion.pdf', b'%PDF-1.4', content_type='application/pdf'),
        )
        aprobacion = AprobacionEvento.objects.create(evento=evento, tipo='MUSICA', titulo='Playlist')
        self.client.force_login(planner)

        response = self.client.get(f'/dashboard/?evento={evento.id}')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Gestion operativa del evento')

        self.client.post('/dashboard/', {
            'accion': 'editar_servicio_evento',
            'evento_id': evento.id,
            'servicio_id': servicio.id,
            'proveedor_id': proveedor.id,
            'nombre_servicio': 'DJ y audio',
            'estado_servicio': 'APROBADO',
            'costo_total_servicio': '15000',
        })
        self.client.post('/dashboard/', {
            'accion': 'editar_tarea_evento',
            'evento_id': evento.id,
            'tarea_id': tarea.id,
            'titulo_tarea': 'Enviar playlist final',
            'estado_tarea': 'COMPLETADA',
            'prioridad_tarea': 'MEDIA',
            'categoria_tarea': 'MUSICA',
            'porcentaje_avance_tarea': '90',
        })
        self.client.post('/dashboard/', {
            'accion': 'editar_pago_evento',
            'evento_id': evento.id,
            'pago_id': pago.id,
            'monto_pago': '2500',
            'metodo_pago': 'EFECTIVO',
        })
        self.client.post('/dashboard/', {
            'accion': 'editar_aprobacion_evento',
            'evento_id': evento.id,
            'aprobacion_id': aprobacion.id,
            'tipo_aprobacion': 'MUSICA',
            'titulo_aprobacion': 'Playlist final',
            'estado_aprobacion': 'CAMBIOS',
            'comentario_aprobacion': 'Cliente pidio cambios',
        })

        servicio.refresh_from_db()
        tarea.refresh_from_db()
        pago.refresh_from_db()
        aprobacion.refresh_from_db()
        self.assertEqual(servicio.nombre_servicio, 'DJ y audio')
        self.assertEqual(servicio.estado, 'APROBADO')
        self.assertEqual(tarea.estado, 'COMPLETADA')
        self.assertEqual(tarea.porcentaje_avance, 100)
        self.assertEqual(pago.monto, 2500)
        self.assertEqual(aprobacion.estado, 'CAMBIOS')

        self.client.post('/dashboard/', {'accion': 'eliminar_documento_evento', 'evento_id': evento.id, 'documento_id': documento.id})
        self.client.post('/dashboard/', {'accion': 'eliminar_servicio_evento', 'evento_id': evento.id, 'servicio_id': servicio.id})
        self.assertFalse(DocumentoEvento.objects.filter(id=documento.id).exists())
        self.assertFalse(ServicioEvento.objects.filter(id=servicio.id).exists())

    def test_dashboard_guarda_sede_y_capacidad_del_evento(self):
        empresa = EmpresaSuscriptora.objects.create(nombre_comercial='Casa Cisneros', slug='casa-cisneros')
        sede = SedeEvento.objects.create(empresa=empresa, nombre='Salon Imperial', tipo='SALON', capacidad_maxima=200)
        evento = crear_evento()
        evento.empresa = empresa
        evento.save()

        response = self.client.post('/dashboard/', {
            'accion': 'personalizar_evento',
            'evento_id': evento.id,
            'empresa_id': empresa.id,
            'sede_id': sede.id,
            'tipo_evento': evento.tipo_evento,
            'estado': evento.estado,
            'nombre_evento': evento.nombre_evento or '',
            'nombre_principal': evento.nombre_principal or '',
            'nombre_secundario': evento.nombre_secundario or '',
            'etiqueta_principal': evento.etiqueta_principal,
            'etiqueta_secundario': evento.etiqueta_secundario,
            'paleta_colores': evento.paleta_colores,
            'paleta_sobre': evento.paleta_sobre,
            'estilo_letra': evento.estilo_letra,
            'texto_boton_sobre': evento.texto_boton_sobre,
            'capacidad_contratada': '180',
            'precio_por_persona': '950',
        })

        evento.refresh_from_db()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(evento.sede, sede)
        self.assertEqual(evento.capacidad_contratada, 180)
        self.assertEqual(evento.precio_por_persona, 950)

    def test_dashboard_no_permite_reasignar_evento_a_empresa_ajena(self):
        User = get_user_model()
        empresa = EmpresaSuscriptora.objects.create(nombre_comercial='Casa Cisneros', slug='casa-cisneros')
        otra_empresa = EmpresaSuscriptora.objects.create(nombre_comercial='Otro Salon', slug='otro-salon')
        admin_empresa = User.objects.create_user(username='admin_empresa_seguro', password='test123')
        MembresiaEmpresa.objects.create(empresa=empresa, usuario=admin_empresa, rol='ADMIN_EMPRESA')
        evento = crear_evento()
        evento.empresa = empresa
        evento.save()
        self.client.force_login(admin_empresa)
        self.client.raise_request_exception = False

        response = self.client.post('/dashboard/', {
            'accion': 'personalizar_evento',
            'evento_id': evento.id,
            'empresa_id': otra_empresa.id,
        })

        evento.refresh_from_db()
        self.assertEqual(response.status_code, 403)
        self.assertEqual(evento.empresa, empresa)
        self.assertTrue(
            RegistroAuditoria.objects.filter(
                empresa=empresa,
                evento=evento,
                accion='INTENTO_CAMBIO_EMPRESA_EVENTO',
            ).exists()
        )

    def test_dirtec_puede_reasignar_evento_a_otra_empresa(self):
        empresa = EmpresaSuscriptora.objects.create(nombre_comercial='Casa Cisneros', slug='casa-cisneros')
        otra_empresa = EmpresaSuscriptora.objects.create(nombre_comercial='Otro Salon', slug='otro-salon')
        evento = crear_evento()
        evento.empresa = empresa
        evento.save()

        response = self.client.post('/dashboard/', {
            'accion': 'personalizar_evento',
            'evento_id': evento.id,
            'empresa_id': otra_empresa.id,
        })

        evento.refresh_from_db()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(evento.empresa, otra_empresa)

    def test_calendario_no_expone_admin_a_usuarios_de_empresa(self):
        User = get_user_model()
        empresa = EmpresaSuscriptora.objects.create(nombre_comercial='Casa Cisneros', slug='casa-cisneros')
        admin_empresa = User.objects.create_user(username='admin_calendario', password='test123')
        MembresiaEmpresa.objects.create(empresa=empresa, usuario=admin_empresa, rol='ADMIN_EMPRESA')
        evento = crear_evento()
        evento.empresa = empresa
        evento.save()
        TareaEvento.objects.create(
            evento=evento,
            titulo='Confirmar banquete',
            fecha_limite=timezone.localdate() + timedelta(days=3),
        )
        self.client.force_login(admin_empresa)

        response = self.client.get(f'/api/calendario/eventos/?evento={evento.id}')

        self.assertEqual(response.status_code, 200)
        urls = [item['url'] for item in response.json()]
        self.assertTrue(urls)
        self.assertTrue(all('/admin/' not in url for url in urls))
        self.assertTrue(all(url == f'/dashboard/?evento={evento.id}#operacion' for url in urls))

    def test_calendario_expone_admin_solo_a_dirtec(self):
        evento = crear_evento()
        tarea = TareaEvento.objects.create(
            evento=evento,
            titulo='Confirmar banquete',
            fecha_limite=timezone.localdate() + timedelta(days=3),
        )

        response = self.client.get(f'/api/calendario/eventos/?evento={evento.id}')

        self.assertEqual(response.status_code, 200)
        urls = [item['url'] for item in response.json()]
        self.assertIn(f'/admin/tareas/tareaevento/{tarea.id}/change/', urls)

    def test_dashboard_crea_y_edita_persona_ceremonia(self):
        evento = crear_evento()

        response = self.client.post('/dashboard/', {
            'accion': 'agregar_persona_ceremonia',
            'evento_id': evento.id,
            'seccion_persona': 'PADRINOS',
            'etiqueta_persona': 'Padrinos de anillos',
            'nombre_persona': 'Jose y Ana',
            'visible_persona': 'on',
        })

        persona = PersonaCeremonia.objects.get(evento=evento)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(persona.nombre, 'Jose y Ana')

        self.client.post('/dashboard/', {
            'accion': 'editar_persona_ceremonia',
            'evento_id': evento.id,
            'persona_id': persona.id,
            'seccion_persona': 'PADRINOS',
            'etiqueta_persona': 'Padrinos',
            'nombre_persona': 'Jose, Ana y Luis',
            'orden_persona': '2',
            'visible_persona': 'on',
        })

        persona.refresh_from_db()
        self.assertEqual(persona.nombre, 'Jose, Ana y Luis')
        self.assertEqual(persona.orden, 2)

    def test_dashboard_edita_regalo_guardado(self):
        evento = crear_evento()
        regalo = EnlaceRegalo.objects.create(evento=evento, nombre='Liverpool', tipo='TIENDA')

        response = self.client.post('/dashboard/', {
            'accion': 'editar_regalo',
            'evento_id': evento.id,
            'regalo_id': regalo.id,
            'tipo_regalo': 'TIENDA',
            'nombre_regalo': 'Liverpool boda',
            'url_regalo': 'https://example.com/mesa',
            'visible': 'on',
        })

        regalo.refresh_from_db()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(regalo.nombre, 'Liverpool boda')
        self.assertEqual(regalo.url, 'https://example.com/mesa')

    def test_dashboard_crea_grupo_familiar_con_integrantes(self):
        evento = crear_evento()

        response = self.client.post('/dashboard/', {
            'accion': 'agregar_grupo',
            'evento_id': evento.id,
            'tipo_grupo': 'FAMILIAR',
            'nombre_grupo': 'Familia Perez',
            'telefono_contacto': '555',
            'cantidad_maxima': '2',
            'invitados_familia': 'Ana Perez | Adulto\nSofia Perez | Niño',
        })

        grupo = Grupoinvitacion.objects.get(evento=evento, nombre_grupo='Familia Perez')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(grupo.invitados.count(), 2)
        self.assertEqual(grupo.invitados.filter(tipo_persona='NINO').count(), 1)

    def test_dashboard_edita_y_elimina_invitado_familiar(self):
        evento = crear_evento()
        grupo = Grupoinvitacion.objects.create(evento=evento, nombre_grupo='Familia Perez', tipo='FAMILIAR')
        invitado = Invitado.objects.create(grupo=grupo, nombre='Ana', tipo_persona='ADULTO')

        self.client.post('/dashboard/', {
            'accion': 'editar_invitado',
            'evento_id': evento.id,
            'invitado_id': invitado.id,
            'nombre_invitado': 'Ana Perez',
            'tipo_persona': 'NINO',
            'orden_invitado': '3',
            'menu_infantil': 'on',
        })

        invitado.refresh_from_db()
        self.assertEqual(invitado.nombre, 'Ana Perez')
        self.assertEqual(invitado.tipo_persona, 'NINO')
        self.assertTrue(invitado.menu_infantil)

        response = self.client.post('/dashboard/', {
            'accion': 'eliminar_invitado',
            'evento_id': evento.id,
            'invitado_id': invitado.id,
        })

        self.assertEqual(response.status_code, 302)
        self.assertFalse(Invitado.objects.filter(id=invitado.id).exists())

    def test_regalo_con_datos_bancarios_se_guarda_como_deposito(self):
        evento = crear_evento()

        response = self.client.post('/dashboard/', {
            'accion': 'agregar_regalo',
            'evento_id': evento.id,
            'tipo_regalo': 'TIENDA',
            'nombre_regalo': 'Apoyo para los novios',
            'banco': 'NU',
            'titular': 'Diego Aldape',
            'clabe': '123456789012345678',
        })

        regalo = evento.regalos.get(nombre='Apoyo para los novios')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(regalo.tipo, 'DEPOSITO')

    def test_invitacion_muestra_regalo_bancario_sin_url(self):
        evento = crear_evento()
        grupo = Grupoinvitacion.objects.create(
            evento=evento,
            nombre_grupo='Carlos',
            tipo='PERSONAL',
        )
        evento.regalos.create(
            nombre='Cuenta bancaria',
            tipo='TIENDA',
            banco='NU',
            titular='Diego Aldape',
            clabe='123456789012345678',
        )

        response = self.client.get(f'/invitacion/{grupo.codigo}/')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Cuenta bancaria')
        self.assertContains(response, 'NU')

    def test_vista_previa_no_muestra_sobre_de_entrada(self):
        evento = crear_evento()
        grupo = Grupoinvitacion.objects.create(
            evento=evento,
            nombre_grupo='Carlos',
            tipo='PERSONAL',
        )

        response = self.client.get(f'/invitacion/{grupo.codigo}/?preview=1')

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'id="intro"')

    def test_dashboard_muestra_preview_embebido_o_creador_de_preview(self):
        evento = crear_evento()

        response = self.client.get(f'/dashboard/?evento={evento.id}')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'design-preview-layout')
        self.assertContains(response, 'Crear preview')
        self.assertContains(response, 'name="destino" value="personalizacion"')

        grupo = Grupoinvitacion.objects.create(
            evento=evento,
            nombre_grupo='Carlos',
            tipo='PERSONAL',
        )

        response = self.client.get(f'/dashboard/?evento={evento.id}')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, f'/invitacion/{grupo.codigo}/?preview=1')
        self.assertContains(response, 'data-preview-refresh')
        self.assertContains(response, 'data-preview-frame')

    def test_crear_preview_desde_diseno_regresa_a_personalizacion(self):
        evento = crear_evento()

        response = self.client.post('/dashboard/', {
            'accion': 'agregar_grupo',
            'evento_id': evento.id,
            'destino': 'personalizacion',
            'tipo_grupo': 'PERSONAL',
            'nombre_grupo': 'Invitado de prueba',
            'cantidad_extra_permitida': '1',
            'cantidad_maxima': '1',
        })

        grupo = Grupoinvitacion.objects.get(evento=evento, nombre_grupo='Invitado de prueba')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], f'/dashboard/?evento={evento.id}#personalizacion')
        self.assertEqual(grupo.tipo, 'PERSONAL')

    def test_dashboard_muestra_regalos_guardados(self):
        evento = crear_evento()
        evento.regalos.create(
            nombre='Cuenta bancaria',
            tipo='DEPOSITO',
            banco='NU',
            titular='Diego Aldape',
        )

        response = self.client.get(f'/dashboard/?evento={evento.id}')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Regalos guardados')
        self.assertContains(response, 'Cuenta bancaria')

    def test_dashboard_aplica_plantilla_predefinida(self):
        evento = crear_evento()

        response = self.client.post('/dashboard/', {
            'accion': 'personalizar_evento',
            'evento_id': evento.id,
            'tipo_evento': evento.tipo_evento,
            'estado': evento.estado,
            'nombre_evento': evento.nombre_evento or '',
            'nombre_principal': evento.nombre_principal or '',
            'nombre_secundario': evento.nombre_secundario or '',
            'etiqueta_principal': evento.etiqueta_principal,
            'etiqueta_secundario': evento.etiqueta_secundario,
            'paleta_colores': evento.paleta_colores,
            'paleta_sobre': evento.paleta_sobre,
            'estilo_letra': evento.estilo_letra,
            'texto_boton_sobre': evento.texto_boton_sobre,
            'plantilla_evento': 'XV',
        })

        evento.refresh_from_db()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(evento.tipo_evento, 'XV')
        self.assertEqual(evento.frase_portada, 'Mis XV años')
        self.assertEqual(evento.estilo_letra, 'ROMANTICA')
        self.assertFalse(evento.mostrar_nombre_secundario)
        self.assertTrue(evento.mostrar_album_compartido)
        self.assertEqual(evento.titulo_invitacion, 'Celebra conmigo')

        secciones = {seccion.tipo: seccion for seccion in evento.secciones_invitacion.all()}
        self.assertEqual(secciones['PADRES_PADRINOS'].titulo, 'Mis padres y padrinos')
        self.assertEqual(secciones['ITINERARIO'].titulo, 'Programa')
        self.assertTrue(secciones['DRESS_CODE'].activa)
        self.assertEqual(secciones['RSVP'].orden, 80)

    def test_dashboard_aplica_plantilla_bautizo_con_modulos_no_necesarios_ocultos(self):
        evento = crear_evento()

        response = self.client.post('/dashboard/', {
            'accion': 'personalizar_evento',
            'evento_id': evento.id,
            'plantilla_evento': 'BAUTIZO',
        })

        evento.refresh_from_db()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(evento.tipo_evento, 'BAUTIZO')
        self.assertFalse(evento.mostrar_regalos)
        self.assertTrue(evento.mostrar_album_compartido)
        self.assertEqual(evento.titulo_detalles, 'Ceremonia y celebracion')

        secciones = {seccion.tipo: seccion for seccion in evento.secciones_invitacion.all()}
        self.assertTrue(secciones['PADRES_PADRINOS'].activa)
        self.assertFalse(secciones['DRESS_CODE'].activa)
        self.assertFalse(secciones['REGALOS'].activa)
        self.assertEqual(secciones['PADRES_PADRINOS'].titulo, 'Padres y padrinos')

    def test_dashboard_sanitiza_google_maps_embed(self):
        evento = crear_evento()
        iframe = '<iframe src="https://www.google.com/maps/embed?pb=abc"></iframe>'

        response = self.client.post('/dashboard/', {
            'accion': 'personalizar_evento',
            'evento_id': evento.id,
            'mapa_misa_embed': iframe,
            'mapa_fiesta_embed': '<script>alert(1)</script>',
        })

        evento.refresh_from_db()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(evento.mapa_misa_embed, 'https://www.google.com/maps/embed?pb=abc')
        self.assertIsNone(evento.mapa_fiesta_embed)
        self.assertIn('<iframe', str(evento.mapa_misa_embed_html))

    def test_dashboard_rechaza_archivo_album_no_permitido(self):
        evento = crear_evento()
        archivo = SimpleUploadedFile('malware.exe', b'contenido', content_type='application/octet-stream')

        response = self.client.post('/dashboard/', {
            'accion': 'agregar_album',
            'evento_id': evento.id,
            'titulo_album_media': 'Archivo malo',
            'archivo_album': archivo,
        })

        self.assertEqual(response.status_code, 302)
        self.assertFalse(FotoEvento.objects.filter(evento=evento).exists())

    def test_dashboard_edita_y_elimina_archivo_de_album(self):
        User = get_user_model()
        admin = User.objects.create_superuser(username='dirtec_album_editar', password='test123')
        evento = crear_evento()
        foto = FotoEvento.objects.create(
            evento=evento,
            titulo='Original',
            imagen=SimpleUploadedFile('original.gif', b'gif-original', content_type='image/gif'),
            orden=1,
            visible=True,
        )
        self.client.force_login(admin)

        response = self.client.post('/dashboard/', {
            'accion': 'editar_album',
            'evento_id': evento.id,
            'foto_id': foto.id,
            'titulo_album_media': 'Video de entrada',
            'orden_album_media': '4',
            'archivo_album': SimpleUploadedFile('entrada.mp4', b'video-entrada', content_type='video/mp4'),
        })

        foto.refresh_from_db()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(foto.titulo, 'Video de entrada')
        self.assertEqual(foto.orden, 4)
        self.assertFalse(foto.visible)
        self.assertTrue(foto.imagen.name.endswith('.mp4'))

        response = self.client.post('/dashboard/', {
            'accion': 'eliminar_album',
            'evento_id': evento.id,
            'foto_id': foto.id,
        })

        self.assertEqual(response.status_code, 302)
        self.assertFalse(FotoEvento.objects.filter(id=foto.id).exists())

    def test_endpoint_metricas_responde_json(self):
        evento = crear_evento()
        grupo = Grupoinvitacion.objects.create(
            evento=evento,
            nombre_grupo='Carlos',
            tipo='PERSONAL',
            asistira=True,
            cantidad_extra_permitida=1,
            acompanantes_adultos=1,
        )
        grupo.confirmado = True
        grupo.save()

        response = self.client.get(f'/api/dashboard/metricas/?evento={evento.id}')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['resumen']['confirmados'], 2)

    def test_exportar_resumen_evento_descarga_excel(self):
        evento = crear_evento()

        response = self.client.get(f'/exportar-resumen/?evento={evento.id}')

        self.assertEqual(response.status_code, 200)
        self.assertIn(
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            response['Content-Type'],
        )

    def test_calendario_operativo_responde(self):
        evento = crear_evento()

        response = self.client.get(f'/dashboard/calendario/?evento={evento.id}')

        self.assertEqual(response.status_code, 200)

    def test_endpoint_calendario_devuelve_actividades(self):
        evento = crear_evento()
        ActividadItinerario.objects.create(
            evento=evento,
            titulo='Montaje',
            fecha=timezone.localdate(),
            hora_inicio=timezone.localtime().time(),
            categoria='MONTAJE',
        )

        response = self.client.get(f'/api/calendario/eventos/?evento={evento.id}')

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data[0]['title'], 'Montaje')
        self.assertEqual(data[0]['extendedProps']['tipo'], 'Actividad')


class PortalTests(TestCase):
    def test_portal_cliente_requiere_login(self):
        response = self.client.get('/portal/cliente/')

        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response['Location'])

    def test_portal_cliente_muestra_evento_asignado(self):
        User = get_user_model()
        user = User.objects.create_user(username='cliente', password='test123')
        evento = crear_evento()
        evento.clientes.add(user)
        self.client.force_login(user)

        response = self.client.get('/portal/cliente/')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Boda Diego &amp; Wendy')

    def test_portal_proveedor_muestra_servicio_asignado(self):
        User = get_user_model()
        user = User.objects.create_user(username='proveedor', password='test123')
        evento = crear_evento()
        proveedor = Proveedor.objects.create(
            usuario=user,
            nombre_comercial='Foto Luz',
            tipo_proveedor='FOTOGRAFIA',
        )
        ServicioEvento.objects.create(
            evento=evento,
            proveedor=proveedor,
            nombre_servicio='Cobertura completa',
        )
        self.client.force_login(user)

        response = self.client.get('/portal/proveedor/')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Cobertura completa')

    def test_proveedor_puede_actualizar_estado_de_su_servicio(self):
        User = get_user_model()
        user = User.objects.create_user(username='proveedor_estado', password='test123')
        evento = crear_evento()
        proveedor = Proveedor.objects.create(
            usuario=user,
            nombre_comercial='DJ Sol',
            tipo_proveedor='DJ',
        )
        servicio = ServicioEvento.objects.create(
            evento=evento,
            proveedor=proveedor,
            nombre_servicio='Musica',
        )
        self.client.force_login(user)

        response = self.client.post(
            f'/portal/proveedor/servicios/{servicio.id}/actualizar/',
            {'estado': 'CONTRATADO', 'nota': 'Confirmado'},
        )

        servicio.refresh_from_db()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(servicio.estado, 'CONTRATADO')
        self.assertIn('Confirmado', servicio.notas)

    def test_proveedor_no_puede_actualizar_servicio_ajeno(self):
        User = get_user_model()
        user = User.objects.create_user(username='proveedor_ajeno', password='test123')
        evento = crear_evento()
        proveedor = Proveedor.objects.create(
            usuario=user,
            nombre_comercial='Foto Propia',
            tipo_proveedor='FOTOGRAFIA',
        )
        otro_proveedor = Proveedor.objects.create(
            nombre_comercial='Foto Ajena',
            tipo_proveedor='FOTOGRAFIA',
        )
        servicio = ServicioEvento.objects.create(
            evento=evento,
            proveedor=otro_proveedor,
            nombre_servicio='Video',
        )
        self.client.force_login(user)

        response = self.client.post(
            f'/portal/proveedor/servicios/{servicio.id}/actualizar/',
            {'estado': 'CONTRATADO'},
        )

        servicio.refresh_from_db()
        self.assertEqual(response.status_code, 404)
        self.assertEqual(servicio.estado, 'SOLICITADO')
        self.assertTrue(proveedor.activo)

    def test_proveedor_puede_subir_documento(self):
        User = get_user_model()
        user = User.objects.create_user(username='proveedor_doc', password='test123')
        evento = crear_evento()
        proveedor = Proveedor.objects.create(
            usuario=user,
            nombre_comercial='Banquetes Norte',
            tipo_proveedor='BANQUETE',
        )
        ServicioEvento.objects.create(
            evento=evento,
            proveedor=proveedor,
            nombre_servicio='Cena',
        )
        archivo = SimpleUploadedFile('cotizacion.txt', b'cotizacion demo', content_type='text/plain')
        self.client.force_login(user)

        response = self.client.post('/portal/proveedor/documentos/subir/', {
            'evento_id': evento.id,
            'tipo_documento': 'COTIZACION',
            'titulo': 'Cotizacion inicial',
            'archivo': archivo,
            'descripcion': 'Version 1',
        })

        self.assertEqual(response.status_code, 302)
        self.assertTrue(DocumentoEvento.objects.filter(
            evento=evento,
            proveedor=proveedor,
            titulo='Cotizacion inicial',
        ).exists())

    def test_cliente_puede_aprobar_solicitud_asignada(self):
        User = get_user_model()
        planner = User.objects.create_user(username='planner_aprueba', password='test123')
        user = User.objects.create_user(username='cliente_aprueba', password='test123')
        evento = crear_evento()
        evento.wedding_planner = planner
        evento.save()
        evento.clientes.add(user)
        aprobacion = AprobacionEvento.objects.create(
            evento=evento,
            tipo='DECORACION',
            titulo='Decoracion floral',
        )
        self.client.force_login(user)

        response = self.client.post(
            f'/portal/cliente/aprobaciones/{aprobacion.id}/responder/',
            {'accion': 'aprobar', 'comentario': 'Se ve bien'},
        )

        aprobacion.refresh_from_db()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(aprobacion.estado, 'APROBADO')
        self.assertEqual(aprobacion.aprobado_por, user)
        self.assertEqual(aprobacion.comentario, 'Se ve bien')
        self.assertTrue(Notificacion.objects.filter(
            usuario=planner,
            tipo='APROBACION',
            titulo__contains='Decoracion floral',
        ).exists())

    def test_usuario_ajeno_no_puede_responder_aprobacion(self):
        User = get_user_model()
        user = User.objects.create_user(username='usuario_ajeno', password='test123')
        aprobacion = AprobacionEvento.objects.create(
            evento=crear_evento(),
            tipo='MENU',
            titulo='Menu principal',
        )
        self.client.force_login(user)

        response = self.client.post(
            f'/portal/cliente/aprobaciones/{aprobacion.id}/responder/',
            {'accion': 'aprobar'},
        )

        aprobacion.refresh_from_db()
        self.assertEqual(response.status_code, 403)
        self.assertEqual(aprobacion.estado, 'PENDIENTE')

    def test_cliente_puede_pedir_cambios(self):
        User = get_user_model()
        user = User.objects.create_user(username='cliente_cambios', password='test123')
        evento = crear_evento()
        evento.clientes.add(user)
        aprobacion = AprobacionEvento.objects.create(
            evento=evento,
            tipo='INVITACION',
            titulo='Diseno de invitacion',
        )
        self.client.force_login(user)

        self.client.post(
            f'/portal/cliente/aprobaciones/{aprobacion.id}/responder/',
            {'accion': 'cambios', 'comentario': 'Cambiar color principal'},
        )

        aprobacion.refresh_from_db()
        self.assertEqual(aprobacion.estado, 'CAMBIOS')
        self.assertEqual(aprobacion.comentario, 'Cambiar color principal')

    def test_proveedor_actualiza_servicio_y_notifica_planner(self):
        User = get_user_model()
        planner = User.objects.create_user(username='planner_servicio', password='test123')
        user = User.objects.create_user(username='proveedor_notifica', password='test123')
        evento = crear_evento()
        evento.wedding_planner = planner
        evento.save()
        proveedor = Proveedor.objects.create(
            usuario=user,
            nombre_comercial='Audio Centro',
            tipo_proveedor='AUDIO',
        )
        servicio = ServicioEvento.objects.create(
            evento=evento,
            proveedor=proveedor,
            nombre_servicio='Audio principal',
        )
        self.client.force_login(user)

        self.client.post(
            f'/portal/proveedor/servicios/{servicio.id}/actualizar/',
            {'estado': 'CONTRATADO'},
        )

        self.assertTrue(Notificacion.objects.filter(
            usuario=planner,
            tipo='PROVEEDOR',
            titulo__contains='Audio principal',
        ).exists())

    def test_documento_visible_notifica_cliente(self):
        User = get_user_model()
        planner = User.objects.create_user(username='planner_doc', password='test123')
        cliente = User.objects.create_user(username='cliente_doc', password='test123')
        user = User.objects.create_user(username='proveedor_doc_notifica', password='test123')
        evento = crear_evento()
        evento.wedding_planner = planner
        evento.save()
        evento.clientes.add(cliente)
        proveedor = Proveedor.objects.create(
            usuario=user,
            nombre_comercial='Salon Norte',
            tipo_proveedor='SALON',
        )
        ServicioEvento.objects.create(
            evento=evento,
            proveedor=proveedor,
            nombre_servicio='Salon',
        )
        archivo = SimpleUploadedFile('contrato.txt', b'contrato demo', content_type='text/plain')
        self.client.force_login(user)

        self.client.post('/portal/proveedor/documentos/subir/', {
            'evento_id': evento.id,
            'tipo_documento': 'CONTRATO',
            'titulo': 'Contrato salon',
            'archivo': archivo,
            'visible_cliente': 'on',
        })

        self.assertTrue(Notificacion.objects.filter(usuario=planner, tipo='DOCUMENTO').exists())
        self.assertTrue(Notificacion.objects.filter(usuario=cliente, tipo='DOCUMENTO').exists())

    def test_comando_genera_alertas_sin_duplicar(self):
        User = get_user_model()
        planner = User.objects.create_user(username='planner_alertas', password='test123')
        evento = crear_evento()
        evento.wedding_planner = planner
        evento.save()
        TareaEvento.objects.create(
            evento=evento,
            titulo='Tarea vencida',
            fecha_limite=timezone.localdate() - timedelta(days=1),
        )
        categoria = CategoriaGasto.objects.create(nombre='Gasto prueba')
        GastoEvento.objects.create(
            evento=evento,
            categoria=categoria,
            concepto='Pago vencido',
            monto_real=1000,
            fecha_limite=timezone.localdate() - timedelta(days=1),
        )

        call_command('generar_alertas_evento', evento=evento.id)
        call_command('generar_alertas_evento', evento=evento.id)

        self.assertEqual(Notificacion.objects.filter(usuario=planner, tipo='TAREA').count(), 1)
        self.assertEqual(Notificacion.objects.filter(usuario=planner, tipo='PAGO').count(), 1)
