import csv
import io
import json
import re
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.db.models.deletion import ProtectedError
from django.http import HttpResponse, JsonResponse
from django.db.models import Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.clickjacking import xframe_options_sameorigin
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.utils.crypto import get_random_string
from django.utils.text import slugify
from openpyxl import Workbook, load_workbook
from urllib.parse import quote

from .models import (
    AssetInvitacion,
    ComponenteInvitacion,
    DetalleProduccionEvento,
    DisenoInvitacion,
    EnlaceRegalo,
    EventoBoda,
    FotoEvento,
    Grupoinvitacion,
    Invitado,
    ItinerarioEvento,
    MenuBoda,
    PersonaCeremonia,
    PlantillaInvitacion,
    SeccionInvitacion,
    VersionDisenoInvitacion,
    es_video_archivo,
    google_maps_src,
)
from .permissions import (
    empresas_para_usuario,
    eventos_visibles_usuario,
    roles_activos_empresa,
    usuario_es_dirtec,
    usuario_puede_gestionar_catalogos,
    usuario_puede_gestionar_usuarios,
)
from catering.models import Alimento, CateringEvento, PaqueteBuffet
from decoracion.models import ElementoDecoracion
from entretenimiento.models import CancionEvento, EntretenimientoEvento
from itinerario.models import ActividadItinerario
from mesas.models import AsignacionMesa, Mesa
from paquetes.models import PaqueteBoda, PaqueteEvento
from presupuesto.models import CategoriaGasto, GastoEvento, PagoEvento
from proveedores.models import PersonalEvento, Proveedor, ServicioEvento
from suscripciones.models import PagoSuscripcion, PlanSuscripcion, SuscripcionEmpresa
from aprobaciones.models import AprobacionEvento
from documentos.models import DocumentoEvento
from notificaciones.models import Notificacion
from organizaciones.models import EmpresaSuscriptora, MembresiaEmpresa, SedeEvento
from tareas.models import TareaEvento
from core.services.auditoria import registrar_auditoria
from core.services.limites_plan import (
    LimitePlanExcedido,
    resumen_uso_plan,
    validar_limite_eventos_activos,
    validar_limite_clientes,
    validar_limite_planners,
    validar_limite_usuarios,
)


LOGIN_DASHBOARD_URL = '/login/'


ACCIONES_PANEL_EMPRESA_USUARIOS = {
    'crear_planner',
    'crear_cliente',
    'editar_usuario_empresa',
    'desactivar_usuario_empresa',
    'eliminar_usuario_empresa',
}
ACCIONES_PANEL_EMPRESA_CATALOGOS = {
    'crear_sede',
    'editar_sede',
    'desactivar_sede',
    'eliminar_sede',
    'crear_proveedor',
    'editar_proveedor',
    'desactivar_proveedor',
    'eliminar_proveedor',
    'crear_paquete',
    'editar_paquete',
    'desactivar_paquete',
    'eliminar_paquete',
}


def bloquear_accion_dashboard(request, empresa=None, evento=None, accion='', permiso=''):
    registrar_auditoria(
        usuario=request.user,
        empresa=empresa,
        evento=evento,
        accion='ACCESO_DENEGADO_DASHBOARD',
        modelo='Dashboard',
        objeto_id=getattr(empresa, 'id', '') or getattr(evento, 'id', ''),
        descripcion=f'Accion bloqueada: {accion}. Permiso requerido: {permiso}.',
        valores_nuevos={'accion_solicitada': accion, 'permiso_requerido': permiso},
        request=request,
    )
    raise PermissionDenied('No tienes permiso para realizar esta accion.')


def slug_empresa_unico(nombre):
    base = slugify(nombre) or 'empresa'
    slug = base
    contador = 2
    while EmpresaSuscriptora.objects.filter(slug=slug).exists():
        slug = f'{base}-{contador}'
        contador += 1
    return slug


def aplicar_datos_usuario_empresa(request, user, *, created=False, activar_default=True):
    user.first_name = limpiar_texto(request, 'first_name_usuario') or ''
    user.last_name = limpiar_texto(request, 'last_name_usuario') or ''
    user.email = limpiar_texto(request, 'email_usuario') or ''

    password = (request.POST.get('password_usuario') or '').strip()
    password_generada = None
    if password:
        user.set_password(password)
    elif created or not user.has_usable_password():
        password_generada = get_random_string(10)
        user.set_password(password_generada)

    user.is_active = bool_post(request, 'activo_usuario') if 'activo_usuario' in request.POST else activar_default
    user.is_staff = False
    user.is_superuser = False
    user.save()

    if password_generada:
        messages.warning(
            request,
            f'Contrasena temporal generada para {user.username}: {password_generada}. Compartela ahora por un canal seguro.',
        )
    return user


def crear_o_actualizar_usuario_empresa(request, empresa, rol_default='WEDDING_PLANNER'):
    username = limpiar_texto(request, 'username_usuario')
    if not empresa or not username:
        return None

    roles_validos = {valor for valor, _ in MembresiaEmpresa.ROLES}
    rol = request.POST.get('rol_usuario') if request.POST.get('rol_usuario') in roles_validos else rol_default
    User = get_user_model()
    user, created = User.objects.get_or_create(username=username)
    aplicar_datos_usuario_empresa(request, user, created=created)

    MembresiaEmpresa.objects.filter(empresa=empresa, usuario=user).exclude(rol=rol).update(activo=False)
    MembresiaEmpresa.objects.update_or_create(
        empresa=empresa,
        usuario=user,
        rol=rol,
        defaults={
            'activo': bool_post(request, 'activo_usuario'),
            'puede_gestionar_catalogos': bool_post(request, 'puede_gestionar_catalogos_usuario'),
        },
    )
    messages.success(request, f'Acceso listo: usuario {user.username} - rol {dict(MembresiaEmpresa.ROLES).get(rol, rol)}.')
    return user


def usuario_empresa_existente_activo(empresa, username, rol=None):
    if not username:
        return False
    filtros = {
        'empresa': empresa,
        'usuario__username': username,
        'activo': True,
    }
    if rol:
        filtros['rol'] = rol
    return MembresiaEmpresa.objects.filter(**filtros).exists()


def bloquear_por_limite_plan(request, empresa, mensaje, destino):
    messages.error(request, mensaje)
    registrar_auditoria(
        usuario=request.user,
        empresa=empresa,
        accion='LIMITE_PLAN_EXCEDIDO',
        modelo='EmpresaSuscriptora',
        objeto_id=empresa.id,
        descripcion=mensaje,
        request=request,
    )
    return redirect(f'/dashboard/empresa/?empresa={empresa.id}{destino}')


def fecha_hora_dashboard(request, campo, default=None):
    valor = request.POST.get(campo)
    if not valor:
        return default or timezone.now()
    try:
        fecha = datetime.strptime(valor, '%Y-%m-%dT%H:%M')
        return timezone.make_aware(fecha, timezone.get_current_timezone())
    except ValueError:
        return default or timezone.now()


def fecha_dashboard(request, campo, default=None):
    valor = request.POST.get(campo)
    if not valor:
        return default or timezone.localdate()
    try:
        return datetime.strptime(valor, '%Y-%m-%d').date()
    except ValueError:
        return default or timezone.localdate()


def hora_dashboard(request, campo, default=None):
    valor = request.POST.get(campo)
    if not valor:
        return default
    try:
        return datetime.strptime(valor, '%H:%M').time()
    except ValueError:
        return default


def resumen_eventos(eventos):
    eventos = eventos.select_related('empresa', 'sede', 'wedding_planner')
    hoy = timezone.localdate()
    return {
        'total': eventos.count(),
        'activos': eventos.filter(activo=True).count(),
        'proximos': eventos.filter(fecha_fiesta__date__gte=hoy).count(),
        'sin_planner': eventos.filter(wedding_planner__isnull=True).count(),
        'planeacion': eventos.filter(estado='PLANEACION').count(),
        'confirmados': eventos.filter(estado='CONFIRMADO').count(),
    }


def resumen_operativo_eventos(eventos):
    eventos_ids = list(eventos.values_list('id', flat=True))
    grupos = Grupoinvitacion.objects.filter(evento_id__in=eventos_ids)
    servicios = ServicioEvento.objects.filter(evento_id__in=eventos_ids)
    tareas = TareaEvento.objects.filter(evento_id__in=eventos_ids)
    gastos = GastoEvento.objects.filter(evento_id__in=eventos_ids)
    return {
        'invitaciones': grupos.count(),
        'confirmados': sum(grupo.lugares_asistiran for grupo in grupos),
        'pendientes_rsvp': sum(grupo.lugares_pendientes for grupo in grupos),
        'servicios_pendientes': servicios.exclude(
            estado__in=['CONTRATADO', 'ANTICIPO_PAGADO', 'LIQUIDADO', 'SERVICIO_COMPLETADO']
        ).count(),
        'tareas_pendientes': tareas.exclude(estado__in=['COMPLETADA', 'CANCELADA']).count(),
        'tareas_vencidas': sum(1 for tarea in tareas if tarea.esta_vencida),
        'pagos_vencidos': sum(1 for gasto in gastos if gasto.esta_vencido),
    }


def empresa_dashboard_autorizada(request, roles_permitidos=None):
    empresa_id = request.GET.get('empresa') or request.POST.get('empresa_id')
    empresas = empresas_para_usuario(request.user)
    if empresa_id:
        empresa = get_object_or_404(empresas, id=empresa_id)
    else:
        empresa = empresas.first()
    if not empresa:
        return None, empresas
    roles = roles_activos_empresa(request.user, empresa)
    if roles_permitidos and not roles.intersection(set(roles_permitidos)):
        return None, empresas
    return empresa, empresas


def crear_evento_para_empresa(request, empresa):
    nombre_evento = limpiar_texto(request, 'nombre_evento') or 'Nuevo evento'
    principal = limpiar_texto(request, 'nombre_principal') or nombre_evento
    secundario = limpiar_texto(request, 'nombre_secundario') or ''
    fecha_evento = fecha_hora_dashboard(request, 'fecha_evento')
    sede = None
    sede_id = request.POST.get('sede_id')
    if sede_id:
        sede = SedeEvento.objects.filter(empresa=empresa, id=sede_id, activa=True).first()

    evento = EventoBoda.objects.create(
        empresa=empresa,
        sede=sede,
        nombre_evento=nombre_evento,
        tipo_evento=request.POST.get('tipo_evento') or 'BODA',
        estado='PLANEACION',
        novio=principal,
        novia=secundario or principal,
        nombre_principal=principal,
        nombre_secundario=secundario,
        mostrar_nombre_secundario=bool(secundario),
        frase_portada=limpiar_texto(request, 'frase_portada') or nombre_evento,
        mensaje_general='Estamos preparando todos los detalles de este evento.',
        fecha_misa=fecha_evento,
        lugar_misa=limpiar_texto(request, 'lugar_ceremonia') or (sede.nombre if sede else 'Ceremonia'),
        fecha_fiesta=fecha_evento,
        lugar_fiesta=limpiar_texto(request, 'lugar_recepcion') or (sede.nombre if sede else 'Recepcion'),
        capacidad_contratada=convertir_entero(request.POST.get('capacidad_contratada'), 0),
    )
    planner_id = request.POST.get('planner_id')
    if planner_id:
        membresia = MembresiaEmpresa.objects.filter(
            empresa=empresa,
            usuario_id=planner_id,
            rol='WEDDING_PLANNER',
            activo=True,
        ).select_related('usuario').first()
        if membresia:
            evento.wedding_planner = membresia.usuario
            evento.save(update_fields=['wedding_planner'])
    return evento


def crear_plan_suscripcion_dirtec(request):
    nombre = limpiar_texto(request, 'nombre_plan')
    if not nombre:
        return None
    plan = PlanSuscripcion.objects.create(
        nombre=nombre,
        descripcion=limpiar_texto(request, 'descripcion_plan') or '',
        precio_mensual=convertir_decimal(request.POST.get('precio_mensual_plan'), 0),
        precio_anual=convertir_decimal(request.POST.get('precio_anual_plan'), 0) or None,
        limite_usuarios=convertir_entero(request.POST.get('limite_usuarios_plan'), 5),
        limite_wedding_planners=convertir_entero(request.POST.get('limite_planners_plan'), 3),
        limite_eventos_activos=convertir_entero(request.POST.get('limite_eventos_plan'), 10),
        limite_clientes=convertir_entero(request.POST.get('limite_clientes_plan'), 50),
        limite_almacenamiento_mb=convertir_entero(request.POST.get('limite_almacenamiento_plan'), 1024),
        permite_proveedores=bool_post(request, 'permite_proveedores_plan'),
        permite_reportes=bool_post(request, 'permite_reportes_plan'),
        permite_api=bool_post(request, 'permite_api_plan'),
        permite_personalizacion=bool_post(request, 'permite_personalizacion_plan'),
        activo=bool_post(request, 'activo_plan'),
    )
    registrar_auditoria(
        usuario=request.user,
        accion='CREAR_PLAN_SUSCRIPCION',
        modelo='PlanSuscripcion',
        objeto_id=plan.id,
        descripcion=f'DIRTEC creo el plan {plan.nombre}.',
        request=request,
    )
    return plan


def actualizar_plan_suscripcion_dirtec(request):
    plan = get_object_or_404(PlanSuscripcion, id=request.POST.get('plan_id'))
    nombre = limpiar_texto(request, 'nombre_plan')
    if nombre:
        plan.nombre = nombre
    plan.descripcion = limpiar_texto(request, 'descripcion_plan') or ''
    plan.precio_mensual = convertir_decimal(request.POST.get('precio_mensual_plan'), plan.precio_mensual)
    plan.precio_anual = convertir_decimal(request.POST.get('precio_anual_plan'), 0) or None
    plan.limite_usuarios = convertir_entero(request.POST.get('limite_usuarios_plan'), plan.limite_usuarios)
    plan.limite_wedding_planners = convertir_entero(request.POST.get('limite_planners_plan'), plan.limite_wedding_planners)
    plan.limite_eventos_activos = convertir_entero(request.POST.get('limite_eventos_plan'), plan.limite_eventos_activos)
    plan.limite_clientes = convertir_entero(request.POST.get('limite_clientes_plan'), plan.limite_clientes)
    plan.limite_almacenamiento_mb = convertir_entero(request.POST.get('limite_almacenamiento_plan'), plan.limite_almacenamiento_mb)
    plan.permite_proveedores = bool_post(request, 'permite_proveedores_plan')
    plan.permite_reportes = bool_post(request, 'permite_reportes_plan')
    plan.permite_api = bool_post(request, 'permite_api_plan')
    plan.permite_personalizacion = bool_post(request, 'permite_personalizacion_plan')
    plan.activo = bool_post(request, 'activo_plan')
    plan.save()

    registrar_auditoria(
        usuario=request.user,
        accion='ACTUALIZAR_PLAN_SUSCRIPCION',
        modelo='PlanSuscripcion',
        objeto_id=plan.id,
        descripcion=f'DIRTEC actualizo el plan {plan.nombre}.',
        request=request,
    )
    messages.success(request, f'Plan actualizado: {plan.nombre}.')
    return plan


def eliminar_plan_suscripcion_dirtec(request):
    plan = get_object_or_404(PlanSuscripcion, id=request.POST.get('plan_id'))
    plan_id = plan.id
    nombre = plan.nombre
    try:
        plan.delete()
        messages.success(request, f'Plan eliminado: {nombre}.')
        accion = 'ELIMINAR_PLAN_SUSCRIPCION'
    except ProtectedError:
        plan.activo = False
        plan.save(update_fields=['activo', 'fecha_actualizacion'])
        messages.error(request, f'El plan {nombre} tiene suscripciones asociadas; se desactivo para no romper historial.')
        accion = 'DESACTIVAR_PLAN_SUSCRIPCION'

    registrar_auditoria(
        usuario=request.user,
        accion=accion,
        modelo='PlanSuscripcion',
        objeto_id=plan_id,
        descripcion=f'DIRTEC proceso baja del plan {nombre}.',
        request=request,
    )
    return plan_id


def crear_empresa_saas_dirtec(request):
    nombre = limpiar_texto(request, 'nombre_empresa')
    if not nombre:
        return None
    plan = get_object_or_404(PlanSuscripcion, id=request.POST.get('plan_suscripcion_id'), activo=True)
    fecha_inicio = fecha_dashboard(request, 'fecha_inicio_suscripcion')
    fecha_vencimiento = fecha_dashboard(request, 'fecha_vencimiento_suscripcion', fecha_inicio)
    estado_suscripcion = request.POST.get('estado_suscripcion') or 'ACTIVA'
    estados_validos = {valor for valor, _ in SuscripcionEmpresa.ESTADOS}
    if estado_suscripcion not in estados_validos:
        estado_suscripcion = 'ACTIVA'

    with transaction.atomic():
        empresa = EmpresaSuscriptora.objects.create(
            nombre_comercial=nombre,
            razon_social=limpiar_texto(request, 'razon_social'),
            slug=slug_empresa_unico(nombre),
            rfc=limpiar_texto(request, 'rfc_empresa') or '',
            contacto_nombre=limpiar_texto(request, 'contacto_nombre'),
            contacto_email=limpiar_texto(request, 'contacto_email'),
            contacto_telefono=limpiar_texto(request, 'contacto_telefono'),
            direccion=limpiar_texto(request, 'direccion_empresa') or '',
            estado='ACTIVA' if bool_post(request, 'empresa_activa') else 'INACTIVA',
            plan='PROFESIONAL',
            max_eventos_activos=plan.limite_eventos_activos,
            max_usuarios=plan.limite_usuarios,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_vencimiento,
            activo=bool_post(request, 'empresa_activa'),
        )
        if request.FILES.get('logotipo_empresa'):
            empresa.logotipo = request.FILES['logotipo_empresa']
        colores_marca = {
            'primario': limpiar_texto(request, 'color_primario_empresa'),
            'secundario': limpiar_texto(request, 'color_secundario_empresa'),
        }
        empresa.colores_marca = {clave: valor for clave, valor in colores_marca.items() if valor}
        if empresa.logotipo or empresa.colores_marca:
            empresa.save(update_fields=['logotipo', 'colores_marca', 'fecha_actualizacion'])
        suscripcion = SuscripcionEmpresa.objects.create(
            empresa=empresa,
            plan=plan,
            fecha_inicio=fecha_inicio,
            fecha_vencimiento=fecha_vencimiento,
            fecha_periodo_gracia=fecha_dashboard(request, 'fecha_periodo_gracia_suscripcion', None) if request.POST.get('fecha_periodo_gracia_suscripcion') else None,
            estado=estado_suscripcion,
            renovacion_automatica=bool_post(request, 'renovacion_automatica'),
            observaciones=limpiar_texto(request, 'observaciones_suscripcion') or '',
        )
        monto_inicial = convertir_decimal(request.POST.get('monto_pago_inicial'), 0)
        if monto_inicial > 0:
            PagoSuscripcion.objects.create(
                empresa=empresa,
                suscripcion=suscripcion,
                monto=monto_inicial,
                fecha_vencimiento=fecha_dashboard(request, 'fecha_vencimiento_pago', fecha_vencimiento),
                fecha_pago=fecha_dashboard(request, 'fecha_pago_inicial', None) if request.POST.get('fecha_pago_inicial') else None,
                metodo_pago=limpiar_texto(request, 'metodo_pago_inicial') or '',
                referencia=limpiar_texto(request, 'referencia_pago_inicial') or '',
                estado=request.POST.get('estado_pago_inicial') or 'PENDIENTE',
                registrado_por=request.user,
                notas=limpiar_texto(request, 'notas_pago_inicial') or '',
            )
        if limpiar_texto(request, 'username_usuario'):
            crear_o_actualizar_usuario_empresa(request, empresa, 'ADMIN_EMPRESA')

        registrar_auditoria(
            usuario=request.user,
            empresa=empresa,
            accion='CREAR_EMPRESA_SAAS',
            modelo='EmpresaSuscriptora',
            objeto_id=empresa.id,
            descripcion=f'DIRTEC creo la empresa {empresa.nombre_comercial} con suscripcion {suscripcion.id}.',
            valores_nuevos={'plan': plan.nombre, 'estado_suscripcion': suscripcion.estado},
            request=request,
        )
    return empresa


def actualizar_empresa_dirtec(request):
    empresa = get_object_or_404(EmpresaSuscriptora, id=request.POST.get('empresa_id'))
    estados_validos = {valor for valor, _ in EmpresaSuscriptora.ESTADOS}
    planes_validos = {valor for valor, _ in EmpresaSuscriptora.PLANES}
    estado = request.POST.get('estado_empresa')
    plan = request.POST.get('plan_empresa')

    empresa.nombre_comercial = limpiar_texto(request, 'nombre_empresa') or empresa.nombre_comercial
    empresa.razon_social = limpiar_texto(request, 'razon_social')
    empresa.rfc = limpiar_texto(request, 'rfc_empresa') or ''
    empresa.contacto_nombre = limpiar_texto(request, 'contacto_nombre')
    empresa.contacto_email = limpiar_texto(request, 'contacto_email')
    empresa.contacto_telefono = limpiar_texto(request, 'contacto_telefono')
    empresa.direccion = limpiar_texto(request, 'direccion_empresa') or ''
    empresa.notas = limpiar_texto(request, 'notas_empresa')
    if request.FILES.get('logotipo_empresa'):
        empresa.logotipo = request.FILES['logotipo_empresa']
    colores_marca = {
        'primario': limpiar_texto(request, 'color_primario_empresa'),
        'secundario': limpiar_texto(request, 'color_secundario_empresa'),
    }
    empresa.colores_marca = {clave: valor for clave, valor in colores_marca.items() if valor}
    empresa.max_eventos_activos = convertir_entero(request.POST.get('max_eventos_activos'), empresa.max_eventos_activos)
    empresa.max_usuarios = convertir_entero(request.POST.get('max_usuarios'), empresa.max_usuarios)
    empresa.fecha_inicio = fecha_dashboard(request, 'fecha_inicio_empresa', None) if request.POST.get('fecha_inicio_empresa') else None
    empresa.fecha_fin = fecha_dashboard(request, 'fecha_fin_empresa', None) if request.POST.get('fecha_fin_empresa') else None
    if estado in estados_validos:
        empresa.estado = estado
    if plan in planes_validos:
        empresa.plan = plan
    empresa.activo = bool_post(request, 'empresa_activa')
    empresa.save()

    registrar_auditoria(
        usuario=request.user,
        empresa=empresa,
        accion='ACTUALIZAR_EMPRESA_DIRTEC',
        modelo='EmpresaSuscriptora',
        objeto_id=empresa.id,
        descripcion=f'DIRTEC actualizo la empresa {empresa.nombre_comercial}.',
        request=request,
    )
    return empresa


def desactivar_empresa_dirtec(request):
    empresa = get_object_or_404(EmpresaSuscriptora, id=request.POST.get('empresa_id'))
    empresa.activo = False
    empresa.estado = 'INACTIVA'
    empresa.save(update_fields=['activo', 'estado', 'fecha_actualizacion'])
    MembresiaEmpresa.objects.filter(empresa=empresa).update(activo=False)
    registrar_auditoria(
        usuario=request.user,
        empresa=empresa,
        accion='DESACTIVAR_EMPRESA_DIRTEC',
        modelo='EmpresaSuscriptora',
        objeto_id=empresa.id,
        descripcion=f'DIRTEC desactivo la empresa {empresa.nombre_comercial}.',
        request=request,
    )
    return empresa


def eliminar_empresa_dirtec(request):
    empresa = get_object_or_404(EmpresaSuscriptora, id=request.POST.get('empresa_id'))
    empresa_id = empresa.id
    nombre = empresa.nombre_comercial
    registrar_auditoria(
        usuario=request.user,
        empresa=empresa,
        accion='ELIMINAR_EMPRESA_DIRTEC',
        modelo='EmpresaSuscriptora',
        objeto_id=empresa.id,
        descripcion=f'DIRTEC elimino definitivamente la empresa {nombre}.',
        request=request,
    )

    with transaction.atomic():
        EventoBoda.objects.filter(empresa=empresa).delete()
        Proveedor.objects.filter(empresa=empresa).delete()
        for paquete in PaqueteBoda.objects.filter(empresa=empresa):
            paquete.eventos.all().delete()
            paquete.delete()
        empresa.delete()

    messages.success(request, f'Empresa eliminada: {nombre}.')
    return empresa_id


def actualizar_suscripcion_dirtec(request):
    suscripcion = get_object_or_404(SuscripcionEmpresa.objects.select_related('empresa'), id=request.POST.get('suscripcion_id'))
    plan = get_object_or_404(PlanSuscripcion, id=request.POST.get('plan_suscripcion_id'), activo=True)
    estados_validos = {valor for valor, _ in SuscripcionEmpresa.ESTADOS}
    estado = request.POST.get('estado_suscripcion') if request.POST.get('estado_suscripcion') in estados_validos else suscripcion.estado
    anteriores = {
        'plan': suscripcion.plan_id,
        'estado': suscripcion.estado,
        'fecha_vencimiento': str(suscripcion.fecha_vencimiento),
        'bloqueada_manualmente': suscripcion.bloqueada_manualmente,
    }

    suscripcion.plan = plan
    suscripcion.fecha_inicio = fecha_dashboard(request, 'fecha_inicio_suscripcion', suscripcion.fecha_inicio)
    suscripcion.fecha_vencimiento = fecha_dashboard(request, 'fecha_vencimiento_suscripcion', suscripcion.fecha_vencimiento)
    suscripcion.fecha_periodo_gracia = fecha_dashboard(request, 'fecha_periodo_gracia_suscripcion', None) if request.POST.get('fecha_periodo_gracia_suscripcion') else None
    suscripcion.estado = estado
    suscripcion.renovacion_automatica = bool_post(request, 'renovacion_automatica')
    suscripcion.bloqueada_manualmente = bool_post(request, 'bloqueada_manualmente')
    suscripcion.motivo_bloqueo = limpiar_texto(request, 'motivo_bloqueo') or ''
    suscripcion.observaciones = limpiar_texto(request, 'observaciones_suscripcion') or ''
    suscripcion.save()

    empresa = suscripcion.empresa
    empresa.estado = 'BLOQUEADA' if suscripcion.bloqueada_manualmente else ('SUSPENDIDA' if estado == 'SUSPENDIDA' else 'ACTIVA')
    empresa.activo = estado not in {'SUSPENDIDA', 'CANCELADA'} and not suscripcion.bloqueada_manualmente
    empresa.fecha_inicio = suscripcion.fecha_inicio
    empresa.fecha_fin = suscripcion.fecha_vencimiento
    empresa.max_eventos_activos = plan.limite_eventos_activos
    empresa.max_usuarios = plan.limite_usuarios
    empresa.save(update_fields=['estado', 'activo', 'fecha_inicio', 'fecha_fin', 'max_eventos_activos', 'max_usuarios', 'fecha_actualizacion'])

    registrar_auditoria(
        usuario=request.user,
        empresa=empresa,
        accion='ACTUALIZAR_SUSCRIPCION',
        modelo='SuscripcionEmpresa',
        objeto_id=suscripcion.id,
        descripcion=f'DIRTEC actualizo la suscripcion de {empresa.nombre_comercial}.',
        valores_anteriores=anteriores,
        valores_nuevos={
            'plan': plan.id,
            'estado': suscripcion.estado,
            'fecha_vencimiento': str(suscripcion.fecha_vencimiento),
            'bloqueada_manualmente': suscripcion.bloqueada_manualmente,
        },
        request=request,
    )
    return suscripcion


def registrar_pago_suscripcion_dirtec(request):
    suscripcion = get_object_or_404(SuscripcionEmpresa.objects.select_related('empresa'), id=request.POST.get('suscripcion_id'))
    estado = request.POST.get('estado_pago') or 'PENDIENTE'
    estados_validos = {valor for valor, _ in PagoSuscripcion.ESTADOS}
    if estado not in estados_validos:
        estado = 'PENDIENTE'
    pago = PagoSuscripcion.objects.create(
        empresa=suscripcion.empresa,
        suscripcion=suscripcion,
        monto=convertir_decimal(request.POST.get('monto_pago'), 0),
        fecha_vencimiento=fecha_dashboard(request, 'fecha_vencimiento_pago', timezone.localdate()),
        fecha_pago=fecha_dashboard(request, 'fecha_pago', None) if request.POST.get('fecha_pago') else None,
        metodo_pago=limpiar_texto(request, 'metodo_pago') or '',
        referencia=limpiar_texto(request, 'referencia_pago') or '',
        estado=estado,
        registrado_por=request.user,
        notas=limpiar_texto(request, 'notas_pago') or '',
    )
    if pago.estado == 'PAGADO':
        suscripcion.estado = 'ACTIVA'
        suscripcion.bloqueada_manualmente = False
        suscripcion.motivo_bloqueo = ''
        suscripcion.save(update_fields=['estado', 'bloqueada_manualmente', 'motivo_bloqueo', 'fecha_actualizacion'])
        suscripcion.empresa.estado = 'ACTIVA'
        suscripcion.empresa.activo = True
        suscripcion.empresa.save(update_fields=['estado', 'activo', 'fecha_actualizacion'])
    registrar_auditoria(
        usuario=request.user,
        empresa=suscripcion.empresa,
        accion='REGISTRAR_PAGO_SUSCRIPCION',
        modelo='PagoSuscripcion',
        objeto_id=pago.id,
        descripcion=f'DIRTEC registro pago de suscripcion por {pago.monto}.',
        request=request,
    )
    return pago


def planner_activo_empresa(empresa, planner_id):
    if not planner_id:
        return None
    membresia = MembresiaEmpresa.objects.filter(
        empresa=empresa,
        usuario_id=planner_id,
        rol='WEDDING_PLANNER',
        activo=True,
    ).select_related('usuario').first()
    return membresia.usuario if membresia else None


def actualizar_evento_empresa_dashboard(request, empresa):
    evento = get_object_or_404(EventoBoda, empresa=empresa, id=request.POST.get('evento_id'))
    tipos_validos = {valor for valor, _ in EventoBoda.TIPOS_EVENTO}
    estados_validos = {valor for valor, _ in EventoBoda.ESTADOS_EVENTO}
    tipo_evento = request.POST.get('tipo_evento')
    estado = request.POST.get('estado')
    sede_id = request.POST.get('sede_id')
    principal = limpiar_texto(request, 'nombre_principal') or evento.nombre_principal or evento.novio
    secundario = limpiar_texto(request, 'nombre_secundario') or ''

    evento.nombre_evento = limpiar_texto(request, 'nombre_evento') or evento.nombre_evento
    if tipo_evento in tipos_validos:
        evento.tipo_evento = tipo_evento
    if estado in estados_validos:
        evento.estado = estado
    evento.nombre_principal = principal
    evento.nombre_secundario = secundario
    evento.novio = principal
    evento.novia = secundario or principal
    evento.mostrar_nombre_secundario = bool(secundario)
    evento.fecha_fiesta = fecha_hora_dashboard(request, 'fecha_evento', evento.fecha_fiesta)
    evento.fecha_misa = fecha_hora_dashboard(request, 'fecha_ceremonia', evento.fecha_misa)
    evento.lugar_misa = limpiar_texto(request, 'lugar_ceremonia') or evento.lugar_misa
    evento.lugar_fiesta = limpiar_texto(request, 'lugar_recepcion') or evento.lugar_fiesta
    evento.capacidad_contratada = convertir_entero(request.POST.get('capacidad_contratada'), evento.capacidad_contratada)
    evento.frase_portada = limpiar_texto(request, 'frase_portada') or evento.frase_portada
    evento.activo = bool_post(request, 'activo_evento')

    evento.sede = SedeEvento.objects.filter(empresa=empresa, id=sede_id).first() if sede_id else None
    evento.wedding_planner = planner_activo_empresa(empresa, request.POST.get('planner_id'))
    evento.save()
    return evento


def actualizar_usuario_empresa_dashboard(request, empresa):
    membresia = get_object_or_404(
        MembresiaEmpresa.objects.select_related('usuario'),
        empresa=empresa,
        id=request.POST.get('membresia_id'),
    )
    roles_validos = {valor for valor, _ in MembresiaEmpresa.ROLES}
    rol = request.POST.get('rol_usuario') if request.POST.get('rol_usuario') in roles_validos else membresia.rol
    activo = bool_post(request, 'activo_usuario')
    puede_catalogos = bool_post(request, 'puede_gestionar_catalogos_usuario')
    user = membresia.usuario
    user.first_name = limpiar_texto(request, 'first_name_usuario') or user.first_name
    user.last_name = limpiar_texto(request, 'last_name_usuario') or user.last_name
    user.email = limpiar_texto(request, 'email_usuario') or user.email
    password = request.POST.get('password_usuario')
    if password:
        user.set_password(password)
    user.is_active = activo
    user.save()

    if rol != membresia.rol:
        destino = MembresiaEmpresa.objects.filter(
            empresa=empresa,
            usuario=user,
            rol=rol,
        ).exclude(id=membresia.id).first()
        if destino:
            destino.activo = activo
            destino.puede_gestionar_catalogos = puede_catalogos
            destino.save(update_fields=['activo', 'puede_gestionar_catalogos'])
            membresia.activo = False
            membresia.save(update_fields=['activo'])
            return destino
        membresia.rol = rol

    membresia.activo = activo
    membresia.puede_gestionar_catalogos = puede_catalogos
    membresia.save(update_fields=['rol', 'activo', 'puede_gestionar_catalogos'])
    return membresia


def desactivar_usuario_empresa_dashboard(request, empresa):
    membresia = get_object_or_404(MembresiaEmpresa, empresa=empresa, id=request.POST.get('membresia_id'))
    if membresia.usuario_id == request.user.id:
        return membresia
    membresia.activo = False
    membresia.save(update_fields=['activo'])
    if not MembresiaEmpresa.objects.filter(usuario=membresia.usuario, activo=True).exists():
        membresia.usuario.is_active = False
        membresia.usuario.save(update_fields=['is_active'])
    return membresia


def eliminar_usuario_empresa_dashboard(request, empresa):
    membresia = get_object_or_404(
        MembresiaEmpresa.objects.select_related('usuario'),
        empresa=empresa,
        id=request.POST.get('membresia_id'),
    )
    if membresia.usuario_id == request.user.id:
        messages.error(request, 'No puedes eliminar tu propio acceso desde este panel.')
        return membresia

    user = membresia.usuario
    rol = membresia.rol
    username = user.username
    membresia.delete()

    if not user.is_staff and not user.is_superuser and not MembresiaEmpresa.objects.filter(usuario=user).exists():
        user.delete()

    registrar_auditoria(
        usuario=request.user,
        empresa=empresa,
        accion='ELIMINAR_USUARIO_EMPRESA',
        modelo='MembresiaEmpresa',
        objeto_id=request.POST.get('membresia_id'),
        descripcion=f'Se elimino el acceso {rol} de {username} en {empresa.nombre_comercial}.',
        request=request,
    )
    messages.success(request, f'Usuario eliminado del panel: {username}.')
    return rol


def crear_cliente_empresa_dashboard(request, empresa):
    user = crear_o_actualizar_usuario_empresa(request, empresa, 'CLIENTE')
    evento_id = request.POST.get('evento_cliente_id')
    if user and evento_id:
        evento = get_object_or_404(EventoBoda, empresa=empresa, id=evento_id)
        evento.clientes.add(user)
    if user:
        registrar_auditoria(
            usuario=request.user,
            empresa=empresa,
            accion='CREAR_CLIENTE_EMPRESA',
            modelo='auth.User',
            objeto_id=user.id,
            descripcion=f'Se creo o actualizo cliente {user.username} desde dashboard de empresa.',
            request=request,
        )
    return user


def crear_evento_planner_dashboard(request, empresa):
    post = request.POST.copy()
    post['planner_id'] = str(request.user.id)
    request.POST = post
    evento = crear_evento_para_empresa(request, empresa)
    if evento.wedding_planner_id != request.user.id:
        evento.wedding_planner = request.user
        evento.save(update_fields=['wedding_planner'])
    registrar_auditoria(
        usuario=request.user,
        empresa=empresa,
        evento=evento,
        accion='CREAR_EVENTO_PLANNER',
        modelo='EventoBoda',
        objeto_id=evento.id,
        descripcion=f'Wedding planner creo evento {evento}.',
        request=request,
    )
    return evento


def actualizar_sede_empresa_dashboard(request, empresa):
    sede = get_object_or_404(SedeEvento, empresa=empresa, id=request.POST.get('sede_id'))
    tipos_validos = {valor for valor, _ in SedeEvento.TIPOS}
    tipo = request.POST.get('tipo_sede')
    sede.nombre = limpiar_texto(request, 'nombre_sede') or sede.nombre
    if tipo in tipos_validos:
        sede.tipo = tipo
    sede.capacidad_minima = convertir_entero(request.POST.get('capacidad_minima'), sede.capacidad_minima)
    sede.capacidad_maxima = convertir_entero(request.POST.get('capacidad_maxima'), sede.capacidad_maxima)
    sede.precio_base = convertir_decimal(request.POST.get('precio_base_sede'), sede.precio_base)
    sede.direccion = limpiar_texto(request, 'direccion_sede')
    sede.descripcion = limpiar_texto(request, 'descripcion_sede')
    sede.activa = bool_post(request, 'activa_sede')
    sede.save()
    return sede


def actualizar_proveedor_empresa_dashboard(request, empresa):
    proveedor = get_object_or_404(Proveedor, empresa=empresa, id=request.POST.get('proveedor_id'))
    tipos_validos = {valor for valor, _ in Proveedor.TIPOS}
    tipo = request.POST.get('tipo_proveedor')
    proveedor.nombre_comercial = limpiar_texto(request, 'nombre_proveedor') or proveedor.nombre_comercial
    if tipo in tipos_validos:
        proveedor.tipo_proveedor = tipo
    proveedor.nombre_contacto = limpiar_texto(request, 'contacto_proveedor')
    proveedor.telefono = limpiar_texto(request, 'telefono_proveedor')
    proveedor.correo = limpiar_texto(request, 'correo_proveedor')
    proveedor.contacto_operativo = limpiar_texto(request, 'contacto_operativo_proveedor')
    proveedor.telefono_operativo = limpiar_texto(request, 'telefono_operativo_proveedor')
    proveedor.correo_operativo = limpiar_texto(request, 'correo_operativo_proveedor')
    proveedor.visible_para_wedding_planners = bool_post(request, 'visible_wedding_planners_proveedor')
    proveedor.rfc = limpiar_texto(request, 'rfc_proveedor')
    proveedor.datos_bancarios = limpiar_texto(request, 'datos_bancarios_proveedor')
    proveedor.notas_privadas = limpiar_texto(request, 'notas_privadas_proveedor')
    proveedor.descripcion = limpiar_texto(request, 'descripcion_proveedor')
    proveedor.activo = bool_post(request, 'activo_proveedor')
    proveedor.save()
    return proveedor


def actualizar_paquete_empresa_dashboard(request, empresa):
    paquete = get_object_or_404(PaqueteBoda, empresa=empresa, id=request.POST.get('paquete_id'))
    paquete.nombre = limpiar_texto(request, 'nombre_paquete') or paquete.nombre
    paquete.descripcion = limpiar_texto(request, 'descripcion_paquete')
    paquete.numero_personas_incluidas = convertir_entero(request.POST.get('personas_paquete'), paquete.numero_personas_incluidas)
    paquete.precio_base = convertir_decimal(request.POST.get('precio_base_paquete'), paquete.precio_base)
    paquete.activo = bool_post(request, 'activo_paquete')
    paquete.save()
    return paquete


def eliminar_evento_empresa_dashboard(request, empresa):
    evento = get_object_or_404(EventoBoda, empresa=empresa, id=request.POST.get('evento_id'))
    nombre = str(evento)
    evento.delete()
    registrar_auditoria(
        usuario=request.user,
        empresa=empresa,
        accion='ELIMINAR_EVENTO_EMPRESA',
        modelo='EventoBoda',
        objeto_id=request.POST.get('evento_id'),
        descripcion=f'Se elimino definitivamente el evento {nombre}.',
        request=request,
    )
    messages.success(request, f'Evento eliminado: {nombre}.')


def eliminar_sede_empresa_dashboard(request, empresa):
    sede = get_object_or_404(SedeEvento, empresa=empresa, id=request.POST.get('sede_id'))
    nombre = sede.nombre
    sede.delete()
    registrar_auditoria(
        usuario=request.user,
        empresa=empresa,
        accion='ELIMINAR_SEDE_EMPRESA',
        modelo='SedeEvento',
        objeto_id=request.POST.get('sede_id'),
        descripcion=f'Se elimino definitivamente la sede {nombre}.',
        request=request,
    )
    messages.success(request, f'Sede eliminada: {nombre}.')


def eliminar_proveedor_empresa_dashboard(request, empresa):
    proveedor = get_object_or_404(Proveedor, empresa=empresa, id=request.POST.get('proveedor_id'))
    nombre = proveedor.nombre_comercial
    proveedor.delete()
    registrar_auditoria(
        usuario=request.user,
        empresa=empresa,
        accion='ELIMINAR_PROVEEDOR_EMPRESA',
        modelo='Proveedor',
        objeto_id=request.POST.get('proveedor_id'),
        descripcion=f'Se elimino definitivamente el proveedor {nombre}.',
        request=request,
    )
    messages.success(request, f'Proveedor eliminado: {nombre}.')


def eliminar_paquete_empresa_dashboard(request, empresa):
    paquete = get_object_or_404(PaqueteBoda, empresa=empresa, id=request.POST.get('paquete_id'))
    nombre = paquete.nombre
    try:
        paquete.eventos.all().delete()
        paquete.delete()
    except ProtectedError:
        messages.error(request, f'No se pudo eliminar el paquete {nombre} porque tiene relaciones protegidas.')
        return
    registrar_auditoria(
        usuario=request.user,
        empresa=empresa,
        accion='ELIMINAR_PAQUETE_EMPRESA',
        modelo='PaqueteBoda',
        objeto_id=request.POST.get('paquete_id'),
        descripcion=f'Se elimino definitivamente el paquete {nombre}.',
        request=request,
    )
    messages.success(request, f'Paquete eliminado: {nombre}.')


def empresa_actual_dashboard(request):
    empresas = empresas_para_usuario(request.user)
    empresa_id = request.GET.get('empresa')
    if empresa_id and (not request.user.is_authenticated or usuario_es_dirtec(request.user)):
        empresa = get_object_or_404(EmpresaSuscriptora, id=empresa_id)
    elif empresa_id:
        empresa = get_object_or_404(empresas, id=empresa_id)
    else:
        empresa = empresas.first()
    return empresa, empresas


def empresa_autorizada_para_evento(request, evento, empresa_id):
    if not empresa_id:
        return evento.empresa
    if usuario_es_dirtec(request.user):
        return get_object_or_404(EmpresaSuscriptora, id=empresa_id)

    if evento.empresa_id and str(evento.empresa_id) != str(empresa_id):
        registrar_auditoria(
            usuario=request.user,
            empresa=evento.empresa,
            evento=evento,
            accion='INTENTO_CAMBIO_EMPRESA_EVENTO',
            modelo='EventoBoda',
            objeto_id=evento.id,
            descripcion=f'Intento de reasignar evento a empresa {empresa_id} sin permiso DIRTEC.',
            request=request,
        )
        raise PermissionDenied('No puedes cambiar la empresa de este evento.')
    empresa = get_object_or_404(empresas_para_usuario(request.user), id=empresa_id)
    return empresa


def membresia_empresa_usuario(user, empresa):
    if not user.is_authenticated or not empresa:
        return None
    return MembresiaEmpresa.objects.filter(usuario=user, empresa=empresa, activo=True).order_by('rol').first()


def eventos_dashboard_queryset(request):
    empresa, _ = empresa_actual_dashboard(request)
    eventos = eventos_visibles_usuario(request.user)
    if empresa:
        eventos = eventos.filter(empresa=empresa)
    return eventos


def obtener_evento_dashboard(request):
    evento_id = request.GET.get('evento')
    eventos = eventos_dashboard_queryset(request)

    if evento_id:
        evento = get_object_or_404(eventos, id=evento_id)
    else:
        evento = eventos.filter(activo=True).first() or eventos.first()

    return evento, eventos

def eventos_para_cliente(user):
    return eventos_visibles_usuario(user)


def obtener_evento_portal(request, eventos):
    evento_id = request.GET.get('evento')
    if evento_id:
        return get_object_or_404(eventos, id=evento_id)
    return eventos.filter(activo=True).first() or eventos.first()


def usuario_puede_ver_evento_cliente(user, evento):
    if not user.is_authenticated or not evento:
        return False
    return eventos_visibles_usuario(user).filter(id=evento.id).exists()


def proveedor_de_usuario(user):
    if not user.is_authenticated:
        return None
    return Proveedor.objects.filter(usuario=user, activo=True).first()


def usuarios_notificacion_evento(evento, incluir_clientes=False, usuarios_extra=None):
    usuarios = []
    usuarios_extra = usuarios_extra or []

    if evento and evento.wedding_planner:
        usuarios.append(evento.wedding_planner)

    if incluir_clientes and evento:
        usuarios.extend(list(evento.clientes.all()))

    usuarios.extend([usuario for usuario in usuarios_extra if usuario])

    unicos = {}
    for usuario in usuarios:
        if usuario and usuario.pk:
            unicos[usuario.pk] = usuario
    return unicos.values()


def crear_notificaciones_evento(evento, titulo, mensaje, tipo='INFO', enlace=None, incluir_clientes=False, usuarios_extra=None):
    for usuario in usuarios_notificacion_evento(evento, incluir_clientes=incluir_clientes, usuarios_extra=usuarios_extra):
        Notificacion.objects.create(
            usuario=usuario,
            evento=evento,
            titulo=titulo,
            mensaje=mensaje,
            tipo=tipo,
            enlace=enlace,
        )


@login_required(login_url=LOGIN_DASHBOARD_URL)
def dashboard_profesional(request):
    if usuario_es_dirtec(request.user):
        return redirect('/dirtec/dashboard/')

    empresas = empresas_para_usuario(request.user)
    for empresa in empresas:
        roles = roles_activos_empresa(request.user, empresa)
        if roles.intersection({'ADMIN_EMPRESA', 'VENTAS'}):
            return redirect(f'/empresa/{empresa.slug}/dashboard/')
        if 'WEDDING_PLANNER' in roles:
            return redirect(f'/empresa/{empresa.slug}/wedding-planner/dashboard/')

    return redirect('dashboard')


@login_required(login_url=LOGIN_DASHBOARD_URL)
def dashboard_dirtec(request):
    if not usuario_es_dirtec(request.user):
        return redirect('dashboard_profesional')

    if request.method == 'POST':
        accion = request.POST.get('accion')
        if accion == 'crear_plan_suscripcion':
            crear_plan_suscripcion_dirtec(request)
            return redirect('/dirtec/dashboard/#planes')
        if accion == 'editar_plan_suscripcion':
            actualizar_plan_suscripcion_dirtec(request)
            return redirect('/dirtec/dashboard/#planes')
        if accion == 'eliminar_plan_suscripcion':
            eliminar_plan_suscripcion_dirtec(request)
            return redirect('/dirtec/dashboard/#planes')
        if accion == 'crear_empresa':
            empresa = crear_empresa_saas_dirtec(request)
            return redirect(f'/dirtec/dashboard/?empresa={empresa.id}#empresas' if empresa else '/dirtec/dashboard/#empresas')
        if accion == 'editar_empresa':
            empresa = actualizar_empresa_dirtec(request)
            return redirect(f'/dirtec/dashboard/?empresa={empresa.id}#empresas')
        if accion == 'desactivar_empresa':
            empresa = desactivar_empresa_dirtec(request)
            return redirect(f'/dirtec/dashboard/?empresa={empresa.id}#empresas')
        if accion == 'eliminar_empresa':
            eliminar_empresa_dirtec(request)
            return redirect('/dirtec/dashboard/#empresas')
        if accion == 'crear_admin_empresa':
            empresa = get_object_or_404(EmpresaSuscriptora, id=request.POST.get('empresa_id'))
            crear_o_actualizar_usuario_empresa(request, empresa, 'ADMIN_EMPRESA')
            return redirect(f'/dirtec/dashboard/?empresa={empresa.id}#usuarios')
        if accion == 'editar_usuario_empresa':
            empresa = get_object_or_404(EmpresaSuscriptora, id=request.POST.get('empresa_id'))
            actualizar_usuario_empresa_dashboard(request, empresa)
            return redirect(f'/dirtec/dashboard/?empresa={empresa.id}#usuarios')
        if accion == 'desactivar_usuario_empresa':
            empresa = get_object_or_404(EmpresaSuscriptora, id=request.POST.get('empresa_id'))
            desactivar_usuario_empresa_dashboard(request, empresa)
            return redirect(f'/dirtec/dashboard/?empresa={empresa.id}#usuarios')
        if accion == 'eliminar_usuario_empresa':
            empresa = get_object_or_404(EmpresaSuscriptora, id=request.POST.get('empresa_id'))
            eliminar_usuario_empresa_dashboard(request, empresa)
            return redirect(f'/dirtec/dashboard/?empresa={empresa.id}#usuarios')
        if accion == 'actualizar_suscripcion':
            suscripcion = actualizar_suscripcion_dirtec(request)
            return redirect(f'/dirtec/dashboard/?empresa={suscripcion.empresa_id}#suscripciones')
        if accion == 'registrar_pago_suscripcion':
            pago = registrar_pago_suscripcion_dirtec(request)
            return redirect(f'/dirtec/dashboard/?empresa={pago.empresa_id}#pagos')

    empresas = EmpresaSuscriptora.objects.all().order_by('nombre_comercial')
    empresa_actual = None
    empresa_id = request.GET.get('empresa')
    if empresa_id:
        empresa_actual = get_object_or_404(empresas, id=empresa_id)
    else:
        empresa_actual = empresas.first()

    eventos = EventoBoda.objects.all()
    membresias = MembresiaEmpresa.objects.select_related('empresa', 'usuario')
    planes_suscripcion = PlanSuscripcion.objects.all().order_by('-activo', 'nombre')
    suscripciones = SuscripcionEmpresa.objects.select_related('empresa', 'plan').order_by('fecha_vencimiento')
    pagos_suscripcion = PagoSuscripcion.objects.select_related('empresa', 'suscripcion', 'registrado_por').order_by('-fecha_registro')
    hoy = timezone.localdate()
    empresas_detalle = []
    for empresa in empresas:
        eventos_empresa = eventos.filter(empresa=empresa)
        suscripcion = getattr(empresa, 'suscripcion', None)
        empresas_detalle.append({
            'empresa': empresa,
            'suscripcion': suscripcion,
            'eventos': eventos_empresa.count(),
            'usuarios': membresias.filter(empresa=empresa, activo=True).values('usuario_id').distinct().count(),
            'planners': membresias.filter(empresa=empresa, rol='WEDDING_PLANNER', activo=True).count(),
            'pendientes': resumen_operativo_eventos(eventos_empresa)['tareas_pendientes'],
        })

    context = {
        'titulo_dashboard': 'DIRTEC Control',
        'empresas': empresas,
        'empresa_actual': empresa_actual,
        'empresas_detalle': empresas_detalle,
        'planes': EmpresaSuscriptora.PLANES,
        'estados_empresa': EmpresaSuscriptora.ESTADOS,
        'planes_suscripcion': planes_suscripcion,
        'suscripciones': suscripciones,
        'suscripcion_actual': getattr(empresa_actual, 'suscripcion', None) if empresa_actual else None,
        'pagos_suscripcion': pagos_suscripcion.filter(empresa=empresa_actual)[:12] if empresa_actual else [],
        'estados_suscripcion': SuscripcionEmpresa.ESTADOS,
        'estados_pago_suscripcion': PagoSuscripcion.ESTADOS,
        'estados_evento': EventoBoda.ESTADOS_EVENTO,
        'roles_empresa': MembresiaEmpresa.ROLES,
        'usuarios_empresa': membresias.filter(empresa=empresa_actual).order_by('-activo', 'rol') if empresa_actual else [],
        'eventos_recientes': eventos.select_related('empresa', 'sede', 'wedding_planner').order_by('-fecha_creacion')[:10],
        'resumen': {
            'empresas': empresas.count(),
            'empresas_activas': empresas.filter(activo=True).count(),
            'empresas_suspendidas': empresas.filter(estado='SUSPENDIDA').count(),
            'empresas_bloqueadas': empresas.filter(estado='BLOQUEADA').count(),
            'eventos': eventos.count(),
            'usuarios': membresias.values('usuario_id').distinct().count(),
            'suscripciones_vigentes': suscripciones.filter(estado__in=['PRUEBA', 'ACTIVA', 'PROXIMA_A_VENCER'], fecha_vencimiento__gte=hoy).count(),
            'suscripciones_por_vencer': suscripciones.filter(fecha_vencimiento__gte=hoy, fecha_vencimiento__lte=hoy + timedelta(days=7)).count(),
            'suscripciones_vencidas': suscripciones.filter(fecha_vencimiento__lt=hoy).count(),
            'pagos_pendientes': pagos_suscripcion.filter(estado='PENDIENTE').count(),
        },
    }
    return render(request, 'invitaciones/dashboard_dirtec.html', context)


@login_required(login_url=LOGIN_DASHBOARD_URL)
def dashboard_empresa(request):
    empresa, empresas = empresa_dashboard_autorizada(request, ['ADMIN_EMPRESA', 'VENTAS'])
    if not empresa:
        return redirect('dashboard_profesional')

    puede_catalogos = usuario_puede_gestionar_catalogos(request.user, empresa)
    puede_usuarios = usuario_puede_gestionar_usuarios(request.user, empresa)
    roles_usuario_actual = roles_activos_empresa(request.user, empresa)

    if request.method == 'POST':
        accion = request.POST.get('accion')
        if accion in ACCIONES_PANEL_EMPRESA_USUARIOS and not puede_usuarios:
            bloquear_accion_dashboard(request, empresa=empresa, accion=accion, permiso='gestionar usuarios')
        if accion in ACCIONES_PANEL_EMPRESA_CATALOGOS and not puede_catalogos:
            bloquear_accion_dashboard(request, empresa=empresa, accion=accion, permiso='gestionar catalogos')
        if accion == 'crear_evento':
            try:
                validar_limite_eventos_activos(empresa)
            except LimitePlanExcedido as exc:
                return bloquear_por_limite_plan(request, empresa, str(exc), '#eventos')
            evento = crear_evento_para_empresa(request, empresa)
            return redirect(f'/dashboard/empresa/?empresa={empresa.id}#eventos')
        if accion == 'editar_evento':
            actualizar_evento_empresa_dashboard(request, empresa)
            return redirect(f'/dashboard/empresa/?empresa={empresa.id}#eventos')
        if accion == 'desactivar_evento':
            evento = get_object_or_404(EventoBoda, empresa=empresa, id=request.POST.get('evento_id'))
            evento.activo = False
            evento.save(update_fields=['activo'])
            return redirect(f'/dashboard/empresa/?empresa={empresa.id}#eventos')
        if accion == 'eliminar_evento':
            eliminar_evento_empresa_dashboard(request, empresa)
            return redirect(f'/dashboard/empresa/?empresa={empresa.id}#eventos')
        if accion == 'crear_planner' and puede_usuarios:
            username = limpiar_texto(request, 'username_usuario')
            if not usuario_empresa_existente_activo(empresa, username):
                try:
                    validar_limite_usuarios(empresa)
                except LimitePlanExcedido as exc:
                    return bloquear_por_limite_plan(request, empresa, str(exc), '#equipo')
            if not usuario_empresa_existente_activo(empresa, username, 'WEDDING_PLANNER'):
                try:
                    validar_limite_planners(empresa)
                except LimitePlanExcedido as exc:
                    return bloquear_por_limite_plan(request, empresa, str(exc), '#equipo')
            crear_o_actualizar_usuario_empresa(request, empresa, 'WEDDING_PLANNER')
            return redirect(f'/dashboard/empresa/?empresa={empresa.id}#equipo')
        if accion == 'editar_usuario_empresa' and puede_usuarios:
            membresia = actualizar_usuario_empresa_dashboard(request, empresa)
            origen = request.POST.get('origen') or ('clientes' if membresia.rol == 'CLIENTE' else 'equipo')
            return redirect(f'/dashboard/empresa/?empresa={empresa.id}#{origen}')
        if accion == 'desactivar_usuario_empresa' and puede_usuarios:
            membresia = desactivar_usuario_empresa_dashboard(request, empresa)
            origen = request.POST.get('origen') or ('clientes' if membresia.rol == 'CLIENTE' else 'equipo')
            return redirect(f'/dashboard/empresa/?empresa={empresa.id}#{origen}')
        if accion == 'eliminar_usuario_empresa' and puede_usuarios:
            rol = eliminar_usuario_empresa_dashboard(request, empresa)
            origen = request.POST.get('origen') or ('clientes' if rol == 'CLIENTE' else 'equipo')
            return redirect(f'/dashboard/empresa/?empresa={empresa.id}#{origen}')
        if accion == 'crear_cliente' and puede_usuarios:
            username = limpiar_texto(request, 'username_usuario')
            if not usuario_empresa_existente_activo(empresa, username):
                try:
                    validar_limite_usuarios(empresa)
                except LimitePlanExcedido as exc:
                    return bloquear_por_limite_plan(request, empresa, str(exc), '#clientes')
            if not usuario_empresa_existente_activo(empresa, username, 'CLIENTE'):
                try:
                    validar_limite_clientes(empresa)
                except LimitePlanExcedido as exc:
                    return bloquear_por_limite_plan(request, empresa, str(exc), '#clientes')
            crear_cliente_empresa_dashboard(request, empresa)
            return redirect(f'/dashboard/empresa/?empresa={empresa.id}#clientes')
        if accion == 'crear_sede' and puede_catalogos:
            nombre = limpiar_texto(request, 'nombre_sede')
            if nombre:
                SedeEvento.objects.create(
                    empresa=empresa,
                    nombre=nombre,
                    tipo=request.POST.get('tipo_sede') or 'SALON',
                    capacidad_minima=convertir_entero(request.POST.get('capacidad_minima'), 0),
                    capacidad_maxima=convertir_entero(request.POST.get('capacidad_maxima'), 0),
                    precio_base=convertir_decimal(request.POST.get('precio_base_sede'), 0),
                    direccion=limpiar_texto(request, 'direccion_sede'),
                    activa=True,
                )
            return redirect(f'/dashboard/empresa/?empresa={empresa.id}#catalogos')
        if accion == 'editar_sede' and puede_catalogos:
            actualizar_sede_empresa_dashboard(request, empresa)
            return redirect(f'/dashboard/empresa/?empresa={empresa.id}#catalogos')
        if accion == 'desactivar_sede' and puede_catalogos:
            sede = get_object_or_404(SedeEvento, empresa=empresa, id=request.POST.get('sede_id'))
            sede.activa = False
            sede.save(update_fields=['activa'])
            return redirect(f'/dashboard/empresa/?empresa={empresa.id}#catalogos')
        if accion == 'eliminar_sede' and puede_catalogos:
            eliminar_sede_empresa_dashboard(request, empresa)
            return redirect(f'/dashboard/empresa/?empresa={empresa.id}#catalogos')
        if accion == 'crear_proveedor' and puede_catalogos:
            nombre = limpiar_texto(request, 'nombre_proveedor')
            if nombre:
                Proveedor.objects.create(
                    empresa=empresa,
                    nombre_comercial=nombre,
                    tipo_proveedor=request.POST.get('tipo_proveedor') or 'OTROS',
                    nombre_contacto=limpiar_texto(request, 'contacto_proveedor'),
                    telefono=limpiar_texto(request, 'telefono_proveedor'),
                    correo=limpiar_texto(request, 'correo_proveedor'),
                    contacto_operativo=limpiar_texto(request, 'contacto_operativo_proveedor'),
                    telefono_operativo=limpiar_texto(request, 'telefono_operativo_proveedor'),
                    correo_operativo=limpiar_texto(request, 'correo_operativo_proveedor'),
                    visible_para_wedding_planners=request.POST.get('visible_wedding_planners_proveedor', 'on') == 'on',
                    rfc=limpiar_texto(request, 'rfc_proveedor'),
                    datos_bancarios=limpiar_texto(request, 'datos_bancarios_proveedor'),
                    notas_privadas=limpiar_texto(request, 'notas_privadas_proveedor'),
                    activo=True,
                )
            return redirect(f'/dashboard/empresa/?empresa={empresa.id}#catalogos')
        if accion == 'editar_proveedor' and puede_catalogos:
            actualizar_proveedor_empresa_dashboard(request, empresa)
            return redirect(f'/dashboard/empresa/?empresa={empresa.id}#catalogos')
        if accion == 'desactivar_proveedor' and puede_catalogos:
            proveedor = get_object_or_404(Proveedor, empresa=empresa, id=request.POST.get('proveedor_id'))
            proveedor.activo = False
            proveedor.save(update_fields=['activo'])
            return redirect(f'/dashboard/empresa/?empresa={empresa.id}#catalogos')
        if accion == 'eliminar_proveedor' and puede_catalogos:
            eliminar_proveedor_empresa_dashboard(request, empresa)
            return redirect(f'/dashboard/empresa/?empresa={empresa.id}#catalogos')
        if accion == 'crear_paquete' and puede_catalogos:
            nombre = limpiar_texto(request, 'nombre_paquete')
            if nombre:
                PaqueteBoda.objects.create(
                    empresa=empresa,
                    nombre=nombre,
                    descripcion=limpiar_texto(request, 'descripcion_paquete'),
                    precio_base=convertir_decimal(request.POST.get('precio_base_paquete'), 0),
                    numero_personas_incluidas=convertir_entero(request.POST.get('personas_paquete'), 0),
                    activo=True,
                )
            return redirect(f'/dashboard/empresa/?empresa={empresa.id}#catalogos')
        if accion == 'editar_paquete' and puede_catalogos:
            actualizar_paquete_empresa_dashboard(request, empresa)
            return redirect(f'/dashboard/empresa/?empresa={empresa.id}#catalogos')
        if accion == 'desactivar_paquete' and puede_catalogos:
            paquete = get_object_or_404(PaqueteBoda, empresa=empresa, id=request.POST.get('paquete_id'))
            paquete.activo = False
            paquete.save(update_fields=['activo'])
            return redirect(f'/dashboard/empresa/?empresa={empresa.id}#catalogos')
        if accion == 'eliminar_paquete' and puede_catalogos:
            eliminar_paquete_empresa_dashboard(request, empresa)
            return redirect(f'/dashboard/empresa/?empresa={empresa.id}#catalogos')

    eventos = EventoBoda.objects.filter(empresa=empresa).select_related('sede', 'wedding_planner').order_by('-activo', '-fecha_fiesta')
    membresias = MembresiaEmpresa.objects.filter(empresa=empresa).select_related('usuario').order_by('-activo', 'rol', 'usuario__username')
    planners = membresias.filter(rol='WEDDING_PLANNER', activo=True)
    clientes_empresa = membresias.filter(rol='CLIENTE')
    context = {
        'empresa': empresa,
        'empresas': empresas,
        'eventos': eventos,
        'resumen_eventos': resumen_eventos(eventos),
        'resumen_operativo': resumen_operativo_eventos(eventos),
        'uso_plan': resumen_uso_plan(empresa),
        'suscripcion_empresa': getattr(empresa, 'suscripcion', None),
        'membresias': membresias,
        'planners': planners,
        'clientes_empresa': clientes_empresa,
        'eventos_activos_empresa': eventos.filter(activo=True),
        'sedes': empresa.sedes.all(),
        'proveedores': empresa.proveedores.all(),
        'paquetes': empresa.paquetes.all(),
        'puede_catalogos': puede_catalogos,
        'puede_usuarios': puede_usuarios,
        'roles_usuario_actual': roles_usuario_actual,
        'es_planner_empresa': 'WEDDING_PLANNER' in roles_usuario_actual,
        'tipos_evento': EventoBoda.TIPOS_EVENTO,
        'estados_evento': EventoBoda.ESTADOS_EVENTO,
        'roles_empresa': MembresiaEmpresa.ROLES,
        'tipos_sede': SedeEvento.TIPOS,
        'tipos_proveedor': Proveedor.TIPOS,
    }
    return render(request, 'invitaciones/dashboard_empresa.html', context)


@login_required(login_url=LOGIN_DASHBOARD_URL)
def dashboard_empresa_slug(request, empresa_slug):
    empresa = get_object_or_404(empresas_para_usuario(request.user), slug=empresa_slug)
    request.GET = request.GET.copy()
    request.GET['empresa'] = str(empresa.id)
    return dashboard_empresa(request)


def asignar_proveedor_planner_dashboard(request, eventos):
    evento = get_object_or_404(eventos, id=request.POST.get('evento_id'))
    proveedor = get_object_or_404(
        Proveedor,
        id=request.POST.get('proveedor_id'),
        empresa=evento.empresa,
        activo=True,
        visible_para_wedding_planners=True,
    )
    servicio = ServicioEvento.objects.create(
        evento=evento,
        proveedor=proveedor,
        nombre_servicio=limpiar_texto(request, 'nombre_servicio') or proveedor.nombre_comercial,
        descripcion=limpiar_texto(request, 'descripcion_servicio'),
        fecha_servicio=fecha_dashboard(request, 'fecha_servicio', None) if request.POST.get('fecha_servicio') else None,
        hora_inicio=hora_dashboard(request, 'hora_inicio_servicio'),
        hora_fin=hora_dashboard(request, 'hora_fin_servicio'),
        lugar=limpiar_texto(request, 'lugar_servicio'),
        estado='SOLICITADO',
        notas=limpiar_texto(request, 'notas_servicio'),
    )
    registrar_auditoria(
        usuario=request.user,
        empresa=evento.empresa,
        evento=evento,
        accion='ASIGNAR_PROVEEDOR_PLANNER',
        modelo='ServicioEvento',
        objeto_id=servicio.id,
        descripcion=f'Wedding planner asigno {proveedor.nombre_comercial} al evento {evento}.',
        request=request,
    )
    return servicio


def actualizar_servicio_planner_dashboard(request, eventos):
    servicio = get_object_or_404(
        ServicioEvento.objects.select_related('evento', 'proveedor').filter(evento__in=eventos),
        id=request.POST.get('servicio_id'),
    )
    estados_validos = {valor for valor, _ in ServicioEvento.ESTADOS}
    estado = request.POST.get('estado_servicio')

    servicio.nombre_servicio = limpiar_texto(request, 'nombre_servicio') or servicio.nombre_servicio
    servicio.descripcion = limpiar_texto(request, 'descripcion_servicio')
    servicio.fecha_servicio = fecha_dashboard(request, 'fecha_servicio', None) if request.POST.get('fecha_servicio') else None
    servicio.hora_inicio = hora_dashboard(request, 'hora_inicio_servicio')
    servicio.hora_fin = hora_dashboard(request, 'hora_fin_servicio')
    servicio.lugar = limpiar_texto(request, 'lugar_servicio')
    servicio.costo_total = convertir_decimal(request.POST.get('costo_total_servicio'), servicio.costo_total)
    servicio.anticipo = convertir_decimal(request.POST.get('anticipo_servicio'), servicio.anticipo)
    servicio.fecha_limite_pago = fecha_dashboard(request, 'fecha_limite_pago_servicio', None) if request.POST.get('fecha_limite_pago_servicio') else None
    if estado in estados_validos:
        servicio.estado = estado
    servicio.notas = limpiar_texto(request, 'notas_servicio')

    for campo in ('cotizacion', 'contrato', 'comprobante_pago'):
        archivo = request.FILES.get(campo)
        if archivo:
            setattr(servicio, campo, archivo)

    servicio.save()
    registrar_auditoria(
        usuario=request.user,
        empresa=servicio.evento.empresa,
        evento=servicio.evento,
        accion='ACTUALIZAR_SERVICIO_PLANNER',
        modelo='ServicioEvento',
        objeto_id=servicio.id,
        descripcion=f'Wedding planner actualizo servicio {servicio.nombre_servicio}.',
        request=request,
    )
    return servicio


@login_required(login_url=LOGIN_DASHBOARD_URL)
def dashboard_planner(request):
    eventos = eventos_visibles_usuario(request.user).filter(wedding_planner=request.user).select_related('empresa', 'sede').order_by('-activo', 'fecha_fiesta')
    empresas = empresas_para_usuario(request.user)
    empresas_creacion = empresas.filter(
        membresias__usuario=request.user,
        membresias__rol='WEDDING_PLANNER',
        membresias__activo=True,
    ).distinct()
    empresa_id = request.GET.get('empresa')
    empresa_actual = None
    if empresa_id:
        empresa_actual = get_object_or_404(empresas, id=empresa_id)
        eventos = eventos.filter(empresa=empresa_actual)

    if request.method == 'POST' and request.POST.get('accion') == 'crear_evento_planner':
        empresa_post_id = request.POST.get('empresa_id') or empresa_id
        empresa_evento = get_object_or_404(empresas, id=empresa_post_id) if empresa_post_id else empresas.first()
        if not empresa_evento or 'WEDDING_PLANNER' not in roles_activos_empresa(request.user, empresa_evento):
            bloquear_accion_dashboard(
                request,
                empresa=empresa_evento,
                accion='crear_evento_planner',
                permiso='wedding planner activo de la empresa',
            )
        try:
            validar_limite_eventos_activos(empresa_evento)
        except LimitePlanExcedido as exc:
            messages.error(request, str(exc))
            registrar_auditoria(
                usuario=request.user,
                empresa=empresa_evento,
                accion='LIMITE_PLAN_EXCEDIDO',
                modelo='EmpresaSuscriptora',
                objeto_id=empresa_evento.id,
                descripcion=str(exc),
                request=request,
            )
            return redirect(f'/empresa/{empresa_evento.slug}/wedding-planner/dashboard/#eventos')
        crear_evento_planner_dashboard(request, empresa_evento)
        return redirect(f'/empresa/{empresa_evento.slug}/wedding-planner/dashboard/#eventos')

    if request.method == 'POST' and request.POST.get('accion') == 'actualizar_estado_evento':
        evento = get_object_or_404(eventos, id=request.POST.get('evento_id'))
        estado = request.POST.get('estado')
        estados_validos = {valor for valor, _ in EventoBoda.ESTADOS_EVENTO}
        if estado in estados_validos:
            evento.estado = estado
            evento.save(update_fields=['estado'])
        return redirect(f'/empresa/{evento.empresa.slug}/wedding-planner/dashboard/#eventos' if evento.empresa else '/dashboard/planner/#eventos')

    if request.method == 'POST' and request.POST.get('accion') == 'asignar_proveedor_evento':
        servicio = asignar_proveedor_planner_dashboard(request, eventos)
        messages.success(request, f'Proveedor asignado a {servicio.evento}.')
        return redirect(f'/empresa/{servicio.evento.empresa.slug}/wedding-planner/dashboard/#proveedores' if servicio.evento.empresa else '/dashboard/planner/#proveedores')

    if request.method == 'POST' and request.POST.get('accion') == 'actualizar_servicio_evento':
        servicio = actualizar_servicio_planner_dashboard(request, eventos)
        messages.success(request, f'Servicio actualizado: {servicio.nombre_servicio}.')
        return redirect(f'/empresa/{servicio.evento.empresa.slug}/wedding-planner/dashboard/#proveedores' if servicio.evento.empresa else '/dashboard/planner/#proveedores')

    eventos_lista = list(eventos)
    empresa_actual = empresa_actual or empresas.first()
    empresas_ids = list(empresas.values_list('id', flat=True))
    proveedores_autorizados = Proveedor.objects.filter(
        empresa_id__in=empresas_ids,
        activo=True,
        visible_para_wedding_planners=True,
    ).order_by('tipo_proveedor', 'nombre_comercial')
    if empresa_actual:
        proveedores_autorizados = proveedores_autorizados.filter(empresa=empresa_actual)
    servicios_eventos_planner_qs = ServicioEvento.objects.filter(
        evento__in=eventos_lista,
    ).select_related('evento', 'proveedor').order_by('-fecha_creacion')
    servicios_eventos_planner = list(servicios_eventos_planner_qs)
    context = {
        'eventos': eventos,
        'empresas': empresas,
        'empresas_creacion': empresas_creacion,
        'puede_crear_eventos_planner': empresas_creacion.exists(),
        'empresa_actual': empresa_actual,
        'resumen_eventos': resumen_eventos(eventos),
        'resumen_operativo': resumen_operativo_eventos(eventos),
        'eventos_lista': eventos_lista,
        'proveedores_autorizados': proveedores_autorizados,
        'servicios_eventos_planner': servicios_eventos_planner,
        'total_costos_proveedores': sum(servicio.costo_total for servicio in servicios_eventos_planner),
        'saldo_proveedores': sum(servicio.saldo_pendiente for servicio in servicios_eventos_planner),
        'estados_servicio': ServicioEvento.ESTADOS,
        'tipos_evento': EventoBoda.TIPOS_EVENTO,
        'estados_evento': EventoBoda.ESTADOS_EVENTO,
        'tareas_proximas': TareaEvento.objects.filter(
            evento__in=eventos_lista,
            responsable=request.user,
        ).exclude(estado__in=['COMPLETADA', 'CANCELADA']).order_by('fecha_limite')[:8],
        'servicios_pendientes': ServicioEvento.objects.filter(
            evento__in=eventos_lista,
        ).exclude(estado__in=['CONTRATADO', 'ANTICIPO_PAGADO', 'LIQUIDADO', 'SERVICIO_COMPLETADO']).select_related('evento', 'proveedor')[:8],
    }
    return render(request, 'invitaciones/dashboard_planner.html', context)


@login_required(login_url=LOGIN_DASHBOARD_URL)
def dashboard_planner_slug(request, empresa_slug):
    empresa = get_object_or_404(empresas_para_usuario(request.user), slug=empresa_slug)
    if 'WEDDING_PLANNER' not in roles_activos_empresa(request.user, empresa):
        return redirect('dashboard_profesional')
    request.GET = request.GET.copy()
    request.GET['empresa'] = str(empresa.id)
    return dashboard_planner(request)


def inicio(request):
    return render(request, 'invitaciones/inicio.html')


@login_required(login_url=LOGIN_DASHBOARD_URL)
def portal_cliente(request):
    eventos = eventos_para_cliente(request.user)
    evento = obtener_evento_portal(request, eventos)

    gastos = GastoEvento.objects.filter(evento=evento) if evento else GastoEvento.objects.none()
    pagos = PagoEvento.objects.filter(gasto__evento=evento) if evento else PagoEvento.objects.none()
    tareas = TareaEvento.objects.filter(evento=evento).exclude(estado__in=['COMPLETADA', 'CANCELADA']) if evento else TareaEvento.objects.none()
    documentos = DocumentoEvento.objects.filter(evento=evento, visible_cliente=True) if evento else DocumentoEvento.objects.none()
    aprobaciones = AprobacionEvento.objects.filter(evento=evento) if evento else AprobacionEvento.objects.none()
    grupos = Grupoinvitacion.objects.filter(evento=evento) if evento else Grupoinvitacion.objects.none()

    total_lugares = sum(grupo.total_lugares for grupo in grupos)
    total_confirmados = sum(grupo.lugares_asistiran for grupo in grupos)
    total_pendientes = sum(grupo.lugares_pendientes for grupo in grupos)
    total_pagado = pagos.aggregate(total=Sum('monto'))['total'] or 0
    total_gasto = gastos.aggregate(total=Sum('monto_real'))['total'] or gastos.aggregate(total=Sum('monto_estimado'))['total'] or 0
    saldo = total_gasto - total_pagado

    context = {
        'evento': evento,
        'eventos': eventos,
        'total_lugares': total_lugares,
        'total_confirmados': total_confirmados,
        'total_pendientes': total_pendientes,
        'total_gasto': total_gasto,
        'total_pagado': total_pagado,
        'saldo': saldo if saldo > 0 else 0,
        'tareas': tareas.order_by('fecha_limite')[:8],
        'documentos': documentos[:8],
        'aprobaciones': aprobaciones[:8],
        'aprobaciones_pendientes': aprobaciones.filter(estado='PENDIENTE').count(),
    }
    return render(request, 'invitaciones/portal_cliente.html', context)


@login_required(login_url=LOGIN_DASHBOARD_URL)
@require_POST
def responder_aprobacion_cliente(request, aprobacion_id):
    aprobacion = get_object_or_404(
        AprobacionEvento.objects.select_related('evento'),
        id=aprobacion_id,
    )

    if not usuario_puede_ver_evento_cliente(request.user, aprobacion.evento):
        return JsonResponse({'ok': False, 'error': 'No autorizado'}, status=403)

    accion = request.POST.get('accion')
    estados = {
        'aprobar': 'APROBADO',
        'rechazar': 'RECHAZADO',
        'cambios': 'CAMBIOS',
    }
    if accion not in estados:
        return JsonResponse({'ok': False, 'error': 'Accion invalida'}, status=400)

    aprobacion.estado = estados[accion]
    aprobacion.aprobado_por = request.user
    aprobacion.comentario = request.POST.get('comentario', '').strip()
    aprobacion.save()
    crear_notificaciones_evento(
        aprobacion.evento,
        f'Aprobacion respondida: {aprobacion.titulo}',
        f'{request.user} marco la solicitud como {aprobacion.get_estado_display()}.',
        tipo='APROBACION',
        enlace=f'/admin/aprobaciones/aprobacionevento/{aprobacion.id}/change/',
        usuarios_extra=[aprobacion.solicitado_por],
    )

    return redirect(f'/portal/cliente/?evento={aprobacion.evento_id}')


@login_required(login_url=LOGIN_DASHBOARD_URL)
def portal_proveedor(request):
    proveedor = proveedor_de_usuario(request.user)
    eventos = EventoBoda.objects.filter(servicios_contratados__proveedor=proveedor).distinct().order_by('-fecha_fiesta') if proveedor else EventoBoda.objects.none()
    evento = obtener_evento_portal(request, eventos)
    servicios = ServicioEvento.objects.filter(proveedor=proveedor, evento=evento) if proveedor and evento else ServicioEvento.objects.none()
    documentos = DocumentoEvento.objects.filter(proveedor=proveedor, evento=evento) if proveedor and evento else DocumentoEvento.objects.none()
    actividades = ActividadItinerario.objects.filter(proveedor=proveedor, evento=evento) if proveedor and evento else ActividadItinerario.objects.none()

    context = {
        'proveedor': proveedor,
        'evento': evento,
        'eventos': eventos,
        'servicios': servicios,
        'documentos': documentos[:8],
        'actividades': actividades.order_by('fecha', 'hora_inicio')[:8],
        'estados_servicio': ServicioEvento.ESTADOS,
        'tipos_documento': DocumentoEvento.TIPOS,
        'total_servicios': servicios.count(),
        'servicios_pendientes': servicios.exclude(estado__in=['LIQUIDADO', 'SERVICIO_COMPLETADO', 'CANCELADO']).count(),
        'saldo_pendiente': sum(servicio.saldo_pendiente for servicio in servicios),
    }
    return render(request, 'invitaciones/portal_proveedor.html', context)


@login_required(login_url=LOGIN_DASHBOARD_URL)
@require_POST
def actualizar_servicio_proveedor(request, servicio_id):
    proveedor = proveedor_de_usuario(request.user)
    servicio = get_object_or_404(ServicioEvento, id=servicio_id, proveedor=proveedor)

    estado = request.POST.get('estado')
    estados_validos = {valor for valor, _ in ServicioEvento.ESTADOS}
    if estado not in estados_validos:
        return JsonResponse({'ok': False, 'error': 'Estado invalido'}, status=400)

    servicio.estado = estado
    nota = request.POST.get('nota', '').strip()
    if nota:
        servicio.notas = f'{servicio.notas or ""}\nProveedor: {nota}'.strip()
    servicio.save(update_fields=['estado', 'notas', 'fecha_actualizacion'])
    crear_notificaciones_evento(
        servicio.evento,
        f'Proveedor actualizo servicio: {servicio.nombre_servicio}',
        f'{proveedor.nombre_comercial} cambio el estado a {servicio.get_estado_display()}.',
        tipo='PROVEEDOR',
        enlace=f'/admin/proveedores/servicioevento/{servicio.id}/change/',
    )

    return redirect(f'/portal/proveedor/?evento={servicio.evento_id}')


@login_required(login_url=LOGIN_DASHBOARD_URL)
@require_POST
def subir_documento_proveedor(request):
    proveedor = proveedor_de_usuario(request.user)
    if not proveedor:
        return JsonResponse({'ok': False, 'error': 'No autorizado'}, status=403)
    evento = get_object_or_404(
        EventoBoda.objects.filter(servicios_contratados__proveedor=proveedor).distinct(),
        id=request.POST.get('evento_id'),
    )

    archivo = request.FILES.get('archivo')
    if not archivo:
        return JsonResponse({'ok': False, 'error': 'Falta archivo'}, status=400)
    if not archivo_pasa_validadores(DocumentoEvento, 'archivo', archivo):
        return JsonResponse({'ok': False, 'error': 'Archivo no permitido'}, status=400)

    documento = DocumentoEvento.objects.create(
        evento=evento,
        proveedor=proveedor,
        tipo_documento=request.POST.get('tipo_documento') or 'OTRO',
        titulo=request.POST.get('titulo') or archivo.name,
        archivo=archivo,
        descripcion=request.POST.get('descripcion') or None,
        cargado_por=request.user,
        visible_cliente=request.POST.get('visible_cliente') == 'on',
    )
    crear_notificaciones_evento(
        evento,
        f'Documento nuevo: {documento.titulo}',
        f'{proveedor.nombre_comercial} subio un documento al evento.',
        tipo='DOCUMENTO',
        enlace=f'/admin/documentos/documentoevento/{documento.id}/change/',
        incluir_clientes=documento.visible_cliente,
    )

    return redirect(f'/portal/proveedor/?evento={evento.id}')


SECCIONES_INVITACION_DEFAULTS = {
    'PORTADA': {'orden': 5, 'titulo_attr': 'frase_portada', 'descripcion_attr': 'mensaje_general', 'fondo_attr': 'foto_portada', 'activa': True},
    'PADRES_PADRINOS': {'orden': 12, 'titulo': 'Nuestros padres y padrinos', 'descripcion': '', 'activa': True},
    'CUENTA_REGRESIVA': {'orden': 20, 'titulo_attr': 'titulo_cuenta_regresiva', 'descripcion': '', 'fondo_attr': 'fondo_cuenta_regresiva', 'activa': True},
    'DETALLES': {'orden': 30, 'titulo_attr': 'titulo_detalles', 'descripcion_attr': 'texto_detalles', 'fondo_attr': 'fondo_detalles', 'activa': True},
    'DRESS_CODE': {'orden': 35, 'titulo': 'Dress Code', 'descripcion_attr': 'dress_code_descripcion', 'fondo_attr': 'fondo_detalles', 'activa': True},
    'ITINERARIO': {'orden': 40, 'titulo': 'Itinerario', 'descripcion': '', 'activa': True},
    'ALBUM': {'orden': 50, 'titulo_attr': 'titulo_album', 'descripcion': '', 'fondo_attr': 'fondo_album', 'activa': True},
    'MENU': {'orden': 60, 'titulo_attr': 'titulo_menu', 'descripcion': '', 'fondo_attr': 'fondo_menu', 'activa': True},
    'REGALOS': {'orden': 70, 'titulo_attr': 'titulo_regalos', 'descripcion': '', 'fondo_attr': 'fondo_regalos', 'activa': True},
    'ALBUM_COMPARTIDO': {
        'orden': 75,
        'titulo_attr': 'titulo_album_compartido',
        'descripcion_attr': 'texto_album_compartido',
        'activa': True,
    },
    'RSVP': {'orden': 80, 'titulo_attr': 'titulo_rsvp', 'descripcion_attr': 'texto_rsvp', 'fondo_attr': 'fondo_rsvp', 'activa': True},
}


def datos_default_seccion(evento, tipo):
    defaults = SECCIONES_INVITACION_DEFAULTS[tipo]
    titulo = defaults.get('titulo')
    descripcion = defaults.get('descripcion', '')
    if defaults.get('titulo_attr'):
        titulo = getattr(evento, defaults['titulo_attr'], '') or titulo
    if defaults.get('descripcion_attr'):
        descripcion = getattr(evento, defaults['descripcion_attr'], '') or descripcion
    fondo = getattr(evento, defaults['fondo_attr'], None) if defaults.get('fondo_attr') else None
    return {
        'tipo': tipo,
        'titulo': titulo or dict(SeccionInvitacion.TIPOS).get(tipo, tipo.title()),
        'descripcion': descripcion or '',
        'orden': defaults.get('orden', 0),
        'activa': defaults.get('activa', True),
        'fondo': fondo,
        'fondo_es_video': es_video_archivo(fondo),
        'imagen_titulo': None,
        'imagen_titulo_es_video': False,
        'mostrar_titulo_texto': True,
        'posicion_fondo': 'center center',
        'opacidad_fondo': '0.18',
        'color_texto': '',
    }


def construir_secciones_invitacion(evento):
    if not evento:
        return {}
    existentes = {
        seccion.tipo: seccion
        for seccion in evento.secciones_invitacion.all()
    }
    secciones = {}
    for tipo in SECCIONES_INVITACION_DEFAULTS:
        datos = datos_default_seccion(evento, tipo)
        seccion = existentes.get(tipo)
        if seccion:
            datos.update({
                'titulo': seccion.titulo or datos['titulo'],
                'descripcion': seccion.descripcion if seccion.descripcion is not None else datos['descripcion'],
                'orden': seccion.orden,
                'activa': seccion.activa,
                'fondo': seccion.fondo or datos['fondo'],
                'imagen_titulo': seccion.imagen_titulo,
                'imagen_titulo_es_video': seccion.imagen_titulo_es_video,
                'mostrar_titulo_texto': seccion.mostrar_titulo_texto,
                'posicion_fondo': seccion.posicion_fondo,
                'opacidad_fondo': seccion.opacidad_fondo,
                'color_texto': seccion.color_texto or '',
                'objeto': seccion,
            })
        datos['fondo_es_video'] = es_video_archivo(datos.get('fondo'))
        secciones[tipo] = datos
    return secciones


def sincronizar_secciones_invitacion(evento):
    if not evento:
        return []
    existentes = {
        seccion.tipo: seccion
        for seccion in evento.secciones_invitacion.all()
    }
    secciones = []
    for tipo in SECCIONES_INVITACION_DEFAULTS:
        datos = datos_default_seccion(evento, tipo)
        seccion = existentes.get(tipo)
        if not seccion:
            seccion = SeccionInvitacion.objects.create(
                evento=evento,
                tipo=tipo,
                titulo=datos['titulo'],
                descripcion=datos['descripcion'],
                orden=datos['orden'],
                activa=datos['activa'],
            )
        secciones.append(seccion)
    return sorted(secciones, key=lambda item: (item.orden, item.id))


EDITOR_ANIMACIONES = {'none', 'fade', 'slide', 'soft'}
EDITOR_ESPACIADOS = {'compact', 'soft', 'wide'}
EDITOR_ALINEACIONES = {'left', 'center', 'right'}
EDITOR_TAMANOS_TITULO = {'small', 'medium', 'large'}
EDITOR_BG_FIT = {'contain', 'cover', 'repeat', 'free'}
EDITOR_LAYER_TYPES = {'background', 'title', 'text', 'decor'}
EDITOR_DECOR_STYLES = {'line', 'flourish', 'rings', 'dots'}
EDITOR_CUSTOM_LAYER_TYPES = {'text', 'image', 'video'}
EDITOR_MEDIA_FIT = {'contain', 'cover'}
HEX_COLOR_RE = re.compile(r'^#[0-9a-fA-F]{6}$')


def valor_choice_seguro(valor, choices, default):
    permitidos = {item[0] for item in choices}
    return valor if valor in permitidos else default


def color_seguro(valor):
    valor = (valor or '').strip()
    return valor if HEX_COLOR_RE.match(valor) else ''


def numero_rango(valor, default, minimo, maximo, decimales=False):
    try:
        numero = float(valor) if decimales else int(valor)
    except (TypeError, ValueError):
        numero = default
    numero = max(min(numero, maximo), minimo)
    return round(numero, 2) if decimales else numero


def ref_asset_editor(asset):
    if not asset:
        return {}
    return {
        'id': asset.id,
        'url': asset.archivo.url,
        'isVideo': asset.es_video,
        'title': asset.titulo or asset.archivo.name.rsplit('/', 1)[-1],
    }


def asset_ref_seguro(evento, asset_id):
    asset_id = convertir_entero(asset_id, 0)
    if not asset_id:
        return {}
    asset = AssetInvitacion.objects.filter(evento=evento, id=asset_id, visible=True).first()
    return ref_asset_editor(asset)


def normalizar_capas_personalizadas_editor(evento, capas):
    capas = capas if isinstance(capas, list) else []
    resultado = []
    for index, capa in enumerate(capas[:60]):
        if not isinstance(capa, dict):
            continue
        tipo = capa.get('kind') if capa.get('kind') in EDITOR_CUSTOM_LAYER_TYPES else 'text'
        asset_ref = {}
        if tipo in {'image', 'video'}:
            asset_data = capa.get('asset') if isinstance(capa.get('asset'), dict) else {}
            asset_ref = asset_ref_seguro(evento, asset_data.get('id'))
            if not asset_ref:
                continue
            tipo = 'video' if asset_ref.get('isVideo') else 'image'
        resultado.append({
            'id': (str(capa.get('id') or f'layer-{index + 1}')[:80]),
            'kind': tipo,
            'name': (capa.get('name') or ('Imagen libre' if tipo in {'image', 'video'} else 'Texto libre'))[:80],
            'text': (capa.get('text') or 'Texto editable')[:220],
            'asset': asset_ref,
            'x': numero_rango(capa.get('x'), 50, -40, 140),
            'y': numero_rango(capa.get('y'), 50, -40, 140),
            'scale': numero_rango(capa.get('scale'), 1, 0.35, 3, decimales=True),
            'opacity': numero_rango(capa.get('opacity'), 1, 0, 1, decimales=True),
            'rotation': numero_rango(capa.get('rotation'), 0, -180, 180),
            'z': numero_rango(capa.get('z'), 3, 1, 12),
            'width': numero_rango(capa.get('width'), 42 if tipo in {'image', 'video'} else 64, 8, 120),
            'align': capa.get('align') if capa.get('align') in EDITOR_ALINEACIONES else 'center',
            'visible': bool(capa.get('visible', True)),
            'locked': bool(capa.get('locked', False)),
            'fit': capa.get('fit') if capa.get('fit') in EDITOR_MEDIA_FIT else 'contain',
        })
    return resultado


def capas_personalizadas_publicas(item_config):
    capas = item_config.get('customLayers') if isinstance(item_config, dict) else []
    resultado = []
    for capa in capas if isinstance(capas, list) else []:
        if not isinstance(capa, dict) or not capa.get('visible', True):
            continue
        tipo = capa.get('kind') if capa.get('kind') in EDITOR_CUSTOM_LAYER_TYPES else 'text'
        asset = capa.get('asset') if isinstance(capa.get('asset'), dict) else {}
        if tipo in {'image', 'video'} and not asset.get('url'):
            continue
        style = (
            f'--layer-x:{numero_rango(capa.get("x"), 50, -40, 140)}%;'
            f'--layer-y:{numero_rango(capa.get("y"), 50, -40, 140)}%;'
            f'--layer-scale:{numero_rango(capa.get("scale"), 1, 0.35, 3, decimales=True)};'
            f'--layer-opacity:{numero_rango(capa.get("opacity"), 1, 0, 1, decimales=True)};'
            f'--layer-rotation:{numero_rango(capa.get("rotation"), 0, -180, 180)}deg;'
            f'--layer-z:{numero_rango(capa.get("z"), 3, 1, 12)};'
            f'--layer-width:{numero_rango(capa.get("width"), 42 if tipo in {"image", "video"} else 64, 8, 120)}%;'
            f'--layer-align:{capa.get("align") if capa.get("align") in EDITOR_ALINEACIONES else "center"};'
            f'--layer-fit:{capa.get("fit") if capa.get("fit") in EDITOR_MEDIA_FIT else "contain"};'
        )
        resultado.append({
            'id': capa.get('id') or '',
            'kind': tipo,
            'name': capa.get('name') or '',
            'text': capa.get('text') or '',
            'asset': asset,
            'fit': capa.get('fit') if capa.get('fit') in EDITOR_MEDIA_FIT else 'contain',
            'style': style,
        })
    return resultado


def serializar_seccion_editor(seccion):
    return {
        'id': f'section-{seccion.id}',
        'sectionId': seccion.id,
        'type': seccion.tipo,
        'title': seccion.titulo or seccion.get_tipo_display(),
        'description': seccion.descripcion or '',
        'visible': seccion.activa,
        'order': seccion.orden,
        'config': {
            'textAlign': 'center',
            'titleSize': 'medium',
            'backgroundOpacity': str(seccion.opacidad_fondo),
            'backgroundPosition': seccion.posicion_fondo,
            'textColor': seccion.color_texto or '',
            'showTextTitle': seccion.mostrar_titulo_texto,
            'backgroundAsset': {},
            'titleAsset': {},
            'backgroundFit': 'contain',
            'backgroundRepeat': 'no-repeat',
            'backgroundX': 50,
            'backgroundY': 50,
            'backgroundScale': 1,
            'backgroundXMobile': 50,
            'backgroundYMobile': 50,
            'backgroundScaleMobile': 1,
            'backgroundXTablet': 50,
            'backgroundYTablet': 50,
            'backgroundScaleTablet': 1,
            'backgroundXDesktop': 50,
            'backgroundYDesktop': 50,
            'backgroundScaleDesktop': 1,
            'backgroundBrightness': 1,
            'backgroundBlur': 0,
            'sectionHeight': 190,
            'activeLayer': 'background',
            'showBackgroundLayer': True,
            'showTitleAsset': True,
            'titleX': 50,
            'titleY': 50,
            'titleScale': 1,
            'titleOpacity': 1,
            'titleVisible': True,
            'titleRotation': 0,
            'titleLocked': False,
            'titleZ': 2,
            'titleWidth': 72,
            'titleAlign': 'center',
            'textX': 50,
            'textY': 50,
            'textScale': 1,
            'textOpacity': 1,
            'textVisible': True,
            'textRotation': 0,
            'textLocked': False,
            'textZ': 2,
            'textWidth': 78,
            'textAlignLayer': 'center',
            'decorX': 50,
            'decorY': 12,
            'decorScale': 1,
            'decorOpacity': 0.42,
            'decorVisible': False,
            'decorRotation': 0,
            'decorLocked': False,
            'decorZ': 1,
            'decorWidth': 36,
            'decorAlign': 'center',
            'decorStyle': 'line',
            'customLayers': [],
        },
    }


def construir_configuracion_diseno(evento):
    config = DisenoInvitacion.configuracion_inicial(evento)
    secciones = sincronizar_secciones_invitacion(evento)
    config['sections'] = [serializar_seccion_editor(seccion) for seccion in secciones]
    return config


def obtener_diseno_invitacion(evento, usuario=None):
    diseno, creado = DisenoInvitacion.objects.get_or_create(
        evento=evento,
        defaults={
            'nombre': 'Diseño principal',
            'configuracion_borrador': construir_configuracion_diseno(evento),
            'actualizado_por': usuario if usuario and usuario.is_authenticated else None,
        },
    )
    if creado or not diseno.configuracion_borrador:
        diseno.configuracion_borrador = construir_configuracion_diseno(evento)
        diseno.actualizado_por = usuario if usuario and usuario.is_authenticated else diseno.actualizado_por
        diseno.save(update_fields=['configuracion_borrador', 'actualizado_por', 'fecha_actualizacion'])
    return diseno


def sincronizar_diseno_con_secciones(evento, diseno):
    config = dict(diseno.configuracion_borrador or construir_configuracion_diseno(evento))
    existentes = {item.get('sectionId'): item for item in config.get('sections', []) if item.get('sectionId')}
    secciones = []
    for seccion in sincronizar_secciones_invitacion(evento):
        item = serializar_seccion_editor(seccion)
        previo = existentes.get(seccion.id)
        if previo:
            item.update({
                'title': previo.get('title') or item['title'],
                'description': previo.get('description', item['description']),
                'visible': bool(previo.get('visible')),
                'order': convertir_entero(previo.get('order'), item['order']),
                'config': {**item['config'], **(previo.get('config') or {})},
            })
        secciones.append(item)
    config['sections'] = sorted(secciones, key=lambda item: (item.get('order', 0), item.get('sectionId', 0)))
    diseno.configuracion_borrador = config
    diseno.save(update_fields=['configuracion_borrador', 'fecha_actualizacion'])
    return config


def normalizar_configuracion_editor(evento, payload):
    payload = payload if isinstance(payload, dict) else {}
    actual = construir_configuracion_diseno(evento)
    theme = payload.get('theme') if isinstance(payload.get('theme'), dict) else {}
    layout = payload.get('layout') if isinstance(payload.get('layout'), dict) else {}
    sections_payload = payload.get('sections') if isinstance(payload.get('sections'), list) else []
    secciones_por_id = {seccion.id: seccion for seccion in sincronizar_secciones_invitacion(evento)}

    config = {
        'theme': {
            'palette': valor_choice_seguro(theme.get('palette'), EventoBoda.PALETAS, evento.paleta_colores),
            'envelopePalette': valor_choice_seguro(theme.get('envelopePalette'), EventoBoda.PALETAS, evento.paleta_sobre),
            'fontStyle': valor_choice_seguro(theme.get('fontStyle'), EventoBoda.ESTILOS_LETRA, evento.estilo_letra),
            'primary': color_seguro(theme.get('primary')),
            'secondary': color_seguro(theme.get('secondary')),
            'accent': color_seguro(theme.get('accent')),
            'background': color_seguro(theme.get('background')),
            'coverAsset': asset_ref_seguro(evento, (theme.get('coverAsset') or {}).get('id') if isinstance(theme.get('coverAsset'), dict) else None),
            'ceremonyAsset': asset_ref_seguro(evento, (theme.get('ceremonyAsset') or {}).get('id') if isinstance(theme.get('ceremonyAsset'), dict) else None),
            'receptionAsset': asset_ref_seguro(evento, (theme.get('receptionAsset') or {}).get('id') if isinstance(theme.get('receptionAsset'), dict) else None),
            'dressAllowedAsset': asset_ref_seguro(evento, (theme.get('dressAllowedAsset') or {}).get('id') if isinstance(theme.get('dressAllowedAsset'), dict) else None),
            'dressBlockedAsset': asset_ref_seguro(evento, (theme.get('dressBlockedAsset') or {}).get('id') if isinstance(theme.get('dressBlockedAsset'), dict) else None),
            'albumAssets': [
                ref for ref in [
                    asset_ref_seguro(evento, (asset or {}).get('id')) for asset in (
                        theme.get('albumAssets') if isinstance(theme.get('albumAssets'), list) else []
                    )
                ] if ref
            ][:80],
        },
        'layout': {
            'maxWidth': min(max(convertir_entero(layout.get('maxWidth'), 430), 320), 720),
            'sectionSpacing': layout.get('sectionSpacing') if layout.get('sectionSpacing') in EDITOR_ESPACIADOS else 'soft',
            'animation': layout.get('animation') if layout.get('animation') in EDITOR_ANIMACIONES else 'fade',
        },
        'sections': [],
    }

    usados = set()
    for index, item in enumerate(sections_payload):
        if not isinstance(item, dict):
            continue
        seccion_id = convertir_entero(item.get('sectionId'), 0)
        seccion = secciones_por_id.get(seccion_id)
        if not seccion or seccion_id in usados:
            continue
        usados.add(seccion_id)
        item_config = item.get('config') if isinstance(item.get('config'), dict) else {}
        capas_personalizadas = normalizar_capas_personalizadas_editor(evento, item_config.get('customLayers'))
        active_layer = item_config.get('activeLayer')
        capas_ids = {capa['id'] for capa in capas_personalizadas}
        if active_layer not in EDITOR_LAYER_TYPES and not (
            isinstance(active_layer, str) and active_layer.startswith('custom:') and active_layer.replace('custom:', '') in capas_ids
        ):
            active_layer = 'background'
        config['sections'].append({
            'id': f'section-{seccion.id}',
            'sectionId': seccion.id,
            'type': seccion.tipo,
            'title': (item.get('title') or seccion.titulo or seccion.get_tipo_display())[:140],
            'description': (item.get('description') or '')[:1200],
            'visible': bool(item.get('visible')),
            'order': convertir_entero(item.get('order'), (index + 1) * 10),
            'config': {
                'textAlign': item_config.get('textAlign') if item_config.get('textAlign') in EDITOR_ALINEACIONES else 'center',
                'titleSize': item_config.get('titleSize') if item_config.get('titleSize') in EDITOR_TAMANOS_TITULO else 'medium',
                'backgroundOpacity': str(convertir_decimal(item_config.get('backgroundOpacity'), seccion.opacidad_fondo)),
                'backgroundPosition': item_config.get('backgroundPosition') if item_config.get('backgroundPosition') in dict(SeccionInvitacion.POSICIONES_FONDO) else seccion.posicion_fondo,
                'textColor': color_seguro(item_config.get('textColor')),
                'showTextTitle': (
                    item_config.get('showTextTitle')
                    if isinstance(item_config.get('showTextTitle'), bool)
                    else seccion.mostrar_titulo_texto
                ),
                'layoutMode': (
                    item_config.get('layoutMode')
                    if item_config.get('layoutMode') in {'normal', 'full-image'}
                    else 'normal'
                ),
                'keepRealContent': (
                    item_config.get('keepRealContent')
                    if isinstance(item_config.get('keepRealContent'), bool)
                    else True
                ),
                'backgroundAsset': asset_ref_seguro(evento, (item_config.get('backgroundAsset') or {}).get('id') if isinstance(item_config.get('backgroundAsset'), dict) else None),
                'titleAsset': asset_ref_seguro(evento, (item_config.get('titleAsset') or {}).get('id') if isinstance(item_config.get('titleAsset'), dict) else None),
                'backgroundFit': item_config.get('backgroundFit') if item_config.get('backgroundFit') in EDITOR_BG_FIT else 'contain',
                'backgroundRepeat': 'repeat' if item_config.get('backgroundRepeat') == 'repeat' else 'no-repeat',
                'backgroundX': numero_rango(item_config.get('backgroundX'), 50, 0, 100),
                'backgroundY': numero_rango(item_config.get('backgroundY'), 50, 0, 100),
                'backgroundScale': numero_rango(item_config.get('backgroundScale'), 1, 0.4, 3, decimales=True),
                'backgroundXMobile': numero_rango(item_config.get('backgroundXMobile'), numero_rango(item_config.get('backgroundX'), 50, 0, 100), 0, 100),
                'backgroundYMobile': numero_rango(item_config.get('backgroundYMobile'), numero_rango(item_config.get('backgroundY'), 50, 0, 100), 0, 100),
                'backgroundScaleMobile': numero_rango(item_config.get('backgroundScaleMobile'), numero_rango(item_config.get('backgroundScale'), 1, 0.4, 3, decimales=True), 0.4, 3, decimales=True),
                'backgroundXTablet': numero_rango(item_config.get('backgroundXTablet'), numero_rango(item_config.get('backgroundX'), 50, 0, 100), 0, 100),
                'backgroundYTablet': numero_rango(item_config.get('backgroundYTablet'), numero_rango(item_config.get('backgroundY'), 50, 0, 100), 0, 100),
                'backgroundScaleTablet': numero_rango(item_config.get('backgroundScaleTablet'), numero_rango(item_config.get('backgroundScale'), 1, 0.4, 3, decimales=True), 0.4, 3, decimales=True),
                'backgroundXDesktop': numero_rango(item_config.get('backgroundXDesktop'), numero_rango(item_config.get('backgroundX'), 50, 0, 100), 0, 100),
                'backgroundYDesktop': numero_rango(item_config.get('backgroundYDesktop'), numero_rango(item_config.get('backgroundY'), 50, 0, 100), 0, 100),
                'backgroundScaleDesktop': numero_rango(item_config.get('backgroundScaleDesktop'), numero_rango(item_config.get('backgroundScale'), 1, 0.4, 3, decimales=True), 0.4, 3, decimales=True),
                'backgroundBrightness': numero_rango(item_config.get('backgroundBrightness'), 1, 0.35, 1.75, decimales=True),
                'backgroundBlur': numero_rango(item_config.get('backgroundBlur'), 0, 0, 12, decimales=True),
                'sectionHeight': numero_rango(item_config.get('sectionHeight'), 190, 120, 900),
                'activeLayer': active_layer,
                'showBackgroundLayer': bool(item_config.get('showBackgroundLayer', True)),
                'showTitleAsset': bool(item_config.get('showTitleAsset', True)),
                'titleX': numero_rango(item_config.get('titleX'), 50, -40, 140),
                'titleY': numero_rango(item_config.get('titleY'), 50, -40, 140),
                'titleScale': numero_rango(item_config.get('titleScale'), 1, 0.5, 2.2, decimales=True),
                'titleOpacity': numero_rango(item_config.get('titleOpacity'), 1, 0, 1, decimales=True),
                'titleVisible': bool(item_config.get('titleVisible', True)),
                'titleRotation': numero_rango(item_config.get('titleRotation'), 0, -45, 45),
                'titleLocked': bool(item_config.get('titleLocked', False)),
                'titleZ': numero_rango(item_config.get('titleZ'), 2, 1, 5),
                'titleWidth': numero_rango(item_config.get('titleWidth'), 72, 12, 100),
                'titleAlign': item_config.get('titleAlign') if item_config.get('titleAlign') in EDITOR_ALINEACIONES else 'center',
                'textX': numero_rango(item_config.get('textX'), 50, -40, 140),
                'textY': numero_rango(item_config.get('textY'), 50, -40, 140),
                'textScale': numero_rango(item_config.get('textScale'), 1, 0.5, 2.2, decimales=True),
                'textOpacity': numero_rango(item_config.get('textOpacity'), 1, 0, 1, decimales=True),
                'textVisible': bool(item_config.get('textVisible', True)),
                'textRotation': numero_rango(item_config.get('textRotation'), 0, -45, 45),
                'textLocked': bool(item_config.get('textLocked', False)),
                'textZ': numero_rango(item_config.get('textZ'), 2, 1, 5),
                'textWidth': numero_rango(item_config.get('textWidth'), 78, 12, 100),
                'textAlignLayer': item_config.get('textAlignLayer') if item_config.get('textAlignLayer') in EDITOR_ALINEACIONES else 'center',
                'decorX': numero_rango(item_config.get('decorX'), 50, -40, 140),
                'decorY': numero_rango(item_config.get('decorY'), 12, -40, 140),
                'decorScale': numero_rango(item_config.get('decorScale'), 1, 0.5, 2.2, decimales=True),
                'decorOpacity': numero_rango(item_config.get('decorOpacity'), 0.42, 0, 1, decimales=True),
                'decorVisible': bool(item_config.get('decorVisible', False)),
                'decorRotation': numero_rango(item_config.get('decorRotation'), 0, -45, 45),
                'decorLocked': bool(item_config.get('decorLocked', False)),
                'decorZ': numero_rango(item_config.get('decorZ'), 1, 1, 5),
                'decorWidth': numero_rango(item_config.get('decorWidth'), 36, 12, 100),
                'decorAlign': item_config.get('decorAlign') if item_config.get('decorAlign') in EDITOR_ALINEACIONES else 'center',
                'decorStyle': item_config.get('decorStyle') if item_config.get('decorStyle') in EDITOR_DECOR_STYLES else 'line',
                'customLayers': capas_personalizadas,
            },
        })

    for seccion_id, seccion in secciones_por_id.items():
        if seccion_id not in usados:
            config['sections'].append(serializar_seccion_editor(seccion))

    config['sections'] = sorted(config['sections'], key=lambda item: (item.get('order', 0), item.get('sectionId', 0)))
    return config or actual


def aplicar_diseno_publicado(evento, config):
    theme = config.get('theme', {})
    evento.paleta_colores = valor_choice_seguro(theme.get('palette'), EventoBoda.PALETAS, evento.paleta_colores)
    evento.paleta_sobre = valor_choice_seguro(theme.get('envelopePalette'), EventoBoda.PALETAS, evento.paleta_sobre)
    evento.estilo_letra = valor_choice_seguro(theme.get('fontStyle'), EventoBoda.ESTILOS_LETRA, evento.estilo_letra)
    evento.color_principal = color_seguro(theme.get('primary')) or evento.color_principal
    evento.color_secundario = color_seguro(theme.get('secondary')) or evento.color_secundario
    evento.color_acento = color_seguro(theme.get('accent')) or evento.color_acento
    campos_media_evento = {
        'coverAsset': 'foto_portada',
        'ceremonyAsset': 'foto_ceremonia',
        'receptionAsset': 'foto_recepcion',
        'dressAllowedAsset': 'dress_code_permitido_imagen',
        'dressBlockedAsset': 'dress_code_prohibido_imagen',
    }
    update_fields = [
        'paleta_colores',
        'paleta_sobre',
        'estilo_letra',
        'color_principal',
        'color_secundario',
        'color_acento',
    ]
    for config_key, campo in campos_media_evento.items():
        asset_ref = theme.get(config_key) if isinstance(theme.get(config_key), dict) else {}
        asset = AssetInvitacion.objects.filter(evento=evento, id=asset_ref.get('id'), visible=True).first()
        if asset:
            setattr(evento, campo, asset.archivo.name)
            update_fields.append(campo)
    evento.save(update_fields=[
        *dict.fromkeys(update_fields),
    ])

    for asset_ref in theme.get('albumAssets', []):
        if not isinstance(asset_ref, dict):
            continue
        asset = AssetInvitacion.objects.filter(evento=evento, id=asset_ref.get('id'), visible=True).first()
        if asset and not FotoEvento.objects.filter(evento=evento, imagen=asset.archivo.name).exists():
            FotoEvento.objects.create(evento=evento, titulo=asset.titulo, imagen=asset.archivo.name, visible=True)

    secciones_por_id = {seccion.id: seccion for seccion in sincronizar_secciones_invitacion(evento)}
    for item in config.get('sections', []):
        seccion = secciones_por_id.get(item.get('sectionId'))
        if not seccion:
            continue
        item_config = item.get('config') or {}
        seccion.titulo = item.get('title') or seccion.titulo
        seccion.descripcion = item.get('description') or ''
        seccion.orden = convertir_entero(item.get('order'), seccion.orden)
        seccion.activa = bool(item.get('visible'))
        if 'showTextTitle' in item_config:
            seccion.mostrar_titulo_texto = (
                item_config.get('showTextTitle') is True
            )
        seccion.posicion_fondo = item_config.get('backgroundPosition') or seccion.posicion_fondo
        seccion.color_texto = color_seguro(item_config.get('textColor')) or None
        seccion.opacidad_fondo = convertir_decimal(item_config.get('backgroundOpacity'), seccion.opacidad_fondo)
        background_asset_ref = item_config.get('backgroundAsset') if isinstance(item_config.get('backgroundAsset'), dict) else {}
        title_asset_ref = item_config.get('titleAsset') if isinstance(item_config.get('titleAsset'), dict) else {}
        background_asset = AssetInvitacion.objects.filter(evento=evento, id=background_asset_ref.get('id'), visible=True).first()
        title_asset = AssetInvitacion.objects.filter(evento=evento, id=title_asset_ref.get('id'), visible=True).first()
        if background_asset:
            seccion.fondo = background_asset.archivo.name
        if title_asset:
            seccion.imagen_titulo = title_asset.archivo.name
        seccion.save()


def fuentes_css_editor(estilo_letra):
    titulos = {
        'CLASICA': "'Playfair Display', serif",
        'EDITORIAL': "'Cormorant Garamond', serif",
        'MODERNA': "'Poppins', sans-serif",
        'ROMANTICA': "'Great Vibes', cursive",
        'MANUSCRITA': "'Allura', cursive",
        'CURSIVA_ELEGANTE': "'Parisienne', cursive",
    }
    textos = {
        'CLASICA': "'Montserrat', sans-serif",
        'EDITORIAL': "'Lato', sans-serif",
        'MODERNA': "'Inter', sans-serif",
        'ROMANTICA': "'Quicksand', sans-serif",
        'MANUSCRITA': "'Montserrat', sans-serif",
        'CURSIVA_ELEGANTE': "'Cormorant Garamond', serif",
    }
    return titulos.get(estilo_letra, titulos['CLASICA']), textos.get(estilo_letra, textos['CLASICA'])


def tema_preview_editor(config):
    theme = config.get('theme', {}) if isinstance(config, dict) else {}
    font_title, font_body = fuentes_css_editor(theme.get('fontStyle'))
    return {
        'primary': color_seguro(theme.get('primary')),
        'secondary': color_seguro(theme.get('secondary')),
        'accent': color_seguro(theme.get('accent')),
        'background': color_seguro(theme.get('background')),
        'font_title': font_title,
        'font_body': font_body,
    }


def estilo_editor_seccion(item_config):
    item_config = item_config or {}
    fit = item_config.get('backgroundFit') if item_config.get('backgroundFit') in EDITOR_BG_FIT else 'contain'
    repeat = 'repeat' if item_config.get('backgroundRepeat') == 'repeat' else 'no-repeat'
    scale = numero_rango(item_config.get('backgroundScale'), 1, 0.4, 3, decimales=True)
    scale_mobile = numero_rango(item_config.get('backgroundScaleMobile'), scale, 0.4, 3, decimales=True)
    scale_tablet = numero_rango(item_config.get('backgroundScaleTablet'), scale, 0.4, 3, decimales=True)
    scale_desktop = numero_rango(item_config.get('backgroundScaleDesktop'), scale, 0.4, 3, decimales=True)
    decor = {
        'line': '-',
        'flourish': '~',
        'rings': 'oo',
        'dots': '. . .',
    }.get(item_config.get('decorStyle'), '-')
    size = {
        'contain': 'contain',
        'cover': 'cover',
        'repeat': f'{max(int(scale * 140), 40)}px auto',
        'free': f'{max(int(scale * 100), 40)}% auto',
    }.get(fit, 'contain')
    def size_for(scale_value):
        return {
            'contain': 'contain',
            'cover': 'cover',
            'repeat': f'{max(int(scale_value * 140), 40)}px auto',
            'free': f'{max(int(scale_value * 100), 40)}% auto',
        }.get(fit, 'contain')
    return (
        f'--section-height:{numero_rango(item_config.get("sectionHeight"), 190, 120, 900)}px;'
        f'--section-bg-opacity:{numero_rango(item_config.get("backgroundOpacity"), 0.18, 0, 1, decimales=True)};'
        f'--section-bg-size:{size};'
        f'--section-bg-position:{numero_rango(item_config.get("backgroundX"), 50, 0, 100)}% '
        f'{numero_rango(item_config.get("backgroundY"), 50, 0, 100)}%;'
        f'--section-bg-size-mobile:{size_for(scale_mobile)};'
        f'--section-bg-position-mobile:{numero_rango(item_config.get("backgroundXMobile"), numero_rango(item_config.get("backgroundX"), 50, 0, 100), 0, 100)}% '
        f'{numero_rango(item_config.get("backgroundYMobile"), numero_rango(item_config.get("backgroundY"), 50, 0, 100), 0, 100)}%;'
        f'--section-bg-size-tablet:{size_for(scale_tablet)};'
        f'--section-bg-position-tablet:{numero_rango(item_config.get("backgroundXTablet"), numero_rango(item_config.get("backgroundX"), 50, 0, 100), 0, 100)}% '
        f'{numero_rango(item_config.get("backgroundYTablet"), numero_rango(item_config.get("backgroundY"), 50, 0, 100), 0, 100)}%;'
        f'--section-bg-size-desktop:{size_for(scale_desktop)};'
        f'--section-bg-position-desktop:{numero_rango(item_config.get("backgroundXDesktop"), numero_rango(item_config.get("backgroundX"), 50, 0, 100), 0, 100)}% '
        f'{numero_rango(item_config.get("backgroundYDesktop"), numero_rango(item_config.get("backgroundY"), 50, 0, 100), 0, 100)}%;'
        f'--section-bg-repeat:{repeat};'
        f'--section-bg-brightness:{numero_rango(item_config.get("backgroundBrightness"), 1, 0.35, 1.75, decimales=True)};'
        f'--section-bg-blur:{numero_rango(item_config.get("backgroundBlur"), 0, 0, 12, decimales=True)}px;'
        f'--section-title-x:{numero_rango(item_config.get("titleX"), 50, -40, 140)}%;'
        f'--section-title-y:{numero_rango(item_config.get("titleY"), 50, -40, 140)}%;'
        f'--section-title-scale:{numero_rango(item_config.get("titleScale"), 1, 0.5, 2.2, decimales=True)};'
        f'--section-title-opacity:{numero_rango(item_config.get("titleOpacity"), 1, 0, 1, decimales=True)};'
        f'--section-title-display:{"block" if item_config.get("titleVisible", True) else "none"};'
        f'--section-title-rotation:{numero_rango(item_config.get("titleRotation"), 0, -45, 45)}deg;'
        f'--section-title-z:{numero_rango(item_config.get("titleZ"), 2, 1, 5)};'
        f'--section-title-width:{numero_rango(item_config.get("titleWidth"), 72, 12, 100)}%;'
        f'--section-title-align:{item_config.get("titleAlign") if item_config.get("titleAlign") in EDITOR_ALINEACIONES else "center"};'
        f'--section-text-x:{numero_rango(item_config.get("textX"), 50, -40, 140)}%;'
        f'--section-text-y:{numero_rango(item_config.get("textY"), 50, -40, 140)}%;'
        f'--section-text-scale:{numero_rango(item_config.get("textScale"), 1, 0.5, 2.2, decimales=True)};'
        f'--section-text-opacity:{numero_rango(item_config.get("textOpacity"), 1, 0, 1, decimales=True)};'
        f'--section-text-display:{"block" if item_config.get("textVisible", True) else "none"};'
        f'--section-text-rotation:{numero_rango(item_config.get("textRotation"), 0, -45, 45)}deg;'
        f'--section-text-z:{numero_rango(item_config.get("textZ"), 2, 1, 5)};'
        f'--section-text-width:{numero_rango(item_config.get("textWidth"), 78, 12, 100)}%;'
        f'--section-text-align:{item_config.get("textAlignLayer") if item_config.get("textAlignLayer") in EDITOR_ALINEACIONES else "center"};'
        f'--section-decor-x:{numero_rango(item_config.get("decorX"), 50, -40, 140)}%;'
        f'--section-decor-y:{numero_rango(item_config.get("decorY"), 12, -40, 140)}%;'
        f'--section-decor-scale:{numero_rango(item_config.get("decorScale"), 1, 0.5, 2.2, decimales=True)};'
        f'--section-decor-opacity:{numero_rango(item_config.get("decorOpacity"), 0.42, 0, 1, decimales=True)};'
        f'--section-decor-display:{"block" if item_config.get("decorVisible", False) else "none"};'
        f'--section-decor-rotation:{numero_rango(item_config.get("decorRotation"), 0, -45, 45)}deg;'
        f'--section-decor-z:{numero_rango(item_config.get("decorZ"), 1, 1, 5)};'
        f'--section-decor-width:{numero_rango(item_config.get("decorWidth"), 36, 12, 100)}%;'
        f'--section-decor-align:{item_config.get("decorAlign") if item_config.get("decorAlign") in EDITOR_ALINEACIONES else "center"};'
        f'--section-decor-content:"{decor}";'
    )


def aplicar_configuracion_preview_a_secciones(secciones, config):
    if not isinstance(config, dict):
        return secciones
    resultado = {tipo: dict(datos) for tipo, datos in secciones.items()}
    for item in config.get('sections', []):
        tipo = item.get('type')
        if tipo not in resultado:
            continue
        datos = resultado[tipo]
        item_config = item.get('config') or {}
        datos.update({
            'titulo': item.get('title') or datos.get('titulo'),
            'descripcion': item.get('description') if item.get('description') is not None else datos.get('descripcion'),
            'orden': convertir_entero(item.get('order'), datos.get('orden', 0)),
            'activa': bool(item.get('visible')),
            'mostrar_titulo_texto': datos.get('mostrar_titulo_texto', True),
            'posicion_fondo': item_config.get('backgroundPosition') or datos.get('posicion_fondo', 'center center'),
            'opacidad_fondo': item_config.get('backgroundOpacity') or datos.get('opacidad_fondo'),
            'color_texto': color_seguro(item_config.get('textColor')) or datos.get('color_texto', ''),
            'editor_config': item_config,
            'estilo_editor': estilo_editor_seccion(item_config),
            'capas_personalizadas': capas_personalizadas_publicas(item_config),
        })
        if item_config.get('showBackgroundLayer') is False:
            datos['fondo'] = None
            datos['fondo_es_video'] = False
        if item_config.get('showTitleAsset') is False:
            datos['imagen_titulo'] = None
            datos['imagen_titulo_es_video'] = False
    return resultado


def usuario_puede_previsualizar_borrador(request, evento):
    return (
        request.user.is_authenticated
        and request.GET.get('draft') == '1'
        and eventos_visibles_usuario(request.user).filter(id=evento.id).exists()
    )


def limpiar_json_texto(payload, campo, max_length=None):
    valor = payload.get(campo)
    if valor is None:
        return None
    valor = str(valor).strip()
    return valor[:max_length] if max_length else valor


def fecha_hora_editor(valor, actual):
    if not valor:
        return actual
    for formato in ('%Y-%m-%dT%H:%M', '%Y-%m-%d %H:%M'):
        try:
            fecha = datetime.strptime(valor, formato)
            return timezone.make_aware(fecha) if timezone.is_naive(fecha) else fecha
        except ValueError:
            continue
    return actual


def serializar_persona_editor(persona):
    return {
        'id': persona.id,
        'section': persona.seccion,
        'sectionLabel': persona.get_seccion_display(),
        'label': persona.etiqueta,
        'name': persona.nombre,
        'order': persona.orden,
        'visible': persona.visible,
    }


def serializar_regalo_editor(regalo):
    return {
        'id': regalo.id,
        'type': regalo.tipo,
        'typeLabel': regalo.get_tipo_display(),
        'name': regalo.nombre,
        'url': regalo.url or '',
        'bank': regalo.banco or '',
        'holder': regalo.titular or '',
        'account': regalo.numero_cuenta or '',
        'clabe': regalo.clabe or '',
        'instructions': regalo.instrucciones or '',
        'visible': regalo.visible,
    }


def serializar_itinerario_editor(item):
    return {
        'id': item.id,
        'time': item.hora.strftime('%H:%M') if item.hora else '',
        'title': item.titulo,
        'description': item.descripcion or '',
        'icon': item.icono,
        'order': item.orden,
        'visible': item.visible,
    }


def qr_url_para_link(link):
    return f'https://api.qrserver.com/v1/create-qr-code/?size=180x180&data={quote(link, safe="")}'


def mesa_actual_grupo(grupo):
    asignacion = grupo.asignaciones_mesa.select_related('mesa').first()
    return asignacion.mesa if asignacion else None


def mesa_actual_invitado(invitado):
    asignacion = invitado.asignaciones_mesa.select_related('mesa').first()
    return asignacion.mesa if asignacion else None


def serializar_invitado_editor(invitado):
    mesa = mesa_actual_invitado(invitado)
    return {
        'id': invitado.id,
        'name': invitado.nombre,
        'lastName': invitado.apellidos or '',
        'type': invitado.tipo_persona,
        'phone': invitado.telefono or '',
        'email': invitado.correo or '',
        'tableId': mesa.id if mesa else '',
        'tableName': mesa.nombre if mesa else (invitado.mesa or ''),
        'order': invitado.orden,
        'menuInfantil': invitado.menu_infantil,
        'allergies': invitado.alergias or '',
        'restrictions': invitado.restricciones_alimentarias or '',
        'status': 'SI' if invitado.asistira is True else 'NO' if invitado.asistira is False else 'PENDIENTE',
    }


def serializar_grupo_editor(grupo, base_url):
    link = f'{base_url}/invitacion/{grupo.codigo}/'
    mesa = mesa_actual_grupo(grupo)
    return {
        'id': grupo.id,
        'name': grupo.nombre_grupo,
        'type': grupo.tipo,
        'typeLabel': grupo.get_tipo_display(),
        'maxGuests': grupo.cantidad_maxima,
        'extraAllowed': grupo.cantidad_extra_permitida,
        'phone': grupo.telefono_contacto or '',
        'email': grupo.correo_contacto or '',
        'tableId': mesa.id if mesa else '',
        'tableName': mesa.nombre if mesa else (grupo.mesa or ''),
        'link': link,
        'qrUrl': qr_url_para_link(link),
        'confirmed': grupo.confirmado,
        'places': grupo.total_lugares,
        'attending': grupo.lugares_asistiran,
        'adults': grupo.adultos_confirmados,
        'children': grupo.ninos_confirmados,
        'guests': [serializar_invitado_editor(invitado) for invitado in grupo.invitados.all()],
    }


def mesas_editor_payload(evento):
    return [
        {
            'id': mesa.id,
            'name': mesa.nombre,
            'capacity': mesa.capacidad,
            'available': mesa.lugares_disponibles,
            'occupied': mesa.lugares_ocupados,
        }
        for mesa in Mesa.objects.filter(evento=evento)
    ]


def invitados_editor_payload(evento, request):
    base_url = request.build_absolute_uri('/')[:-1]
    grupos = (
        Grupoinvitacion.objects.filter(evento=evento)
        .prefetch_related('invitados', 'asignaciones_mesa__mesa', 'invitados__asignaciones_mesa__mesa')
        .order_by('tipo', 'nombre_grupo')
    )
    return {
        'groups': [serializar_grupo_editor(grupo, base_url) for grupo in grupos],
        'tables': mesas_editor_payload(evento),
        'types': [{'value': value, 'label': label} for value, label in Grupoinvitacion.TIPO_INVITACION],
        'personTypes': [{'value': value, 'label': label} for value, label in Invitado.TIPO_PERSONA],
    }


def asignar_mesa_a_grupo_personal(grupo, mesa_id):
    grupo.asignaciones_mesa.all().delete()
    mesa_id = convertir_entero(mesa_id, 0)
    if not mesa_id:
        grupo.mesa = None
        grupo.save(update_fields=['mesa'])
        return
    mesa = get_object_or_404(Mesa, evento=grupo.evento, id=mesa_id)
    AsignacionMesa.objects.create(mesa=mesa, grupo_invitacion=grupo)
    grupo.mesa = mesa.nombre
    grupo.save(update_fields=['mesa'])


def asignar_mesa_a_invitado(invitado, mesa_id):
    invitado.asignaciones_mesa.all().delete()
    mesa_id = convertir_entero(mesa_id, 0)
    if not mesa_id:
        invitado.mesa = None
        invitado.save(update_fields=['mesa'])
        return
    mesa = get_object_or_404(Mesa, evento=invitado.grupo.evento, id=mesa_id)
    AsignacionMesa.objects.create(mesa=mesa, invitado=invitado)
    invitado.mesa = mesa.nombre
    invitado.save(update_fields=['mesa'])


def sincronizar_acompanantes_personales(grupo):
    if not grupo.es_personal:
        return
    objetivo = convertir_entero(grupo.cantidad_extra_permitida, 0)
    actuales = list(grupo.invitados.order_by('orden', 'id'))
    while len(actuales) < objetivo:
        invitado = Invitado.objects.create(
            grupo=grupo,
            nombre=f'Acompanante {len(actuales) + 1}',
            tipo_persona='ADULTO',
            orden=len(actuales) + 1,
        )
        actuales.append(invitado)
    if len(actuales) <= objetivo:
        return
    sobrantes = [
        invitado for invitado in actuales[objetivo:]
        if (invitado.nombre or '').startswith('Acompanante ') and invitado.asistira is None
    ]
    for invitado in sobrantes:
        invitado.delete()


def valor_importado(row, *keys):
    for key in keys:
        value = row.get(key)
        if value not in (None, ''):
            return str(value).strip()
    return ''


def normalizar_header_importacion(header):
    value = str(header or '').strip().lower()
    value = re.sub(r'[^a-z0-9]+', '_', value)
    return value.strip('_')


def filas_importadas_invitados(archivo):
    nombre = (archivo.name or '').lower()
    if nombre.endswith('.csv'):
        texto = archivo.read().decode('utf-8-sig')
        return [
            {normalizar_header_importacion(key): value for key, value in row.items()}
            for row in csv.DictReader(io.StringIO(texto))
        ]
    workbook = load_workbook(archivo, read_only=True, data_only=True)
    sheet = workbook.active
    rows = list(sheet.iter_rows(values_only=True))
    if not rows:
        return []
    headers = [normalizar_header_importacion(value) for value in rows[0]]
    resultado = []
    for row in rows[1:]:
        resultado.append({headers[index]: row[index] for index in range(min(len(headers), len(row))) if headers[index]})
    return resultado


def tipo_grupo_importado(valor):
    valor = (valor or '').strip().upper()
    if valor.startswith('FAM'):
        return 'FAMILIAR'
    return 'PERSONAL'


def tipo_persona_importado(valor):
    valor = (valor or '').strip().upper()
    if valor.startswith('N') or valor in {'CHILD', 'KID', 'MENOR'}:
        return 'NINO'
    return 'ADULTO'


def bool_importado(valor):
    return str(valor or '').strip().lower() in {'1', 'si', 'sí', 'true', 'x', 'yes'}


def importar_invitados_desde_filas(evento, filas):
    creados = 0
    actualizados = 0
    grupos_tocados = set()
    for row in filas:
        grupo_nombre = valor_importado(row, 'grupo', 'familia', 'invitacion', 'nombre_grupo')
        nombre = valor_importado(row, 'nombre', 'invitado', 'nombre_invitado', 'persona')
        apellidos = valor_importado(row, 'apellidos', 'apellido')
        if not grupo_nombre and nombre:
            grupo_nombre = nombre
        if not grupo_nombre:
            continue
        tipo_grupo = tipo_grupo_importado(valor_importado(row, 'tipo_grupo', 'tipo_invitacion', 'tipo'))
        grupo, creado_grupo = Grupoinvitacion.objects.get_or_create(
            evento=evento,
            nombre_grupo=grupo_nombre[:100],
            defaults={
                'tipo': tipo_grupo,
                'cantidad_maxima': 1,
                'cantidad_extra_permitida': 0,
            },
        )
        if not creado_grupo:
            grupo.tipo = tipo_grupo
        grupo.telefono_contacto = valor_importado(row, 'telefono', 'celular', 'whatsapp')[:20] or grupo.telefono_contacto
        grupo.correo_contacto = valor_importado(row, 'correo', 'email')[:200] or grupo.correo_contacto
        extras = convertir_entero(valor_importado(row, 'extras', 'acompanantes', 'acompanantes_permitidos'), grupo.cantidad_extra_permitida)
        grupo.cantidad_extra_permitida = extras if grupo.es_personal else 0
        grupo.cantidad_maxima = max(convertir_entero(valor_importado(row, 'lugares', 'cantidad', 'cantidad_maxima'), grupo.cantidad_maxima), 1)
        grupo.save()
        grupos_tocados.add(grupo.id)

        es_extra = bool_importado(valor_importado(row, 'extra', 'es_extra', 'acompanante'))
        debe_crear_invitado = grupo.es_familiar or es_extra or (grupo.es_personal and nombre and nombre != grupo.nombre_grupo)
        if debe_crear_invitado and nombre:
            invitado, creado_invitado = Invitado.objects.update_or_create(
                grupo=grupo,
                nombre=nombre[:100],
                apellidos=apellidos[:120] or None,
                defaults={
                    'tipo_persona': tipo_persona_importado(valor_importado(row, 'tipo_persona', 'persona_tipo', 'adulto_nino')),
                    'telefono': valor_importado(row, 'telefono_invitado', 'telefono', 'celular')[:30] or None,
                    'correo': valor_importado(row, 'correo_invitado', 'correo', 'email')[:200] or None,
                    'mesa': valor_importado(row, 'mesa')[:50] or None,
                    'alergias': valor_importado(row, 'alergias') or None,
                    'restricciones_alimentarias': valor_importado(row, 'restricciones', 'restricciones_alimentarias') or None,
                    'menu_infantil': bool_importado(valor_importado(row, 'menu_infantil', 'buffet_nino')),
                },
            )
            creados += 1 if creado_invitado else 0
            actualizados += 0 if creado_invitado else 1
            if grupo.es_personal:
                grupo.cantidad_extra_permitida = max(grupo.cantidad_extra_permitida, grupo.invitados.count())
                grupo.save(update_fields=['cantidad_extra_permitida'])
        else:
            creados += 1 if creado_grupo else 0
            actualizados += 0 if creado_grupo else 1
    for grupo in Grupoinvitacion.objects.filter(evento=evento, id__in=grupos_tocados, tipo='PERSONAL'):
        if not grupo.invitados.exists():
            sincronizar_acompanantes_personales(grupo)
    return creados, actualizados


def contenido_editor_payload(evento):
    return {
        'event': {
            'eventName': evento.nombre_evento or '',
            'mainName': evento.nombre_principal or '',
            'secondaryName': evento.nombre_secundario or '',
            'mainLabel': evento.etiqueta_principal or '',
            'secondaryLabel': evento.etiqueta_secundario or '',
            'showSecondaryName': evento.mostrar_nombre_secundario,
            'coverPhrase': evento.frase_portada or '',
            'generalMessage': evento.mensaje_general or '',
            'invitationTitle': evento.titulo_invitacion or '',
            'invitationText': evento.texto_invitacion or '',
            'detailsTitle': evento.titulo_detalles or '',
            'detailsText': evento.texto_detalles or '',
            'rsvpTitle': evento.titulo_rsvp or '',
            'rsvpText': evento.texto_rsvp or '',
            'ceremonyDate': evento.fecha_misa.strftime('%Y-%m-%dT%H:%M') if evento.fecha_misa else '',
            'ceremonyPlace': evento.lugar_misa or '',
            'ceremonyAddress': evento.direccion_ceremonia or '',
            'ceremonyMapUrl': evento.link_mapa_misa or '',
            'ceremonyMapEmbed': evento.mapa_misa_embed or '',
            'receptionDate': evento.fecha_fiesta.strftime('%Y-%m-%dT%H:%M') if evento.fecha_fiesta else '',
            'receptionPlace': evento.lugar_fiesta or '',
            'receptionAddress': evento.direccion_recepcion or '',
            'receptionMapUrl': evento.link_mapa_fiesta or '',
            'receptionMapEmbed': evento.mapa_fiesta_embed or '',
            'dressCode': evento.dress_code or '',
            'dressCodeText': evento.dress_code_descripcion or '',
            'sharedAlbumTitle': evento.titulo_album_compartido or '',
            'sharedAlbumText': evento.texto_album_compartido or '',
            'sharedAlbumUrl': evento.link_album_compartido or '',
            'showAlbum': evento.mostrar_album,
            'showMenu': evento.mostrar_menu,
            'showGifts': evento.mostrar_regalos,
            'showMaps': evento.mostrar_mapa,
            'showSharedAlbum': evento.mostrar_album_compartido,
        },
        'people': [serializar_persona_editor(persona) for persona in evento.personas_ceremonia.all()],
        'gifts': [serializar_regalo_editor(regalo) for regalo in evento.regalos.all()],
        'itinerary': [serializar_itinerario_editor(item) for item in evento.itinerario.all()],
    }


def serializar_version_editor(version):
    configuracion = version.configuracion or {}
    tema = configuracion.get('theme') or {}
    secciones = configuracion.get('sections') or []
    primera_seccion = next((seccion for seccion in secciones if seccion.get('visible', True)), {})
    return {
        'id': version.id,
        'name': version.nombre,
        'published': version.publicado,
        'createdAt': timezone.localtime(version.fecha_creacion).strftime('%d/%m/%Y %H:%M'),
        'createdBy': version.creado_por.get_username() if version.creado_por else '',
        'primary': tema.get('primary') or '#22252d',
        'accent': tema.get('accent') or '#c8a96a',
        'sectionCount': len(secciones),
        'firstTitle': primera_seccion.get('title') or '',
    }


def versiones_editor_payload(diseno, limite=12):
    return [
        serializar_version_editor(version)
        for version in diseno.versiones.select_related('creado_por').all()[:limite]
    ]


def aplicar_plantilla_a_diseno_editor(evento, diseno, codigo, usuario=None):
    aplicar_plantilla_evento(evento, codigo)
    evento.save()
    aplicar_estructura_plantilla_evento(evento, codigo)
    config = construir_configuracion_diseno(evento)
    diseno.configuracion_borrador = normalizar_configuracion_editor(evento, config)
    diseno.estado = 'BORRADOR'
    diseno.actualizado_por = usuario if usuario and usuario.is_authenticated else diseno.actualizado_por
    diseno.save(update_fields=['configuracion_borrador', 'estado', 'actualizado_por', 'fecha_actualizacion'])
    VersionDisenoInvitacion.objects.create(
        diseno=diseno,
        nombre=f'Plantilla {dict(PLANTILLAS_EVENTO).get(codigo, codigo)}',
        configuracion=diseno.configuracion_borrador,
        publicado=False,
        creado_por=usuario if usuario and usuario.is_authenticated else None,
    )
    return diseno.configuracion_borrador


def actualizar_seccion_invitacion_dashboard(request, evento):
    seccion = get_object_or_404(SeccionInvitacion, evento=evento, id=request.POST.get('seccion_id'))
    seccion.titulo = limpiar_texto(request, 'titulo_seccion') or seccion.titulo
    seccion.descripcion = request.POST.get('descripcion_seccion', '').strip()
    seccion.orden = convertir_entero(request.POST.get('orden_seccion'), seccion.orden)
    seccion.activa = bool_post(request, 'activa_seccion')
    seccion.mostrar_titulo_texto = bool_post(request, 'mostrar_titulo_texto')
    seccion.posicion_fondo = request.POST.get('posicion_fondo') or seccion.posicion_fondo
    seccion.color_texto = limpiar_texto(request, 'color_texto_seccion')
    seccion.opacidad_fondo = convertir_decimal(request.POST.get('opacidad_fondo'), seccion.opacidad_fondo)

    for campo in ('fondo', 'imagen_titulo'):
        if request.POST.get(f'eliminar_{campo}') == 'on':
            archivo_actual = getattr(seccion, campo, None)
            if archivo_actual:
                archivo_actual.delete(save=False)
            setattr(seccion, campo, None)

    for campo in ('fondo', 'imagen_titulo'):
        archivo = request.FILES.get(campo)
        if archivo and archivo_pasa_validadores(SeccionInvitacion, campo, archivo):
            setattr(seccion, campo, archivo)

    seccion.save()
    registrar_auditoria(
        usuario=request.user,
        empresa=evento.empresa,
        evento=evento,
        accion='ACTUALIZAR_SECCION_INVITACION',
        modelo='SeccionInvitacion',
        objeto_id=seccion.id,
        descripcion=f'Actualizo seccion de invitacion: {seccion.get_tipo_display()}.',
        request=request,
    )
    return seccion


@xframe_options_sameorigin
def ver_invitacion(request, codigo):
    grupo = get_object_or_404(
        Grupoinvitacion.objects.select_related('evento').prefetch_related(
            'invitados',
            'evento__fotos',
            'evento__regalos',
            'evento__menus',
            'evento__itinerario',
            'evento__personas_ceremonia',
            'evento__secciones_invitacion',
        ),
        codigo=codigo
    )
    evento = grupo.evento or EventoBoda.objects.filter(activo=True).first() or EventoBoda.objects.first()

    if request.method == 'POST':
        if grupo.es_personal:
            procesar_respuesta_personal(request, grupo)
        else:
            procesar_respuesta_familiar(request, grupo)

        return redirect('ver_invitacion', codigo=grupo.codigo)

    secciones_context = construir_secciones_invitacion(evento)
    tema_editor = {}
    if evento:
        diseno_preview = DisenoInvitacion.objects.filter(evento=evento).first()
        if diseno_preview:
            if usuario_puede_previsualizar_borrador(request, evento):
                config_preview = diseno_preview.configuracion_borrador or {}
            else:
                config_preview = diseno_preview.configuracion_publicada or {}
            secciones_context = aplicar_configuracion_preview_a_secciones(secciones_context, config_preview)
            tema_editor = tema_preview_editor(config_preview)

    context = {
        'grupo': grupo,
        'evento': evento,
        'fotos_album': evento.fotos.filter(visible=True) if evento else [],
        'regalos': evento.regalos.filter(visible=True) if evento else [],
        'menus': evento.menus.filter(visible=True) if evento else [],
        'itinerario': evento.itinerario.filter(visible=True) if evento else [],
        'padres_novio': evento.personas_ceremonia.filter(seccion='PADRES_NOVIO', visible=True) if evento else [],
        'padres_novia': evento.personas_ceremonia.filter(seccion='PADRES_NOVIA', visible=True) if evento else [],
        'padrinos': evento.personas_ceremonia.filter(seccion='PADRINOS', visible=True) if evento else [],
        'secciones': secciones_context,
        'tema_editor_preview': tema_editor,
        'modo_preview': request.GET.get('preview') == '1',
    }

    return render(request, 'invitaciones/ver_invitacion.html', context)


def procesar_respuesta_personal(request, grupo):
    respuesta = request.POST.get('asistira')
    comentario = request.POST.get('comentario', '').strip()
    acompanantes = list(grupo.invitados.all())

    if respuesta == 'si':
        if acompanantes:
            adultos = 0
            ninos = 0
            for invitado in acompanantes:
                respuesta_extra = request.POST.get(f'asistira_extra_{invitado.id}')
                if respuesta_extra == 'si':
                    invitado.asistira = True
                elif respuesta_extra == 'no':
                    invitado.asistira = False
                else:
                    invitado.asistira = None
                invitado.menu_infantil = request.POST.get(f'menu_infantil_extra_{invitado.id}') == 'on'
                invitado.comentario = request.POST.get(f'comentario_extra_{invitado.id}', '').strip()
                invitado.fecha_confirmacion = timezone.now() if invitado.asistira is not None else None
                invitado.save()
                if invitado.asistira is True and invitado.tipo_persona == 'NINO':
                    ninos += 1
                elif invitado.asistira is True:
                    adultos += 1
        else:
            total = convertir_entero(request.POST.get('acompanantes_total'), None)
            if total is None:
                adultos = convertir_entero(request.POST.get('acompanantes_adultos'), 0)
                ninos = convertir_entero(request.POST.get('acompanantes_ninos'), 0)
            else:
                adultos = total
                ninos = 0
            adultos, ninos = ajustar_acompanantes(adultos, ninos, grupo.cantidad_extra_permitida)

        grupo.asistira = True
        grupo.acompanantes_adultos = adultos
        grupo.acompanantes_ninos = ninos
        grupo.cantidad_confirmada = 1 + adultos + ninos
    elif respuesta == 'no':
        grupo.asistira = False
        grupo.acompanantes_adultos = 0
        grupo.acompanantes_ninos = 0
        grupo.cantidad_confirmada = 0
        for invitado in acompanantes:
            invitado.asistira = False
            invitado.fecha_confirmacion = timezone.now()
            invitado.save(update_fields=['asistira', 'fecha_confirmacion'])
    else:
        grupo.asistira = None
        grupo.acompanantes_adultos = 0
        grupo.acompanantes_ninos = 0
        grupo.cantidad_confirmada = None
        for invitado in acompanantes:
            invitado.asistira = None
            invitado.fecha_confirmacion = None
            invitado.save(update_fields=['asistira', 'fecha_confirmacion'])

    grupo.comentario = comentario
    grupo.restricciones_alimentarias = request.POST.get('restricciones_alimentarias', '').strip()
    grupo.alergias = request.POST.get('alergias', '').strip()
    grupo.requiere_menu_infantil = request.POST.get('requiere_menu_infantil') == 'on' or any(invitado.menu_infantil for invitado in acompanantes)
    grupo.confirmado = grupo.asistira is not None
    grupo.fecha_confirmacion = timezone.now() if grupo.confirmado else None
    grupo.save()


def procesar_respuesta_familiar(request, grupo):
    invitados = list(grupo.invitados.all())
    for invitado in invitados:
        respuesta = request.POST.get(f'asistira_{invitado.id}')
        comentario = request.POST.get(f'comentario_{invitado.id}', '').strip()

        if respuesta == 'si':
            invitado.asistira = True
        elif respuesta == 'no':
            invitado.asistira = False
        else:
            invitado.asistira = None

        invitado.comentario = comentario
        invitado.restricciones_alimentarias = request.POST.get(f'restricciones_{invitado.id}', '').strip()
        invitado.alergias = request.POST.get(f'alergias_{invitado.id}', '').strip()
        invitado.menu_infantil = request.POST.get(f'menu_infantil_{invitado.id}') == 'on'
        invitado.fecha_confirmacion = timezone.now() if invitado.asistira is not None else None
        invitado.save()

    grupo.comentario = request.POST.get('comentario_grupo', '').strip()
    grupo.confirmado = bool(invitados) and all(invitado.asistira is not None for invitado in invitados)
    grupo.fecha_confirmacion = timezone.now() if grupo.confirmado else None
    grupo.save(update_fields=['comentario', 'confirmado', 'fecha_confirmacion'])


def convertir_entero(valor, default=0):
    try:
        return max(int(valor), 0)
    except (TypeError, ValueError):
        return default


PLANTILLAS_EVENTO = [
    ('BODA', 'Boda elegante'),
    ('XV', 'XV años'),
    ('BABY_SHOWER', 'Baby shower'),
    ('BAUTIZO', 'Bautizo'),
    ('CUMPLEANOS', 'Cumpleanos'),
    ('CORPORATIVO', 'Corporativo'),
]

CONFIGURACION_PLANTILLAS_EVENTO = {
    'BODA': {
        'campos': {
            'tipo_evento': 'BODA',
            'paleta_colores': 'TINTA_MARFIL',
            'paleta_sobre': 'TINTA_MARFIL',
            'estilo_letra': 'CURSIVA_ELEGANTE',
            'etiqueta_principal': 'Novia',
            'etiqueta_secundario': 'Novio',
            'mostrar_nombre_secundario': True,
            'mostrar_album': True,
            'mostrar_menu': True,
            'mostrar_regalos': True,
            'mostrar_mapa': True,
            'mostrar_album_compartido': True,
            'frase_portada': 'Nuestra Boda',
            'titulo_invitacion': 'Con mucha alegria te invitamos',
            'texto_invitacion': 'Tu presencia hara este dia todavia mas especial.',
            'titulo_cuenta_regresiva': 'Faltan',
            'titulo_detalles': 'Ceremonia y recepcion',
            'texto_detalles': 'Ceremonia, recepcion, ubicacion y dress code reunidos para acompanarnos sin complicaciones.',
            'titulo_album': 'Nuestra historia',
            'titulo_menu': 'Menu de la boda',
            'titulo_regalos': 'Mesa de regalos',
            'titulo_album_compartido': 'Comparte tus fotos',
            'texto_album_compartido': 'Ayudanos a guardar tus mejores momentos. Sube tus fotos y videos al album compartido.',
            'titulo_rsvp': 'Confirma tu asistencia',
            'texto_rsvp': 'Tu respuesta nos ayuda a organizar lugares, mesas y buffet.',
        },
        'secciones': {
            'PORTADA': {'orden': 5, 'activa': True},
            'PADRES_PADRINOS': {'orden': 12, 'activa': True, 'titulo': 'Nuestros padres y padrinos'},
            'CUENTA_REGRESIVA': {'orden': 20, 'activa': True},
            'DETALLES': {'orden': 30, 'activa': True},
            'DRESS_CODE': {'orden': 35, 'activa': True},
            'ITINERARIO': {'orden': 40, 'activa': True, 'titulo': 'Itinerario'},
            'ALBUM': {'orden': 50, 'activa': True},
            'MENU': {'orden': 60, 'activa': True},
            'REGALOS': {'orden': 70, 'activa': True},
            'ALBUM_COMPARTIDO': {'orden': 75, 'activa': True},
            'RSVP': {'orden': 80, 'activa': True},
        },
    },
    'XV': {
        'campos': {
            'tipo_evento': 'XV',
            'paleta_colores': 'ROSA',
            'paleta_sobre': 'ROSA',
            'estilo_letra': 'ROMANTICA',
            'etiqueta_principal': 'Festejada',
            'etiqueta_secundario': 'Familia',
            'mostrar_nombre_secundario': False,
            'mostrar_album': True,
            'mostrar_menu': True,
            'mostrar_regalos': True,
            'mostrar_mapa': True,
            'mostrar_album_compartido': True,
            'frase_portada': 'Mis XV años',
            'titulo_invitacion': 'Celebra conmigo',
            'texto_invitacion': 'Me encantaria compartir esta noche tan especial contigo.',
            'titulo_cuenta_regresiva': 'Faltan',
            'titulo_detalles': 'Misa y fiesta',
            'texto_detalles': 'Aqui encontraras horarios, ubicacion, dress code y todo lo necesario para celebrar juntos.',
            'titulo_album': 'Momentos especiales',
            'titulo_menu': 'Menu de la fiesta',
            'titulo_regalos': 'Regalos',
            'titulo_album_compartido': 'Sube tus fotos',
            'texto_album_compartido': 'Comparte fotos y videos de la fiesta para guardar todos los recuerdos.',
            'titulo_rsvp': 'Confirma tu asistencia',
            'texto_rsvp': 'Tu confirmacion nos ayuda a preparar tu lugar en la fiesta.',
        },
        'secciones': {
            'PORTADA': {'orden': 5, 'activa': True},
            'PADRES_PADRINOS': {'orden': 12, 'activa': True, 'titulo': 'Mis padres y padrinos'},
            'CUENTA_REGRESIVA': {'orden': 20, 'activa': True},
            'DETALLES': {'orden': 30, 'activa': True},
            'DRESS_CODE': {'orden': 35, 'activa': True},
            'ITINERARIO': {'orden': 40, 'activa': True, 'titulo': 'Programa'},
            'ALBUM': {'orden': 50, 'activa': True},
            'MENU': {'orden': 60, 'activa': True},
            'REGALOS': {'orden': 70, 'activa': True},
            'ALBUM_COMPARTIDO': {'orden': 75, 'activa': True},
            'RSVP': {'orden': 80, 'activa': True},
        },
    },
    'BABY_SHOWER': {
        'campos': {
            'tipo_evento': 'BABY_SHOWER',
            'paleta_colores': 'SALVIA_PERLA',
            'paleta_sobre': 'SALVIA_PERLA',
            'estilo_letra': 'MANUSCRITA',
            'etiqueta_principal': 'Bebe',
            'etiqueta_secundario': 'Familia',
            'mostrar_nombre_secundario': False,
            'mostrar_album': True,
            'mostrar_menu': True,
            'mostrar_regalos': True,
            'mostrar_mapa': True,
            'mostrar_album_compartido': True,
            'frase_portada': 'Baby Shower',
            'titulo_invitacion': 'Celebremos esta dulce espera',
            'texto_invitacion': 'Acompananos a celebrar la llegada de nuestro bebe.',
            'titulo_cuenta_regresiva': 'Faltan',
            'titulo_detalles': 'Detalles del baby shower',
            'texto_detalles': 'Te compartimos horario, direccion, mesa de regalos y detalles para celebrar esta llegada especial.',
            'titulo_album': 'Momentos del baby shower',
            'titulo_menu': 'Bocadillos y bebidas',
            'titulo_regalos': 'Mesa de regalos',
            'titulo_album_compartido': 'Comparte tus fotos',
            'texto_album_compartido': 'Sube fotos y videos del baby shower para guardar este recuerdo.',
            'titulo_rsvp': 'Confirma tu asistencia',
            'texto_rsvp': 'Tu confirmacion nos ayuda a preparar cada detalle.',
        },
        'secciones': {
            'PORTADA': {'orden': 5, 'activa': True},
            'PADRES_PADRINOS': {'orden': 12, 'activa': False, 'titulo': 'Familia'},
            'CUENTA_REGRESIVA': {'orden': 20, 'activa': True},
            'DETALLES': {'orden': 30, 'activa': True},
            'DRESS_CODE': {'orden': 35, 'activa': False},
            'ITINERARIO': {'orden': 40, 'activa': False, 'titulo': 'Actividades'},
            'ALBUM': {'orden': 50, 'activa': True},
            'MENU': {'orden': 60, 'activa': True},
            'REGALOS': {'orden': 70, 'activa': True},
            'ALBUM_COMPARTIDO': {'orden': 75, 'activa': True},
            'RSVP': {'orden': 80, 'activa': True},
        },
    },
    'BAUTIZO': {
        'campos': {
            'tipo_evento': 'BAUTIZO',
            'paleta_colores': 'DORADO',
            'paleta_sobre': 'DORADO',
            'estilo_letra': 'CLASICA',
            'etiqueta_principal': 'Bautizado',
            'etiqueta_secundario': 'Familia',
            'mostrar_nombre_secundario': False,
            'mostrar_album': True,
            'mostrar_menu': True,
            'mostrar_regalos': False,
            'mostrar_mapa': True,
            'mostrar_album_compartido': True,
            'frase_portada': 'Mi Bautizo',
            'titulo_invitacion': 'Con alegria te invitamos',
            'texto_invitacion': 'Acompanamos en este dia de bendicion y celebracion familiar.',
            'titulo_cuenta_regresiva': 'Faltan',
            'titulo_detalles': 'Ceremonia y celebracion',
            'texto_detalles': 'Aqui tienes los horarios, ubicaciones y detalles para acompanarnos en este dia especial.',
            'titulo_album': 'Recuerdos del bautizo',
            'titulo_menu': 'Menu de la celebracion',
            'titulo_regalos': 'Detalles',
            'titulo_album_compartido': 'Comparte tus fotos',
            'texto_album_compartido': 'Ayudanos a guardar fotos y videos de este dia tan especial.',
            'titulo_rsvp': 'Confirma tu asistencia',
            'texto_rsvp': 'Tu respuesta nos ayuda a organizar la celebracion.',
        },
        'secciones': {
            'PORTADA': {'orden': 5, 'activa': True},
            'PADRES_PADRINOS': {'orden': 12, 'activa': True, 'titulo': 'Padres y padrinos'},
            'CUENTA_REGRESIVA': {'orden': 20, 'activa': True},
            'DETALLES': {'orden': 30, 'activa': True},
            'DRESS_CODE': {'orden': 35, 'activa': False},
            'ITINERARIO': {'orden': 40, 'activa': True, 'titulo': 'Itinerario'},
            'ALBUM': {'orden': 50, 'activa': True},
            'MENU': {'orden': 60, 'activa': True},
            'REGALOS': {'orden': 70, 'activa': False},
            'ALBUM_COMPARTIDO': {'orden': 75, 'activa': True},
            'RSVP': {'orden': 80, 'activa': True},
        },
    },
    'CUMPLEANOS': {
        'campos': {
            'tipo_evento': 'CUMPLEANOS',
            'paleta_colores': 'TERRACOTA',
            'paleta_sobre': 'TERRACOTA',
            'estilo_letra': 'MODERNA',
            'etiqueta_principal': 'Festejado',
            'etiqueta_secundario': 'Familia',
            'mostrar_nombre_secundario': False,
            'mostrar_album': True,
            'mostrar_menu': True,
            'mostrar_regalos': True,
            'mostrar_mapa': True,
            'mostrar_album_compartido': True,
            'frase_portada': 'Mi Cumpleanos',
            'titulo_invitacion': 'Celebremos juntos',
            'texto_invitacion': 'Tu presencia hara que este festejo sea mucho mas especial.',
            'titulo_cuenta_regresiva': 'Faltan',
            'titulo_detalles': 'Detalles de la fiesta',
            'texto_detalles': 'Aqui tienes horario, ubicacion, regalos y detalles para llegar sin complicaciones.',
            'titulo_album': 'Momentos especiales',
            'titulo_menu': 'Menu del festejo',
            'titulo_regalos': 'Mesa de regalos',
            'titulo_album_compartido': 'Comparte tus fotos',
            'texto_album_compartido': 'Sube tus fotos y videos para guardar juntos los mejores momentos.',
            'titulo_rsvp': 'Confirma tu asistencia',
            'texto_rsvp': 'Tu respuesta nos ayuda a organizar lugares, alimentos y detalles.',
        },
        'secciones': {
            'PORTADA': {'orden': 5, 'activa': True},
            'PADRES_PADRINOS': {'orden': 12, 'activa': False, 'titulo': 'Familia'},
            'CUENTA_REGRESIVA': {'orden': 20, 'activa': True},
            'DETALLES': {'orden': 30, 'activa': True},
            'DRESS_CODE': {'orden': 35, 'activa': True, 'titulo': 'Dress code'},
            'ITINERARIO': {'orden': 40, 'activa': True, 'titulo': 'Programa'},
            'ALBUM': {'orden': 50, 'activa': True},
            'MENU': {'orden': 60, 'activa': True},
            'REGALOS': {'orden': 70, 'activa': True},
            'ALBUM_COMPARTIDO': {'orden': 75, 'activa': True},
            'RSVP': {'orden': 80, 'activa': True},
        },
    },
    'CORPORATIVO': {
        'campos': {
            'tipo_evento': 'CORPORATIVO',
            'paleta_colores': 'AZUL',
            'paleta_sobre': 'AZUL',
            'estilo_letra': 'MODERNA',
            'etiqueta_principal': 'Evento',
            'etiqueta_secundario': 'Empresa',
            'mostrar_nombre_secundario': False,
            'mostrar_album': False,
            'mostrar_menu': True,
            'mostrar_regalos': False,
            'mostrar_mapa': True,
            'mostrar_album_compartido': False,
            'frase_portada': 'Evento Corporativo',
            'titulo_invitacion': 'Tenemos el gusto de invitarte',
            'texto_invitacion': 'Te compartimos los detalles para acompanar este encuentro profesional.',
            'titulo_cuenta_regresiva': 'Faltan',
            'titulo_detalles': 'Agenda y ubicacion',
            'texto_detalles': 'Consulta horarios, sede, accesos y detalles importantes del evento.',
            'titulo_album': 'Galeria',
            'titulo_menu': 'Menu',
            'titulo_regalos': 'Informacion adicional',
            'titulo_album_compartido': 'Material del evento',
            'texto_album_compartido': 'Accede al espacio compartido del evento cuando este disponible.',
            'titulo_rsvp': 'Confirma tu asistencia',
            'texto_rsvp': 'Tu confirmacion nos ayuda a preparar accesos, lugares y alimentos.',
        },
        'secciones': {
            'PORTADA': {'orden': 5, 'activa': True},
            'PADRES_PADRINOS': {'orden': 12, 'activa': False, 'titulo': 'Anfitriones'},
            'CUENTA_REGRESIVA': {'orden': 20, 'activa': True},
            'DETALLES': {'orden': 30, 'activa': True},
            'DRESS_CODE': {'orden': 35, 'activa': True, 'titulo': 'Codigo de vestimenta'},
            'ITINERARIO': {'orden': 40, 'activa': True, 'titulo': 'Agenda'},
            'ALBUM': {'orden': 50, 'activa': False},
            'MENU': {'orden': 60, 'activa': True},
            'REGALOS': {'orden': 70, 'activa': False},
            'ALBUM_COMPARTIDO': {'orden': 75, 'activa': False},
            'RSVP': {'orden': 80, 'activa': True},
        },
    },
}


def aplicar_plantilla_evento(evento, codigo):
    configuracion = CONFIGURACION_PLANTILLAS_EVENTO.get(codigo)
    if not configuracion:
        return

    for campo, valor in configuracion['campos'].items():
        setattr(evento, campo, valor)
    return

    plantillas = {
        'BODA': {
            'tipo_evento': 'BODA',
            'paleta_colores': 'TINTA_MARFIL',
            'paleta_sobre': 'TINTA_MARFIL',
            'estilo_letra': 'CURSIVA_ELEGANTE',
            'etiqueta_principal': 'Novia',
            'etiqueta_secundario': 'Novio',
            'frase_portada': 'Nuestra Boda',
            'titulo_detalles': 'Detalles de la celebración',
            'texto_detalles': 'Ceremonia, recepción, ubicación y dress code reunidos para acompañarnos sin complicaciones.',
            'titulo_regalos': 'Mesa de regalos',
            'titulo_rsvp': 'Confirma tu asistencia',
        },
        'XV': {
            'tipo_evento': 'XV',
            'paleta_colores': 'ROSA',
            'paleta_sobre': 'ROSA',
            'estilo_letra': 'ROMANTICA',
            'etiqueta_principal': 'Festejada',
            'etiqueta_secundario': 'Familia',
            'frase_portada': 'Mis XV años',
            'titulo_detalles': 'Detalles de la fiesta',
            'texto_detalles': 'Aquí encontrarás horarios, ubicación, dress code y todo lo necesario para celebrar juntos.',
            'titulo_regalos': 'Regalos',
            'titulo_rsvp': 'Confirma tu asistencia',
        },
        'BABY_SHOWER': {
            'tipo_evento': 'BABY_SHOWER',
            'paleta_colores': 'SALVIA_PERLA',
            'paleta_sobre': 'SALVIA_PERLA',
            'estilo_letra': 'MANUSCRITA',
            'etiqueta_principal': 'Bebé',
            'etiqueta_secundario': 'Familia',
            'frase_portada': 'Baby Shower',
            'titulo_detalles': 'Detalles del baby shower',
            'texto_detalles': 'Te compartimos horario, dirección, mesa de regalos y detalles para celebrar esta llegada especial.',
            'titulo_regalos': 'Mesa de regalos',
            'titulo_rsvp': 'Confirma tu asistencia',
        },
        'BAUTIZO': {
            'tipo_evento': 'BAUTIZO',
            'paleta_colores': 'DORADO',
            'paleta_sobre': 'DORADO',
            'estilo_letra': 'CLASICA',
            'etiqueta_principal': 'Bautizado',
            'etiqueta_secundario': 'Familia',
            'frase_portada': 'Mi Bautizo',
            'titulo_detalles': 'Ceremonia y celebración',
            'texto_detalles': 'Aquí tienes los horarios, ubicaciones y detalles para acompañarnos en este día especial.',
            'titulo_regalos': 'Detalles',
            'titulo_rsvp': 'Confirma tu asistencia',
        },
    }
    valores = plantillas.get(codigo)
    if not valores:
        return

    for campo, valor in valores.items():
        setattr(evento, campo, valor)


def aplicar_estructura_plantilla_evento(evento, codigo):
    configuracion = CONFIGURACION_PLANTILLAS_EVENTO.get(codigo)
    if not configuracion:
        return

    for tipo, ajustes in configuracion.get('secciones', {}).items():
        datos = datos_default_seccion(evento, tipo)
        defaults = {
            'titulo': ajustes.get('titulo', datos['titulo']),
            'descripcion': ajustes.get('descripcion', datos['descripcion']),
            'orden': ajustes.get('orden', datos['orden']),
            'activa': ajustes.get('activa', datos['activa']),
        }
        seccion, creada = SeccionInvitacion.objects.get_or_create(
            evento=evento,
            tipo=tipo,
            defaults=defaults,
        )
        if not creada:
            seccion.titulo = defaults['titulo']
            seccion.descripcion = defaults['descripcion']
            seccion.orden = defaults['orden']
            seccion.activa = defaults['activa']
            seccion.save(update_fields=['titulo', 'descripcion', 'orden', 'activa', 'fecha_actualizacion'])


def ajustar_acompanantes(adultos, ninos, limite):
    limite = max(limite, 0)
    total = adultos + ninos
    if total <= limite:
        return adultos, ninos

    exceso = total - limite
    ninos = max(ninos - exceso, 0)
    exceso = max(adultos + ninos - limite, 0)
    adultos = max(adultos - exceso, 0)
    return adultos, ninos


def bool_post(request, campo):
    return request.POST.get(campo) == 'on'


def limpiar_texto(request, campo):
    valor = request.POST.get(campo)
    return valor.strip() if valor else None


def convertir_hora(valor):
    if not valor:
        return None
    try:
        return datetime.strptime(valor, '%H:%M').time()
    except (TypeError, ValueError):
        return None


def convertir_decimal(valor, default=0):
    try:
        return Decimal(valor or default)
    except (InvalidOperation, TypeError, ValueError):
        return Decimal(default)


def archivo_pasa_validadores(modelo, campo, archivo):
    field = modelo._meta.get_field(campo)
    try:
        for validator in field.validators:
            validator(archivo)
    except ValidationError:
        return False
    return True


def guardar_campos_regalo(regalo, request):
    tipo = request.POST.get('tipo_regalo') or 'TIENDA'
    tiene_datos_bancarios = any(
        request.POST.get(campo)
        for campo in ['banco', 'titular', 'numero_cuenta', 'clabe']
    )
    if tiene_datos_bancarios and not request.POST.get('url_regalo'):
        tipo = 'DEPOSITO'

    regalo.tipo = tipo
    regalo.nombre = limpiar_texto(request, 'nombre_regalo') or ('Deposito bancario' if tipo == 'DEPOSITO' else 'Mesa de regalos')
    regalo.url = limpiar_texto(request, 'url_regalo')
    regalo.banco = limpiar_texto(request, 'banco')
    regalo.titular = limpiar_texto(request, 'titular')
    regalo.numero_cuenta = limpiar_texto(request, 'numero_cuenta')
    regalo.clabe = limpiar_texto(request, 'clabe')
    regalo.instrucciones = limpiar_texto(request, 'instrucciones')
    regalo.visible = bool_post(request, 'visible')
    regalo.save()


def agregar_persona_ceremonia_dashboard(request, evento):
    nombre = limpiar_texto(request, 'nombre_persona')
    if not nombre:
        return 'operacion'

    PersonaCeremonia.objects.create(
        evento=evento,
        seccion=request.POST.get('seccion_persona') or 'PADRINOS',
        etiqueta=limpiar_texto(request, 'etiqueta_persona') or 'Nombre',
        nombre=nombre,
        orden=convertir_entero(request.POST.get('orden_persona'), 0),
        visible=bool_post(request, 'visible_persona'),
    )
    return 'operacion'


def editar_persona_ceremonia_dashboard(request, evento):
    persona = get_object_or_404(PersonaCeremonia, id=request.POST.get('persona_id'), evento=evento)
    persona.seccion = request.POST.get('seccion_persona') or persona.seccion
    persona.etiqueta = limpiar_texto(request, 'etiqueta_persona') or persona.etiqueta
    persona.nombre = limpiar_texto(request, 'nombre_persona') or persona.nombre
    persona.orden = convertir_entero(request.POST.get('orden_persona'), persona.orden)
    persona.visible = bool_post(request, 'visible_persona')
    persona.save()
    return 'operacion'


def eliminar_persona_ceremonia_dashboard(request, evento):
    persona = get_object_or_404(PersonaCeremonia, id=request.POST.get('persona_id'), evento=evento)
    persona.delete()
    return 'operacion'


def editar_regalo_dashboard(request, evento):
    regalo = get_object_or_404(EnlaceRegalo, id=request.POST.get('regalo_id'), evento=evento)
    guardar_campos_regalo(regalo, request)
    return 'operacion'


def eliminar_regalo_dashboard(request, evento):
    regalo = get_object_or_404(EnlaceRegalo, id=request.POST.get('regalo_id'), evento=evento)
    regalo.delete()
    return 'operacion'


def editar_album_dashboard(request, evento):
    foto = get_object_or_404(FotoEvento, id=request.POST.get('foto_id'), evento=evento)
    foto.titulo = limpiar_texto(request, 'titulo_album_media')
    foto.orden = convertir_entero(request.POST.get('orden_album_media'), foto.orden)
    foto.visible = bool_post(request, 'visible_album_media')
    archivo = request.FILES.get('archivo_album')
    if archivo and archivo_pasa_validadores(FotoEvento, 'imagen', archivo):
        if foto.imagen:
            foto.imagen.delete(save=False)
        foto.imagen = archivo
    foto.save()
    return 'contenido'


def eliminar_album_dashboard(request, evento):
    foto = get_object_or_404(FotoEvento, id=request.POST.get('foto_id'), evento=evento)
    if foto.imagen:
        foto.imagen.delete(save=False)
    foto.delete()
    return 'contenido'


def proveedor_empresa_para_evento(evento, proveedor_id):
    if not proveedor_id:
        return None
    filtros = {'id': proveedor_id, 'activo': True}
    if evento.empresa:
        filtros['empresa'] = evento.empresa
    return Proveedor.objects.filter(**filtros).first()


def usuarios_empresa_para_evento(evento):
    if not evento.empresa:
        return get_user_model().objects.none()
    return get_user_model().objects.filter(
        membresias_empresa__empresa=evento.empresa,
        membresias_empresa__activo=True,
    ).distinct()


def categoria_gasto_dashboard(request):
    categoria_id = request.POST.get('categoria_gasto_id')
    nombre = limpiar_texto(request, 'categoria_gasto_nombre')
    if categoria_id:
        categoria = CategoriaGasto.objects.filter(id=categoria_id, activo=True).first()
        if categoria:
            return categoria
    if nombre:
        categoria, _ = CategoriaGasto.objects.get_or_create(nombre=nombre, defaults={'activo': True})
        return categoria
    categoria, _ = CategoriaGasto.objects.get_or_create(nombre='General', defaults={'activo': True})
    return categoria


def guardar_campos_servicio_evento(servicio, request, evento):
    estados_validos = {valor for valor, _ in ServicioEvento.ESTADOS}
    servicio.proveedor = proveedor_empresa_para_evento(evento, request.POST.get('proveedor_id'))
    servicio.nombre_servicio = limpiar_texto(request, 'nombre_servicio') or servicio.nombre_servicio or 'Servicio'
    servicio.descripcion = limpiar_texto(request, 'descripcion_servicio')
    servicio.fecha_servicio = fecha_dashboard(request, 'fecha_servicio', servicio.fecha_servicio)
    servicio.hora_inicio = hora_dashboard(request, 'hora_inicio_servicio', servicio.hora_inicio)
    servicio.hora_fin = hora_dashboard(request, 'hora_fin_servicio', servicio.hora_fin)
    servicio.lugar = limpiar_texto(request, 'lugar_servicio')
    servicio.costo_total = convertir_decimal(request.POST.get('costo_total_servicio'), servicio.costo_total)
    servicio.anticipo = convertir_decimal(request.POST.get('anticipo_servicio'), servicio.anticipo)
    servicio.fecha_limite_pago = fecha_dashboard(request, 'fecha_limite_pago_servicio', servicio.fecha_limite_pago)
    estado = request.POST.get('estado_servicio')
    if estado in estados_validos:
        servicio.estado = estado
    servicio.notas = limpiar_texto(request, 'notas_servicio')
    for campo in ('contrato', 'cotizacion', 'comprobante_pago'):
        if request.POST.get(f'eliminar_{campo}_servicio') == 'on':
            archivo_actual = getattr(servicio, campo, None)
            if archivo_actual:
                archivo_actual.delete(save=False)
            setattr(servicio, campo, None)
        archivo = request.FILES.get(f'{campo}_servicio')
        if archivo and archivo_pasa_validadores(ServicioEvento, campo, archivo):
            archivo_actual = getattr(servicio, campo, None)
            if archivo_actual:
                archivo_actual.delete(save=False)
            setattr(servicio, campo, archivo)
    servicio.save()
    return servicio


def agregar_servicio_evento_dashboard(request, evento):
    servicio = ServicioEvento(evento=evento, nombre_servicio='Servicio')
    guardar_campos_servicio_evento(servicio, request, evento)
    return 'operacion'


def editar_servicio_evento_dashboard(request, evento):
    servicio = get_object_or_404(ServicioEvento, evento=evento, id=request.POST.get('servicio_id'))
    guardar_campos_servicio_evento(servicio, request, evento)
    return 'operacion'


def eliminar_servicio_evento_dashboard(request, evento):
    servicio = get_object_or_404(ServicioEvento, evento=evento, id=request.POST.get('servicio_id'))
    servicio.delete()
    return 'operacion'


def paquete_empresa_para_evento(evento, paquete_id):
    if not paquete_id:
        return None
    filtros = {'id': paquete_id, 'activo': True}
    if evento.empresa:
        filtros['empresa'] = evento.empresa
    return PaqueteBoda.objects.filter(**filtros).first()


def guardar_campos_paquete_evento(paquete_evento, request, evento):
    paquete = paquete_empresa_para_evento(evento, request.POST.get('paquete_id'))
    if paquete:
        paquete_evento.paquete = paquete
    estados_validos = {valor for valor, _ in PaqueteEvento.ESTADOS}
    paquete_evento.precio_acordado = convertir_decimal(request.POST.get('precio_acordado_paquete'), paquete_evento.precio_acordado)
    paquete_evento.descuento = convertir_decimal(request.POST.get('descuento_paquete'), paquete_evento.descuento)
    total_manual = request.POST.get('total_paquete')
    if total_manual:
        paquete_evento.total = convertir_decimal(total_manual, paquete_evento.total)
    else:
        base = paquete_evento.precio_acordado or paquete_evento.paquete.precio_base
        paquete_evento.total = max(base - paquete_evento.descuento, Decimal('0'))
    if request.POST.get('estado_paquete') in estados_validos:
        paquete_evento.estado = request.POST.get('estado_paquete')
    paquete_evento.servicios_adicionales = limpiar_texto(request, 'servicios_adicionales_paquete')
    paquete_evento.notas = limpiar_texto(request, 'notas_paquete')
    paquete_evento.save()
    return paquete_evento


def agregar_paquete_evento_dashboard(request, evento):
    paquete = paquete_empresa_para_evento(evento, request.POST.get('paquete_id'))
    if not paquete:
        return 'operacion'
    paquete_evento = PaqueteEvento(evento=evento, paquete=paquete)
    guardar_campos_paquete_evento(paquete_evento, request, evento)
    return 'operacion'


def editar_paquete_evento_dashboard(request, evento):
    paquete_evento = get_object_or_404(PaqueteEvento, evento=evento, id=request.POST.get('paquete_evento_id'))
    guardar_campos_paquete_evento(paquete_evento, request, evento)
    return 'operacion'


def eliminar_paquete_evento_dashboard(request, evento):
    paquete_evento = get_object_or_404(PaqueteEvento, evento=evento, id=request.POST.get('paquete_evento_id'))
    paquete_evento.delete()
    return 'operacion'


def guardar_campos_personal_evento(personal, request, evento):
    tipos_validos = {valor for valor, _ in PersonalEvento.TIPOS}
    estados_validos = {valor for valor, _ in PersonalEvento.ESTADOS}
    personal.proveedor = proveedor_empresa_para_evento(evento, request.POST.get('proveedor_id'))
    personal.nombre = limpiar_texto(request, 'nombre_personal') or personal.nombre or 'Personal'
    if request.POST.get('tipo_personal') in tipos_validos:
        personal.tipo_personal = request.POST.get('tipo_personal')
    personal.telefono = limpiar_texto(request, 'telefono_personal')
    personal.hora_entrada = hora_dashboard(request, 'hora_entrada_personal', personal.hora_entrada)
    personal.hora_salida = hora_dashboard(request, 'hora_salida_personal', personal.hora_salida)
    personal.area_asignada = limpiar_texto(request, 'area_personal')
    personal.mesas_asignadas = limpiar_texto(request, 'mesas_personal')
    personal.costo = convertir_decimal(request.POST.get('costo_personal'), personal.costo)
    personal.uniforme = limpiar_texto(request, 'uniforme_personal')
    if request.POST.get('estado_personal') in estados_validos:
        personal.estado = request.POST.get('estado_personal')
    personal.notas = limpiar_texto(request, 'notas_personal')
    personal.save()
    return personal


def agregar_personal_evento_dashboard(request, evento):
    personal = PersonalEvento(evento=evento, nombre='Personal')
    guardar_campos_personal_evento(personal, request, evento)
    return 'operacion'


def editar_personal_evento_dashboard(request, evento):
    personal = get_object_or_404(PersonalEvento, evento=evento, id=request.POST.get('personal_id'))
    guardar_campos_personal_evento(personal, request, evento)
    return 'operacion'


def eliminar_personal_evento_dashboard(request, evento):
    personal = get_object_or_404(PersonalEvento, evento=evento, id=request.POST.get('personal_id'))
    personal.delete()
    return 'operacion'


def paquete_buffet_para_evento(evento, paquete_id):
    if not paquete_id:
        return None
    queryset = PaqueteBuffet.objects.filter(id=paquete_id, activo=True)
    if evento.empresa:
        queryset = queryset.filter(proveedor__empresa=evento.empresa)
    return queryset.first()


def guardar_campos_catering_evento(catering, request, evento):
    catering.proveedor = proveedor_empresa_para_evento(evento, request.POST.get('proveedor_id'))
    catering.paquete_buffet = paquete_buffet_para_evento(evento, request.POST.get('paquete_buffet_id'))
    catering.cantidad_adultos = convertir_entero(request.POST.get('cantidad_adultos_catering'), catering.cantidad_adultos)
    catering.cantidad_ninos = convertir_entero(request.POST.get('cantidad_ninos_catering'), catering.cantidad_ninos)
    catering.cantidad_proveedores = convertir_entero(request.POST.get('cantidad_proveedores_catering'), catering.cantidad_proveedores)
    catering.precio_total = convertir_decimal(request.POST.get('precio_total_catering'), catering.precio_total)
    catering.fecha_degustacion = fecha_dashboard(request, 'fecha_degustacion_catering', catering.fecha_degustacion)
    catering.hora_servicio = hora_dashboard(request, 'hora_servicio_catering', catering.hora_servicio)
    catering.horario_montaje = hora_dashboard(request, 'horario_montaje_catering', catering.horario_montaje)
    catering.duracion_servicio = limpiar_texto(request, 'duracion_servicio_catering')
    catering.observaciones = limpiar_texto(request, 'observaciones_catering')
    catering.save()
    alimentos_ids = request.POST.getlist('alimentos_catering')
    if alimentos_ids:
        catering.alimentos_seleccionados.set(Alimento.objects.filter(id__in=alimentos_ids, activo=True))
    elif 'alimentos_catering' in request.POST:
        catering.alimentos_seleccionados.clear()
    return catering


def agregar_catering_evento_dashboard(request, evento):
    catering = CateringEvento(evento=evento)
    guardar_campos_catering_evento(catering, request, evento)
    return 'operacion'


def editar_catering_evento_dashboard(request, evento):
    catering = get_object_or_404(CateringEvento, evento=evento, id=request.POST.get('catering_id'))
    guardar_campos_catering_evento(catering, request, evento)
    return 'operacion'


def eliminar_catering_evento_dashboard(request, evento):
    catering = get_object_or_404(CateringEvento, evento=evento, id=request.POST.get('catering_id'))
    catering.delete()
    return 'operacion'


def guardar_campos_decoracion_evento(elemento, request, evento):
    categorias_validas = {valor for valor, _ in ElementoDecoracion.CATEGORIAS}
    estados_validos = {valor for valor, _ in ElementoDecoracion.ESTADOS}
    if request.POST.get('categoria_decoracion') in categorias_validas:
        elemento.categoria = request.POST.get('categoria_decoracion')
    elemento.nombre = limpiar_texto(request, 'nombre_decoracion') or elemento.nombre or 'Elemento'
    elemento.descripcion = limpiar_texto(request, 'descripcion_decoracion')
    elemento.cantidad = max(convertir_entero(request.POST.get('cantidad_decoracion'), elemento.cantidad), 1)
    elemento.color = limpiar_texto(request, 'color_decoracion')
    elemento.material = limpiar_texto(request, 'material_decoracion')
    elemento.proveedor = proveedor_empresa_para_evento(evento, request.POST.get('proveedor_id'))
    elemento.costo = convertir_decimal(request.POST.get('costo_decoracion'), elemento.costo)
    elemento.aprobado_cliente = bool_post(request, 'aprobado_cliente_decoracion')
    if request.POST.get('estado_decoracion') in estados_validos:
        elemento.estado = request.POST.get('estado_decoracion')
    elemento.notas = limpiar_texto(request, 'notas_decoracion')
    for campo in ('imagen_referencia', 'imagen_final'):
        if request.POST.get(f'eliminar_{campo}_decoracion') == 'on':
            archivo_actual = getattr(elemento, campo, None)
            if archivo_actual:
                archivo_actual.delete(save=False)
            setattr(elemento, campo, None)
        archivo = request.FILES.get(f'{campo}_decoracion')
        if archivo and archivo_pasa_validadores(ElementoDecoracion, campo, archivo):
            archivo_actual = getattr(elemento, campo, None)
            if archivo_actual:
                archivo_actual.delete(save=False)
            setattr(elemento, campo, archivo)
    elemento.save()
    return elemento


def agregar_decoracion_evento_dashboard(request, evento):
    elemento = ElementoDecoracion(evento=evento, nombre='Elemento')
    guardar_campos_decoracion_evento(elemento, request, evento)
    return 'operacion'


def editar_decoracion_evento_dashboard(request, evento):
    elemento = get_object_or_404(ElementoDecoracion, evento=evento, id=request.POST.get('decoracion_id'))
    guardar_campos_decoracion_evento(elemento, request, evento)
    return 'operacion'


def eliminar_decoracion_evento_dashboard(request, evento):
    elemento = get_object_or_404(ElementoDecoracion, evento=evento, id=request.POST.get('decoracion_id'))
    if elemento.imagen_referencia:
        elemento.imagen_referencia.delete(save=False)
    if elemento.imagen_final:
        elemento.imagen_final.delete(save=False)
    elemento.delete()
    return 'operacion'


def guardar_campos_entretenimiento_evento(entretenimiento, request, evento):
    tipos_validos = {valor for valor, _ in EntretenimientoEvento.TIPOS}
    estados_validos = {valor for valor, _ in EntretenimientoEvento.ESTADOS}
    if request.POST.get('tipo_entretenimiento') in tipos_validos:
        entretenimiento.tipo = request.POST.get('tipo_entretenimiento')
    entretenimiento.proveedor = proveedor_empresa_para_evento(evento, request.POST.get('proveedor_id'))
    entretenimiento.nombre_artista = limpiar_texto(request, 'nombre_artista') or entretenimiento.nombre_artista or 'Artista'
    entretenimiento.hora_inicio = hora_dashboard(request, 'hora_inicio_entretenimiento', entretenimiento.hora_inicio)
    entretenimiento.hora_fin = hora_dashboard(request, 'hora_fin_entretenimiento', entretenimiento.hora_fin)
    entretenimiento.duracion = limpiar_texto(request, 'duracion_entretenimiento')
    entretenimiento.costo = convertir_decimal(request.POST.get('costo_entretenimiento'), entretenimiento.costo)
    entretenimiento.anticipo = convertir_decimal(request.POST.get('anticipo_entretenimiento'), entretenimiento.anticipo)
    entretenimiento.requerimientos_tecnicos = limpiar_texto(request, 'requerimientos_entretenimiento')
    if request.POST.get('estado_entretenimiento') in estados_validos:
        entretenimiento.estado = request.POST.get('estado_entretenimiento')
    entretenimiento.notas = limpiar_texto(request, 'notas_entretenimiento')
    entretenimiento.save()
    return entretenimiento


def agregar_entretenimiento_evento_dashboard(request, evento):
    entretenimiento = EntretenimientoEvento(evento=evento, nombre_artista='Artista')
    guardar_campos_entretenimiento_evento(entretenimiento, request, evento)
    return 'operacion'


def editar_entretenimiento_evento_dashboard(request, evento):
    entretenimiento = get_object_or_404(EntretenimientoEvento, evento=evento, id=request.POST.get('entretenimiento_id'))
    guardar_campos_entretenimiento_evento(entretenimiento, request, evento)
    return 'operacion'


def eliminar_entretenimiento_evento_dashboard(request, evento):
    entretenimiento = get_object_or_404(EntretenimientoEvento, evento=evento, id=request.POST.get('entretenimiento_id'))
    entretenimiento.delete()
    return 'operacion'


def entretenimiento_para_cancion(evento, entretenimiento_id):
    if not entretenimiento_id:
        return None
    return EntretenimientoEvento.objects.filter(evento=evento, id=entretenimiento_id).first()


def guardar_campos_cancion_evento(cancion, request, evento):
    momentos_validos = {valor for valor, _ in CancionEvento.TIPOS_MOMENTO}
    cancion.entretenimiento = entretenimiento_para_cancion(evento, request.POST.get('entretenimiento_id'))
    if request.POST.get('tipo_momento') in momentos_validos:
        cancion.tipo_momento = request.POST.get('tipo_momento')
    cancion.nombre_cancion = limpiar_texto(request, 'nombre_cancion') or cancion.nombre_cancion or 'Cancion'
    cancion.artista = limpiar_texto(request, 'artista_cancion')
    cancion.enlace = limpiar_texto(request, 'enlace_cancion')
    cancion.orden = convertir_entero(request.POST.get('orden_cancion'), cancion.orden)
    cancion.notas = limpiar_texto(request, 'notas_cancion')
    cancion.save()
    return cancion


def agregar_cancion_evento_dashboard(request, evento):
    cancion = CancionEvento(evento=evento, nombre_cancion='Cancion')
    guardar_campos_cancion_evento(cancion, request, evento)
    return 'operacion'


def editar_cancion_evento_dashboard(request, evento):
    cancion = get_object_or_404(CancionEvento, evento=evento, id=request.POST.get('cancion_id'))
    guardar_campos_cancion_evento(cancion, request, evento)
    return 'operacion'


def eliminar_cancion_evento_dashboard(request, evento):
    cancion = get_object_or_404(CancionEvento, evento=evento, id=request.POST.get('cancion_id'))
    cancion.delete()
    return 'operacion'


def guardar_campos_tarea_evento(tarea, request, evento):
    estados_validos = {valor for valor, _ in TareaEvento.ESTADOS}
    prioridades_validas = {valor for valor, _ in TareaEvento.PRIORIDADES}
    categorias_validas = {valor for valor, _ in TareaEvento.CATEGORIAS}
    tarea.titulo = limpiar_texto(request, 'titulo_tarea') or tarea.titulo or 'Tarea'
    tarea.descripcion = limpiar_texto(request, 'descripcion_tarea')
    responsable_id = request.POST.get('responsable_id')
    tarea.responsable = usuarios_empresa_para_evento(evento).filter(id=responsable_id).first() if responsable_id else None
    tarea.fecha_inicio = fecha_dashboard(request, 'fecha_inicio_tarea', tarea.fecha_inicio)
    tarea.fecha_limite = fecha_dashboard(request, 'fecha_limite_tarea', tarea.fecha_limite)
    if request.POST.get('prioridad_tarea') in prioridades_validas:
        tarea.prioridad = request.POST.get('prioridad_tarea')
    if request.POST.get('estado_tarea') in estados_validos:
        tarea.estado = request.POST.get('estado_tarea')
    if request.POST.get('categoria_tarea') in categorias_validas:
        tarea.categoria = request.POST.get('categoria_tarea')
    tarea.porcentaje_avance = min(convertir_entero(request.POST.get('porcentaje_avance_tarea'), tarea.porcentaje_avance), 100)
    tarea.notas = limpiar_texto(request, 'notas_tarea')
    if request.POST.get('eliminar_evidencia_tarea') == 'on' and tarea.evidencia:
        tarea.evidencia.delete(save=False)
        tarea.evidencia = None
    evidencia = request.FILES.get('evidencia_tarea')
    if evidencia and archivo_pasa_validadores(TareaEvento, 'evidencia', evidencia):
        if tarea.evidencia:
            tarea.evidencia.delete(save=False)
        tarea.evidencia = evidencia
    tarea.save()
    return tarea


def agregar_tarea_evento_dashboard(request, evento):
    tarea = TareaEvento(evento=evento, titulo='Tarea')
    guardar_campos_tarea_evento(tarea, request, evento)
    return 'operacion'


def editar_tarea_evento_dashboard(request, evento):
    tarea = get_object_or_404(TareaEvento, evento=evento, id=request.POST.get('tarea_id'))
    guardar_campos_tarea_evento(tarea, request, evento)
    return 'operacion'


def eliminar_tarea_evento_dashboard(request, evento):
    tarea = get_object_or_404(TareaEvento, evento=evento, id=request.POST.get('tarea_id'))
    tarea.delete()
    return 'operacion'


def guardar_campos_gasto_evento(gasto, request, evento):
    estados_validos = {valor for valor, _ in GastoEvento.ESTADOS}
    gasto.categoria = categoria_gasto_dashboard(request)
    gasto.proveedor = proveedor_empresa_para_evento(evento, request.POST.get('proveedor_id'))
    gasto.concepto = limpiar_texto(request, 'concepto_gasto') or gasto.concepto or 'Gasto'
    gasto.monto_estimado = convertir_decimal(request.POST.get('monto_estimado_gasto'), gasto.monto_estimado)
    gasto.monto_real = convertir_decimal(request.POST.get('monto_real_gasto'), gasto.monto_real)
    gasto.fecha_limite = fecha_dashboard(request, 'fecha_limite_gasto', gasto.fecha_limite)
    if request.POST.get('estado_gasto') in estados_validos:
        gasto.estado = request.POST.get('estado_gasto')
    gasto.notas = limpiar_texto(request, 'notas_gasto')
    gasto.save()
    return gasto


def agregar_gasto_evento_dashboard(request, evento):
    gasto = GastoEvento(evento=evento, categoria=categoria_gasto_dashboard(request), concepto='Gasto')
    guardar_campos_gasto_evento(gasto, request, evento)
    return 'operacion'


def editar_gasto_evento_dashboard(request, evento):
    gasto = get_object_or_404(GastoEvento, evento=evento, id=request.POST.get('gasto_id'))
    guardar_campos_gasto_evento(gasto, request, evento)
    return 'operacion'


def eliminar_gasto_evento_dashboard(request, evento):
    gasto = get_object_or_404(GastoEvento, evento=evento, id=request.POST.get('gasto_id'))
    gasto.delete()
    return 'operacion'


def guardar_campos_pago_evento(pago, request):
    metodos_validos = {valor for valor, _ in PagoEvento.METODOS}
    pago.monto = convertir_decimal(request.POST.get('monto_pago'), pago.monto)
    pago.fecha_pago = fecha_dashboard(request, 'fecha_pago', pago.fecha_pago)
    if request.POST.get('metodo_pago') in metodos_validos:
        pago.metodo_pago = request.POST.get('metodo_pago')
    pago.referencia = limpiar_texto(request, 'referencia_pago')
    pago.notas = limpiar_texto(request, 'notas_pago')
    if request.POST.get('eliminar_comprobante_pago') == 'on' and pago.comprobante:
        pago.comprobante.delete(save=False)
        pago.comprobante = None
    comprobante = request.FILES.get('comprobante_pago')
    if comprobante and archivo_pasa_validadores(PagoEvento, 'comprobante', comprobante):
        if pago.comprobante:
            pago.comprobante.delete(save=False)
        pago.comprobante = comprobante
    pago.save()
    return pago


def agregar_pago_evento_dashboard(request, evento):
    gasto = get_object_or_404(GastoEvento, evento=evento, id=request.POST.get('gasto_id'))
    pago = PagoEvento(gasto=gasto, monto=0)
    guardar_campos_pago_evento(pago, request)
    return 'operacion'


def editar_pago_evento_dashboard(request, evento):
    pago = get_object_or_404(PagoEvento, gasto__evento=evento, id=request.POST.get('pago_id'))
    guardar_campos_pago_evento(pago, request)
    return 'operacion'


def eliminar_pago_evento_dashboard(request, evento):
    pago = get_object_or_404(PagoEvento, gasto__evento=evento, id=request.POST.get('pago_id'))
    pago.delete()
    return 'operacion'


def guardar_campos_documento_evento(documento, request, evento):
    tipos_validos = {valor for valor, _ in DocumentoEvento.TIPOS}
    if request.POST.get('tipo_documento') in tipos_validos:
        documento.tipo_documento = request.POST.get('tipo_documento')
    documento.titulo = limpiar_texto(request, 'titulo_documento') or documento.titulo or 'Documento'
    documento.descripcion = limpiar_texto(request, 'descripcion_documento')
    documento.proveedor = proveedor_empresa_para_evento(evento, request.POST.get('proveedor_id'))
    documento.visible_cliente = bool_post(request, 'visible_cliente_documento')
    archivo = request.FILES.get('archivo_documento')
    if archivo and archivo_pasa_validadores(DocumentoEvento, 'archivo', archivo):
        if documento.archivo:
            documento.archivo.delete(save=False)
        documento.archivo = archivo
    documento.save()
    return documento


def agregar_documento_evento_dashboard(request, evento):
    archivo = request.FILES.get('archivo_documento')
    if not archivo or not archivo_pasa_validadores(DocumentoEvento, 'archivo', archivo):
        return 'operacion'
    documento = DocumentoEvento(evento=evento, titulo='Documento', cargado_por=request.user)
    guardar_campos_documento_evento(documento, request, evento)
    return 'operacion'


def editar_documento_evento_dashboard(request, evento):
    documento = get_object_or_404(DocumentoEvento, evento=evento, id=request.POST.get('documento_id'))
    guardar_campos_documento_evento(documento, request, evento)
    return 'operacion'


def eliminar_documento_evento_dashboard(request, evento):
    documento = get_object_or_404(DocumentoEvento, evento=evento, id=request.POST.get('documento_id'))
    if documento.archivo:
        documento.archivo.delete(save=False)
    documento.delete()
    return 'operacion'


def guardar_campos_aprobacion_evento(aprobacion, request):
    tipos_validos = {valor for valor, _ in AprobacionEvento.TIPOS}
    estados_validos = {valor for valor, _ in AprobacionEvento.ESTADOS}
    if request.POST.get('tipo_aprobacion') in tipos_validos:
        aprobacion.tipo = request.POST.get('tipo_aprobacion')
    aprobacion.titulo = limpiar_texto(request, 'titulo_aprobacion') or aprobacion.titulo or 'Aprobacion'
    aprobacion.descripcion = limpiar_texto(request, 'descripcion_aprobacion')
    if request.POST.get('estado_aprobacion') in estados_validos:
        aprobacion.estado = request.POST.get('estado_aprobacion')
    aprobacion.comentario = limpiar_texto(request, 'comentario_aprobacion')
    aprobacion.save()
    return aprobacion


def agregar_aprobacion_evento_dashboard(request, evento):
    aprobacion = AprobacionEvento(evento=evento, tipo='OTRO', titulo='Aprobacion', solicitado_por=request.user)
    guardar_campos_aprobacion_evento(aprobacion, request)
    return 'operacion'


def editar_aprobacion_evento_dashboard(request, evento):
    aprobacion = get_object_or_404(AprobacionEvento, evento=evento, id=request.POST.get('aprobacion_id'))
    guardar_campos_aprobacion_evento(aprobacion, request)
    return 'operacion'


def eliminar_aprobacion_evento_dashboard(request, evento):
    aprobacion = get_object_or_404(AprobacionEvento, evento=evento, id=request.POST.get('aprobacion_id'))
    aprobacion.delete()
    return 'operacion'


def sincronizar_menus_desde_detalle_produccion(evento, detalle):
    menus = [
        ('Entrada', detalle.menu_entrada, 'ADULTO'),
        ('Plato fuerte', detalle.menu_plato_fuerte, 'ADULTO'),
        ('Postre', detalle.menu_postre, 'ADULTO'),
        ('Trasnochado', detalle.menu_trasnochado, 'GENERAL'),
        ('Menu infantil', detalle.menu_infantil, 'NINO'),
    ]
    for nombre, descripcion, tipo in menus:
        if not descripcion:
            continue
        MenuBoda.objects.update_or_create(
            evento=evento,
            nombre=nombre,
            defaults={
                'descripcion': descripcion,
                'tipo': tipo,
                'visible': True,
            },
        )


def guardar_detalle_produccion_dashboard(request, evento):
    detalle, _ = DetalleProduccionEvento.objects.get_or_create(evento=evento)
    campos_texto = [
        'folio_contrato',
        'cliente_contrato',
        'arrendador',
        'lugar_contrato',
        'banco',
        'numero_cuenta',
        'clabe',
        'tarjeta',
        'color_mantel',
        'color_servilleta',
        'tipo_mesa',
        'tamano_mesa',
        'mobiliario',
        'tipo_loza_cristaleria',
        'diseno_carpa',
        'tamano_carpa',
        'color_carpa',
        'montaje_carpa',
        'menu_entrada',
        'menu_plato_fuerte',
        'menu_postre',
        'menu_trasnochado',
        'menu_infantil',
        'bebidas',
        'servicios_incluidos',
        'notas_puntualidad',
        'politica_cancelacion',
        'notas_contrato',
    ]
    campos_enteros = [
        'adultos_contratados',
        'ninos_contratados',
        'horas_evento',
        'minutos_desalojo',
        'dias_antes_liquidacion',
    ]
    campos_decimal = [
        'costo_hora_extra',
        'precio_renta_salon',
        'deposito_apartado',
        'anticipo_recibido',
        'saldo_contrato',
    ]
    campos_hora = ['recepcion_hora', 'inicio_evento', 'fin_evento']

    for campo in campos_texto:
        if campo in request.POST:
            setattr(detalle, campo, limpiar_texto(request, campo))
    for campo in campos_enteros:
        if campo in request.POST:
            setattr(detalle, campo, convertir_entero(request.POST.get(campo), getattr(detalle, campo)))
    for campo in campos_decimal:
        if campo in request.POST:
            setattr(detalle, campo, convertir_decimal(request.POST.get(campo), getattr(detalle, campo)))
    for campo in campos_hora:
        if campo in request.POST:
            setattr(detalle, campo, convertir_hora(request.POST.get(campo)))

    detalle.save()
    sincronizar_menus_desde_detalle_produccion(evento, detalle)

    evento.capacidad_contratada = max(detalle.total_personas_contratadas, evento.capacidad_contratada)
    if detalle.inicio_evento:
        evento.hora_inicio = detalle.inicio_evento
    if detalle.fin_evento:
        evento.hora_fin = detalle.fin_evento
    if detalle.precio_renta_salon:
        evento.presupuesto_total = detalle.precio_renta_salon
    if detalle.anticipo_recibido:
        evento.monto_pagado = detalle.anticipo_recibido
    evento.save(update_fields=['capacidad_contratada', 'hora_inicio', 'hora_fin', 'presupuesto_total', 'monto_pagado'])
    return 'operacion'


def valor_pendiente(valor):
    texto = (valor or '').strip().lower()
    return not texto or 'por definir' in texto or 'pendiente' in texto or 'detallar' in texto


def fecha_limite_operativa(evento, dias_antes=30):
    if not evento or not evento.fecha_fiesta:
        return None
    return (evento.fecha_fiesta - timedelta(days=dias_antes)).date()


def crear_tarea_pendiente_contrato(evento, titulo, descripcion, categoria='GENERAL', dias_antes=30):
    tarea, creada = TareaEvento.objects.get_or_create(
        evento=evento,
        titulo=titulo,
        defaults={
            'descripcion': descripcion,
            'categoria': categoria,
            'prioridad': 'ALTA',
            'estado': 'PENDIENTE',
            'fecha_limite': fecha_limite_operativa(evento, dias_antes),
        },
    )
    if not creada and tarea.estado == 'CANCELADA':
        tarea.estado = 'PENDIENTE'
        tarea.descripcion = descripcion
        tarea.categoria = categoria
        tarea.prioridad = 'ALTA'
        tarea.fecha_limite = fecha_limite_operativa(evento, dias_antes)
        tarea.save(update_fields=['estado', 'descripcion', 'categoria', 'prioridad', 'fecha_limite'])
    return tarea


def generar_pendientes_contrato_dashboard(request, evento):
    detalle = DetalleProduccionEvento.objects.filter(evento=evento).first()
    if not detalle:
        return 'operacion'

    pendientes = [
        (
            valor_pendiente(detalle.color_mantel) or valor_pendiente(detalle.color_servilleta),
            'Definir colores de manteleria',
            'Confirmar color de mantel y color de servilleta con el cliente.',
            'DECORACION',
            45,
        ),
        (
            valor_pendiente(detalle.tipo_mesa) or valor_pendiente(detalle.tamano_mesa),
            'Definir tipo y tamano de mesas',
            'Cerrar tipo de mesa, tamano y distribucion base para el layout del evento.',
            'MESAS',
            45,
        ),
        (
            valor_pendiente(detalle.diseno_carpa) or valor_pendiente(detalle.tamano_carpa) or valor_pendiente(detalle.color_carpa),
            'Definir carpa del jardin',
            'Confirmar diseno, tamano, color y ubicacion de la carpa en el montaje.',
            'DECORACION',
            45,
        ),
        (
            valor_pendiente(detalle.menu_entrada) or valor_pendiente(detalle.menu_plato_fuerte),
            'Cerrar entrada y plato fuerte',
            'Definir entrada y comida/plato fuerte final del banquete adulto.',
            'CATERING',
            35,
        ),
        (
            valor_pendiente(detalle.menu_postre),
            'Cerrar postre o mesa de postres',
            'Definir composicion final de postre o mesa de postres.',
            'CATERING',
            35,
        ),
        (
            valor_pendiente(detalle.menu_trasnochado),
            'Cerrar trasnochado',
            'Confirmar tipo, horario y porciones del trasnochado.',
            'CATERING',
            35,
        ),
        (
            valor_pendiente(detalle.notas_puntualidad),
            'Confirmar puntualidad de musica',
            'Asegurar llegada puntual de musica/DJ; el contrato indica que no se repone tiempo por retrasos.',
            'MUSICA',
            20,
        ),
    ]

    for condicion, titulo, descripcion, categoria, dias_antes in pendientes:
        if condicion:
            crear_tarea_pendiente_contrato(evento, titulo, descripcion, categoria, dias_antes)
    return 'operacion'


def agregar_grupo_dashboard(request, evento):
    nombre = limpiar_texto(request, 'nombre_grupo')
    tipo = request.POST.get('tipo_grupo') or 'PERSONAL'
    destino = request.POST.get('destino') if request.POST.get('destino') in {'personalizacion', 'invitados'} else 'invitados'
    if not nombre:
        return destino

    grupo = Grupoinvitacion.objects.create(
        evento=evento,
        nombre_grupo=nombre,
        tipo=tipo,
        cantidad_extra_permitida=convertir_entero(request.POST.get('cantidad_extra_permitida'), 0),
        cantidad_maxima=max(convertir_entero(request.POST.get('cantidad_maxima'), 1), 1),
        telefono_contacto=limpiar_texto(request, 'telefono_contacto'),
        correo_contacto=limpiar_texto(request, 'correo_contacto'),
        mesa=limpiar_texto(request, 'mesa'),
    )
    if grupo.es_familiar:
        crear_invitados_desde_textarea(grupo, request.POST.get('invitados_familia', ''))
    return destino


def editar_grupo_dashboard(request, evento):
    grupo = get_object_or_404(Grupoinvitacion, id=request.POST.get('grupo_id'), evento=evento)
    grupo.nombre_grupo = limpiar_texto(request, 'nombre_grupo') or grupo.nombre_grupo
    grupo.cantidad_extra_permitida = convertir_entero(request.POST.get('cantidad_extra_permitida'), grupo.cantidad_extra_permitida)
    grupo.cantidad_maxima = max(convertir_entero(request.POST.get('cantidad_maxima'), grupo.cantidad_maxima), 1)
    grupo.telefono_contacto = limpiar_texto(request, 'telefono_contacto')
    grupo.correo_contacto = limpiar_texto(request, 'correo_contacto')
    grupo.mesa = limpiar_texto(request, 'mesa')
    grupo.save()
    return 'invitados'


def eliminar_grupo_dashboard(request, evento):
    grupo = get_object_or_404(Grupoinvitacion, id=request.POST.get('grupo_id'), evento=evento)
    grupo.delete()
    return 'invitados'


def crear_invitados_desde_textarea(grupo, texto):
    for orden, linea in enumerate(texto.splitlines(), 1):
        partes = [parte.strip() for parte in linea.split('|')]
        nombre = partes[0] if partes else ''
        if not nombre:
            continue
        tipo_persona = 'NINO' if len(partes) > 1 and partes[1].upper().startswith('N') else 'ADULTO'
        Invitado.objects.create(
            grupo=grupo,
            nombre=nombre,
            tipo_persona=tipo_persona,
            orden=orden,
        )


def agregar_invitado_dashboard(request, evento):
    grupo = get_object_or_404(Grupoinvitacion, id=request.POST.get('grupo_id'), evento=evento, tipo='FAMILIAR')
    nombre = limpiar_texto(request, 'nombre_invitado')
    if not nombre:
        return 'invitados'

    Invitado.objects.create(
        grupo=grupo,
        nombre=nombre,
        tipo_persona=request.POST.get('tipo_persona') or 'ADULTO',
        orden=convertir_entero(request.POST.get('orden_invitado'), 0),
        mesa=limpiar_texto(request, 'mesa_invitado'),
        alergias=limpiar_texto(request, 'alergias_invitado'),
        restricciones_alimentarias=limpiar_texto(request, 'restricciones_invitado'),
        menu_infantil=bool_post(request, 'menu_infantil'),
    )
    return 'invitados'


def editar_invitado_dashboard(request, evento):
    invitado = get_object_or_404(Invitado, id=request.POST.get('invitado_id'), grupo__evento=evento)
    invitado.nombre = limpiar_texto(request, 'nombre_invitado') or invitado.nombre
    invitado.tipo_persona = request.POST.get('tipo_persona') or invitado.tipo_persona
    invitado.orden = convertir_entero(request.POST.get('orden_invitado'), invitado.orden)
    invitado.mesa = limpiar_texto(request, 'mesa_invitado')
    invitado.alergias = limpiar_texto(request, 'alergias_invitado')
    invitado.restricciones_alimentarias = limpiar_texto(request, 'restricciones_invitado')
    invitado.menu_infantil = bool_post(request, 'menu_infantil')
    invitado.save()
    return 'invitados'


def eliminar_invitado_dashboard(request, evento):
    invitado = get_object_or_404(Invitado, id=request.POST.get('invitado_id'), grupo__evento=evento)
    invitado.delete()
    return 'invitados'


def empresa_operativa_dashboard(request, evento):
    empresa, _ = empresa_actual_dashboard(request)
    return evento.empresa or empresa


def agregar_sede_dashboard(request, evento):
    empresa = empresa_operativa_dashboard(request, evento)
    nombre = limpiar_texto(request, 'nombre_sede')
    if not empresa or not nombre:
        return 'operacion'

    SedeEvento.objects.create(
        empresa=empresa,
        nombre=nombre,
        tipo=request.POST.get('tipo_sede') or 'SALON',
        capacidad_minima=convertir_entero(request.POST.get('capacidad_minima'), 0),
        capacidad_maxima=convertir_entero(request.POST.get('capacidad_maxima'), 0),
        precio_base=convertir_decimal(request.POST.get('precio_base_sede'), 0),
        direccion=limpiar_texto(request, 'direccion_sede'),
        descripcion=limpiar_texto(request, 'descripcion_sede'),
        activa=True,
    )
    return 'operacion'


def agregar_proveedor_empresa_dashboard(request, evento):
    empresa = empresa_operativa_dashboard(request, evento)
    nombre = limpiar_texto(request, 'nombre_proveedor')
    if not empresa or not nombre:
        return 'operacion'

    Proveedor.objects.create(
        empresa=empresa,
        nombre_comercial=nombre,
        tipo_proveedor=request.POST.get('tipo_proveedor') or 'OTROS',
        nombre_contacto=limpiar_texto(request, 'contacto_proveedor'),
        telefono=limpiar_texto(request, 'telefono_proveedor'),
        correo=limpiar_texto(request, 'correo_proveedor'),
        contacto_operativo=limpiar_texto(request, 'contacto_operativo_proveedor'),
        telefono_operativo=limpiar_texto(request, 'telefono_operativo_proveedor'),
        correo_operativo=limpiar_texto(request, 'correo_operativo_proveedor'),
        visible_para_wedding_planners=request.POST.get('visible_wedding_planners_proveedor', 'on') == 'on',
        rfc=limpiar_texto(request, 'rfc_proveedor'),
        datos_bancarios=limpiar_texto(request, 'datos_bancarios_proveedor'),
        notas_privadas=limpiar_texto(request, 'notas_privadas_proveedor'),
        descripcion=limpiar_texto(request, 'descripcion_proveedor'),
        activo=True,
    )
    return 'operacion'


def agregar_paquete_empresa_dashboard(request, evento):
    empresa = empresa_operativa_dashboard(request, evento)
    nombre = limpiar_texto(request, 'nombre_paquete')
    if not empresa or not nombre:
        return 'operacion'

    PaqueteBoda.objects.create(
        empresa=empresa,
        nombre=nombre,
        descripcion=limpiar_texto(request, 'descripcion_paquete'),
        precio_base=convertir_decimal(request.POST.get('precio_base_paquete'), 0),
        numero_personas_incluidas=convertir_entero(request.POST.get('personas_paquete'), 0),
        activo=True,
    )
    return 'operacion'


def editar_sede_empresa_avanzado_dashboard(request, evento):
    empresa = empresa_operativa_dashboard(request, evento)
    if empresa:
        actualizar_sede_empresa_dashboard(request, empresa)
    return 'contenido'


def eliminar_sede_empresa_avanzado_dashboard(request, evento):
    empresa = empresa_operativa_dashboard(request, evento)
    if empresa:
        eliminar_sede_empresa_dashboard(request, empresa)
    return 'contenido'


def editar_proveedor_empresa_avanzado_dashboard(request, evento):
    empresa = empresa_operativa_dashboard(request, evento)
    if empresa:
        actualizar_proveedor_empresa_dashboard(request, empresa)
    return 'contenido'


def eliminar_proveedor_empresa_avanzado_dashboard(request, evento):
    empresa = empresa_operativa_dashboard(request, evento)
    if empresa:
        eliminar_proveedor_empresa_dashboard(request, empresa)
    return 'contenido'


def editar_paquete_empresa_avanzado_dashboard(request, evento):
    empresa = empresa_operativa_dashboard(request, evento)
    if empresa:
        actualizar_paquete_empresa_dashboard(request, empresa)
    return 'contenido'


def eliminar_paquete_empresa_avanzado_dashboard(request, evento):
    empresa = empresa_operativa_dashboard(request, evento)
    if empresa:
        eliminar_paquete_empresa_dashboard(request, empresa)
    return 'contenido'


def crear_usuario_empresa_dashboard(request, evento):
    empresa = empresa_operativa_dashboard(request, evento)
    username = limpiar_texto(request, 'username_usuario')
    if not empresa or not username:
        return 'usuarios'

    usuarios_activos = empresa.membresias.filter(activo=True).values('usuario_id').distinct().count()
    if usuarios_activos >= empresa.max_usuarios:
        return 'usuarios'

    crear_o_actualizar_usuario_empresa(request, empresa, 'WEDDING_PLANNER')
    return 'usuarios'


def editar_membresia_empresa_dashboard(request, evento):
    empresa = empresa_operativa_dashboard(request, evento)
    membresia = get_object_or_404(
        MembresiaEmpresa.objects.select_related('usuario'),
        id=request.POST.get('membresia_id'),
        empresa=empresa,
    )
    roles_validos = {valor for valor, _ in MembresiaEmpresa.ROLES}
    rol = request.POST.get('rol_usuario') if request.POST.get('rol_usuario') in roles_validos else membresia.rol
    user = membresia.usuario
    user.first_name = limpiar_texto(request, 'first_name_usuario')
    user.last_name = limpiar_texto(request, 'last_name_usuario')
    user.email = limpiar_texto(request, 'email_usuario')
    user.is_active = bool_post(request, 'activo_usuario')
    password = request.POST.get('password_usuario')
    if password:
        user.set_password(password)
    user.save()

    datos_membresia = {
        'activo': bool_post(request, 'activo_usuario'),
        'puede_gestionar_catalogos': bool_post(request, 'puede_gestionar_catalogos_usuario'),
    }
    if rol != membresia.rol:
        nueva_membresia, _ = MembresiaEmpresa.objects.update_or_create(
            empresa=empresa,
            usuario=user,
            rol=rol,
            defaults=datos_membresia,
        )
        MembresiaEmpresa.objects.filter(empresa=empresa, usuario=user).exclude(id=nueva_membresia.id).update(activo=False)
    else:
        for campo, valor in datos_membresia.items():
            setattr(membresia, campo, valor)
        membresia.save()
    return 'usuarios'


def desactivar_membresia_empresa_dashboard(request, evento):
    empresa = empresa_operativa_dashboard(request, evento)
    membresia = get_object_or_404(MembresiaEmpresa, id=request.POST.get('membresia_id'), empresa=empresa)
    if membresia.usuario_id == request.user.id:
        messages.error(request, 'No puedes desactivar tu propio acceso desde este panel.')
        return 'usuarios'
    membresia.activo = False
    membresia.save(update_fields=['activo'])
    if not MembresiaEmpresa.objects.filter(usuario=membresia.usuario, activo=True).exists():
        membresia.usuario.is_active = False
        membresia.usuario.save(update_fields=['is_active'])
    return 'usuarios'


def eliminar_membresia_empresa_dashboard(request, evento):
    empresa = empresa_operativa_dashboard(request, evento)
    membresia = get_object_or_404(
        MembresiaEmpresa.objects.select_related('usuario'),
        id=request.POST.get('membresia_id'),
        empresa=empresa,
    )
    if membresia.usuario_id == request.user.id:
        messages.error(request, 'No puedes eliminar tu propio acceso desde este panel.')
        return 'usuarios'

    user = membresia.usuario
    username = user.username
    membresia_id = membresia.id
    membresia.delete()
    if not user.is_staff and not user.is_superuser and not MembresiaEmpresa.objects.filter(usuario=user).exists():
        user.delete()

    registrar_auditoria(
        usuario=request.user,
        empresa=empresa,
        evento=evento,
        accion='ELIMINAR_MEMBRESIA_EMPRESA',
        modelo='MembresiaEmpresa',
        objeto_id=membresia_id,
        descripcion=f'Se elimino el acceso de {username} desde el dashboard avanzado.',
        request=request,
    )
    messages.success(request, f'Acceso eliminado: {username}.')
    return 'usuarios'


def asignar_planner_evento_dashboard(request, evento):
    empresa = empresa_operativa_dashboard(request, evento)
    planner_id = request.POST.get('planner_id')
    if not empresa:
        return 'usuarios'

    if not planner_id:
        evento.wedding_planner = None
        evento.save(update_fields=['wedding_planner'])
        return 'usuarios'

    membresia = get_object_or_404(
        MembresiaEmpresa,
        empresa=empresa,
        usuario_id=planner_id,
        rol='WEDDING_PLANNER',
        activo=True,
    )
    evento.wedding_planner = membresia.usuario
    if not evento.empresa:
        evento.empresa = empresa
        evento.save(update_fields=['wedding_planner', 'empresa'])
    else:
        evento.save(update_fields=['wedding_planner'])
    return 'usuarios'


ACCIONES_DASHBOARD_AVANZADO = {
    'agregar_persona_ceremonia': agregar_persona_ceremonia_dashboard,
    'editar_persona_ceremonia': editar_persona_ceremonia_dashboard,
    'eliminar_persona_ceremonia': eliminar_persona_ceremonia_dashboard,
    'editar_regalo': editar_regalo_dashboard,
    'eliminar_regalo': eliminar_regalo_dashboard,
    'editar_album': editar_album_dashboard,
    'eliminar_album': eliminar_album_dashboard,
    'agregar_servicio_evento': agregar_servicio_evento_dashboard,
    'editar_servicio_evento': editar_servicio_evento_dashboard,
    'eliminar_servicio_evento': eliminar_servicio_evento_dashboard,
    'agregar_paquete_evento': agregar_paquete_evento_dashboard,
    'editar_paquete_evento': editar_paquete_evento_dashboard,
    'eliminar_paquete_evento': eliminar_paquete_evento_dashboard,
    'agregar_personal_evento': agregar_personal_evento_dashboard,
    'editar_personal_evento': editar_personal_evento_dashboard,
    'eliminar_personal_evento': eliminar_personal_evento_dashboard,
    'agregar_catering_evento': agregar_catering_evento_dashboard,
    'editar_catering_evento': editar_catering_evento_dashboard,
    'eliminar_catering_evento': eliminar_catering_evento_dashboard,
    'agregar_decoracion_evento': agregar_decoracion_evento_dashboard,
    'editar_decoracion_evento': editar_decoracion_evento_dashboard,
    'eliminar_decoracion_evento': eliminar_decoracion_evento_dashboard,
    'agregar_entretenimiento_evento': agregar_entretenimiento_evento_dashboard,
    'editar_entretenimiento_evento': editar_entretenimiento_evento_dashboard,
    'eliminar_entretenimiento_evento': eliminar_entretenimiento_evento_dashboard,
    'agregar_cancion_evento': agregar_cancion_evento_dashboard,
    'editar_cancion_evento': editar_cancion_evento_dashboard,
    'eliminar_cancion_evento': eliminar_cancion_evento_dashboard,
    'agregar_tarea_evento': agregar_tarea_evento_dashboard,
    'editar_tarea_evento': editar_tarea_evento_dashboard,
    'eliminar_tarea_evento': eliminar_tarea_evento_dashboard,
    'agregar_gasto_evento': agregar_gasto_evento_dashboard,
    'editar_gasto_evento': editar_gasto_evento_dashboard,
    'eliminar_gasto_evento': eliminar_gasto_evento_dashboard,
    'agregar_pago_evento': agregar_pago_evento_dashboard,
    'editar_pago_evento': editar_pago_evento_dashboard,
    'eliminar_pago_evento': eliminar_pago_evento_dashboard,
    'agregar_documento_evento': agregar_documento_evento_dashboard,
    'editar_documento_evento': editar_documento_evento_dashboard,
    'eliminar_documento_evento': eliminar_documento_evento_dashboard,
    'agregar_aprobacion_evento': agregar_aprobacion_evento_dashboard,
    'editar_aprobacion_evento': editar_aprobacion_evento_dashboard,
    'eliminar_aprobacion_evento': eliminar_aprobacion_evento_dashboard,
    'guardar_detalle_produccion': guardar_detalle_produccion_dashboard,
    'generar_pendientes_contrato': generar_pendientes_contrato_dashboard,
    'agregar_grupo': agregar_grupo_dashboard,
    'editar_grupo': editar_grupo_dashboard,
    'eliminar_grupo': eliminar_grupo_dashboard,
    'agregar_invitado': agregar_invitado_dashboard,
    'editar_invitado': editar_invitado_dashboard,
    'eliminar_invitado': eliminar_invitado_dashboard,
    'agregar_sede_empresa': agregar_sede_dashboard,
    'editar_sede_empresa': editar_sede_empresa_avanzado_dashboard,
    'eliminar_sede_empresa': eliminar_sede_empresa_avanzado_dashboard,
    'agregar_proveedor_empresa': agregar_proveedor_empresa_dashboard,
    'editar_proveedor_empresa': editar_proveedor_empresa_avanzado_dashboard,
    'eliminar_proveedor_empresa': eliminar_proveedor_empresa_avanzado_dashboard,
    'agregar_paquete_empresa': agregar_paquete_empresa_dashboard,
    'editar_paquete_empresa': editar_paquete_empresa_avanzado_dashboard,
    'eliminar_paquete_empresa': eliminar_paquete_empresa_avanzado_dashboard,
    'crear_usuario_empresa': crear_usuario_empresa_dashboard,
    'editar_membresia_empresa': editar_membresia_empresa_dashboard,
    'desactivar_membresia_empresa': desactivar_membresia_empresa_dashboard,
    'eliminar_membresia_empresa': eliminar_membresia_empresa_dashboard,
    'asignar_planner_evento': asignar_planner_evento_dashboard,
}

ACCIONES_CATALOGOS_EMPRESA = {
    'agregar_sede_empresa',
    'editar_sede_empresa',
    'eliminar_sede_empresa',
    'agregar_proveedor_empresa',
    'editar_proveedor_empresa',
    'eliminar_proveedor_empresa',
    'agregar_paquete_empresa',
    'editar_paquete_empresa',
    'eliminar_paquete_empresa',
}

ACCIONES_USUARIOS_EMPRESA = {
    'crear_usuario_empresa',
    'editar_membresia_empresa',
    'desactivar_membresia_empresa',
    'eliminar_membresia_empresa',
    'asignar_planner_evento',
}


@login_required(login_url=LOGIN_DASHBOARD_URL)
def dashboard(request):
    evento, eventos = obtener_evento_dashboard(request)
    empresa_dashboard, empresas_dashboard = empresa_actual_dashboard(request)
    if not empresa_dashboard and evento and evento.empresa:
        empresa_dashboard = evento.empresa
    membresia_actual = membresia_empresa_usuario(request.user, empresa_dashboard)
    puede_gestionar_catalogos = usuario_puede_gestionar_catalogos(request.user, empresa_dashboard)
    puede_gestionar_usuarios = usuario_puede_gestionar_usuarios(request.user, empresa_dashboard)

    if request.method == 'POST' and request.POST.get('accion') in ACCIONES_DASHBOARD_AVANZADO:
        accion = request.POST.get('accion')
        evento = get_object_or_404(eventos_visibles_usuario(request.user), id=request.POST.get('evento_id'))
        empresa_accion = empresa_operativa_dashboard(request, evento)
        if accion in ACCIONES_CATALOGOS_EMPRESA and not usuario_puede_gestionar_catalogos(request.user, empresa_accion):
            bloquear_accion_dashboard(request, empresa=empresa_accion, evento=evento, accion=accion, permiso='gestionar catalogos')
        if accion in ACCIONES_USUARIOS_EMPRESA and not usuario_puede_gestionar_usuarios(request.user, empresa_accion):
            bloquear_accion_dashboard(request, empresa=empresa_accion, evento=evento, accion=accion, permiso='gestionar usuarios')
        destino = ACCIONES_DASHBOARD_AVANZADO[accion](request, evento)
        return redirect(f'/dashboard/?evento={evento.id}#{destino}')

    if request.method == 'POST' and request.POST.get('accion') == 'personalizar_evento':
        evento = get_object_or_404(eventos_visibles_usuario(request.user), id=request.POST.get('evento_id'))
        guardar_personalizacion_evento(request, evento)
        return redirect(f'/dashboard/?evento={evento.id}')

    if request.method == 'POST' and request.POST.get('accion') == 'agregar_regalo':
        evento = get_object_or_404(eventos_visibles_usuario(request.user), id=request.POST.get('evento_id'))
        agregar_regalo_dashboard(request, evento)
        return redirect(f'/dashboard/?evento={evento.id}')

    if request.method == 'POST' and request.POST.get('accion') == 'agregar_album':
        evento = get_object_or_404(eventos_visibles_usuario(request.user), id=request.POST.get('evento_id'))
        agregar_album_dashboard(request, evento)
        return redirect(f'/dashboard/?evento={evento.id}')

    if request.method == 'POST' and request.POST.get('accion') == 'agregar_itinerario':
        evento = get_object_or_404(eventos_visibles_usuario(request.user), id=request.POST.get('evento_id'))
        agregar_itinerario_dashboard(request, evento)
        return redirect(f'/dashboard/?evento={evento.id}')

    if request.method == 'POST' and request.POST.get('accion') == 'editar_seccion_invitacion':
        evento = get_object_or_404(eventos_visibles_usuario(request.user), id=request.POST.get('evento_id'))
        sincronizar_secciones_invitacion(evento)
        actualizar_seccion_invitacion_dashboard(request, evento)
        return redirect(f'/dashboard/?evento={evento.id}#secciones-invitacion')

    grupos = list(
        Grupoinvitacion.objects.filter(evento=evento)
        .select_related('evento')
        .prefetch_related('invitados')
        .order_by('tipo', 'nombre_grupo')
    ) if evento else []

    total_grupos = len(grupos)
    total_lugares = sum(grupo.total_lugares for grupo in grupos)
    total_asistiran = sum(grupo.lugares_asistiran for grupo in grupos)
    total_no_asistiran = sum(grupo.lugares_no_asistiran for grupo in grupos)
    total_pendientes = sum(grupo.lugares_pendientes for grupo in grupos)
    total_adultos = sum(grupo.adultos_confirmados for grupo in grupos)
    total_ninos = sum(grupo.ninos_confirmados for grupo in grupos)

    porcentaje_asistencia = 0
    if total_lugares > 0:
        porcentaje_asistencia = round((total_asistiran / total_lugares) * 100, 2)

    servicios_evento = ServicioEvento.objects.filter(evento=evento).select_related('proveedor') if evento else ServicioEvento.objects.none()
    personal_evento = PersonalEvento.objects.filter(evento=evento).select_related('proveedor') if evento else PersonalEvento.objects.none()
    catering_evento = CateringEvento.objects.filter(evento=evento).select_related('proveedor', 'paquete_buffet').prefetch_related('alimentos_seleccionados') if evento else CateringEvento.objects.none()
    paquetes_evento = PaqueteEvento.objects.filter(evento=evento).select_related('paquete') if evento else PaqueteEvento.objects.none()
    decoracion_evento = ElementoDecoracion.objects.filter(evento=evento).select_related('proveedor') if evento else ElementoDecoracion.objects.none()
    entretenimiento_evento = EntretenimientoEvento.objects.filter(evento=evento).select_related('proveedor') if evento else EntretenimientoEvento.objects.none()
    canciones_evento = CancionEvento.objects.filter(evento=evento).select_related('entretenimiento') if evento else CancionEvento.objects.none()
    actividades_evento = ActividadItinerario.objects.filter(evento=evento) if evento else ActividadItinerario.objects.none()
    mesas_evento = Mesa.objects.filter(evento=evento) if evento else Mesa.objects.none()
    asignaciones_mesa = AsignacionMesa.objects.filter(mesa__evento=evento) if evento else AsignacionMesa.objects.none()
    gastos_evento = GastoEvento.objects.filter(evento=evento).select_related('categoria', 'proveedor').prefetch_related('pagos') if evento else GastoEvento.objects.none()
    pagos_evento = PagoEvento.objects.filter(gasto__evento=evento).select_related('gasto') if evento else PagoEvento.objects.none()
    tareas_evento = TareaEvento.objects.filter(evento=evento).select_related('responsable') if evento else TareaEvento.objects.none()
    documentos_evento = DocumentoEvento.objects.filter(evento=evento).select_related('proveedor', 'cargado_por') if evento else DocumentoEvento.objects.none()
    aprobaciones_evento = AprobacionEvento.objects.filter(evento=evento).select_related('solicitado_por', 'aprobado_por') if evento else AprobacionEvento.objects.none()
    notificaciones_evento = Notificacion.objects.filter(evento=evento) if evento else Notificacion.objects.none()
    detalle_produccion = DetalleProduccionEvento.objects.filter(evento=evento).first() if evento else None
    usuarios_empresa = (
        MembresiaEmpresa.objects.filter(empresa=empresa_dashboard)
        .select_related('usuario')
        .order_by('-activo', 'rol', 'usuario__username')
    ) if empresa_dashboard and puede_gestionar_usuarios else MembresiaEmpresa.objects.none()
    planners_empresa = usuarios_empresa.filter(rol='WEDDING_PLANNER', activo=True) if empresa_dashboard and puede_gestionar_usuarios else MembresiaEmpresa.objects.none()
    responsables_evento = usuarios_empresa_para_evento(evento) if evento else get_user_model().objects.none()

    total_proveedores_evento = servicios_evento.values('proveedor').distinct().count()
    total_servicios_evento = servicios_evento.count()
    proveedores_pendientes = servicios_evento.exclude(
        estado__in=['CONTRATADO', 'ANTICIPO_PAGADO', 'LIQUIDADO', 'SERVICIO_COMPLETADO']
    ).count()
    total_personal_evento = personal_evento.count()
    total_catering_evento = catering_evento.count()
    total_paquetes_evento = paquetes_evento.count()
    total_decoracion_evento = decoracion_evento.count()
    decoracion_pendiente = decoracion_evento.exclude(estado__in=['APROBADO', 'COMPRADO', 'RENTADO', 'LISTO_MONTAJE', 'MONTADO']).count()
    total_entretenimiento_evento = entretenimiento_evento.count()
    total_canciones_evento = canciones_evento.count()
    total_actividades_evento = actividades_evento.count()
    actividades_pendientes = actividades_evento.exclude(estado__in=['COMPLETADA', 'CANCELADA']).count()
    total_mesas_evento = mesas_evento.count()
    mesas_excedidas = sum(1 for mesa in mesas_evento if mesa.excedida)
    invitados_confirmados_sin_mesa = max(total_asistiran - asignaciones_mesa.count(), 0)
    total_gastos_evento = gastos_evento.count()
    total_gasto_estimado = gastos_evento.aggregate(total=Sum('monto_estimado'))['total'] or 0
    total_gasto_real = gastos_evento.aggregate(total=Sum('monto_real'))['total'] or 0
    total_pagos_evento = pagos_evento.aggregate(total=Sum('monto'))['total'] or 0
    gastos_vencidos = sum(1 for gasto in gastos_evento if gasto.esta_vencido)
    total_tareas_evento = tareas_evento.count()
    tareas_pendientes = tareas_evento.exclude(estado__in=['COMPLETADA', 'CANCELADA']).count()
    tareas_vencidas = sum(1 for tarea in tareas_evento if tarea.esta_vencida)
    total_documentos_evento = documentos_evento.count()
    documentos_cliente = documentos_evento.filter(visible_cliente=True).count()
    aprobaciones_pendientes = aprobaciones_evento.filter(estado='PENDIENTE').count()
    total_aprobaciones_evento = aprobaciones_evento.count()
    notificaciones_no_leidas = notificaciones_evento.filter(leida=False).count()

    base_url = request.build_absolute_uri('/')[:-1]
    for grupo in grupos:
        preparar_links_grupo(grupo, base_url)

    context = {
        'evento': evento,
        'eventos': eventos,
        'empresa_dashboard': empresa_dashboard,
        'empresas_dashboard': empresas_dashboard,
        'membresia_actual': membresia_actual,
        'es_dirtec': usuario_es_dirtec(request.user),
        'puede_gestionar_catalogos': puede_gestionar_catalogos,
        'puede_gestionar_usuarios': puede_gestionar_usuarios,
        'usuarios_empresa': usuarios_empresa,
        'planners_empresa': planners_empresa,
        'roles_empresa': MembresiaEmpresa.ROLES,
        'sedes_empresa': empresa_dashboard.sedes.filter(activa=True) if empresa_dashboard else [],
        'proveedores_empresa': empresa_dashboard.proveedores.filter(activo=True) if empresa_dashboard else [],
        'paquetes_empresa': empresa_dashboard.paquetes.filter(activo=True) if empresa_dashboard else [],
        'tipos_sede': SedeEvento.TIPOS,
        'tipos_proveedor': Proveedor.TIPOS,
        'catalogo_sedes_empresa': empresa_dashboard.sedes.all() if empresa_dashboard and puede_gestionar_catalogos else [],
        'catalogo_proveedores_empresa': empresa_dashboard.proveedores.all() if empresa_dashboard and puede_gestionar_catalogos else [],
        'catalogo_paquetes_empresa': empresa_dashboard.paquetes.all() if empresa_dashboard and puede_gestionar_catalogos else [],
        'servicios_evento': servicios_evento,
        'personal_evento': personal_evento,
        'tareas_evento': tareas_evento,
        'gastos_evento': gastos_evento,
        'pagos_evento': pagos_evento,
        'documentos_evento': documentos_evento,
        'aprobaciones_evento': aprobaciones_evento,
        'detalle_produccion': detalle_produccion,
        'responsables_evento': responsables_evento,
        'categorias_gasto': CategoriaGasto.objects.filter(activo=True).order_by('nombre'),
        'estados_servicio': ServicioEvento.ESTADOS,
        'paquetes_evento': paquetes_evento,
        'estados_paquete_evento': PaqueteEvento.ESTADOS,
        'tipos_personal': PersonalEvento.TIPOS,
        'estados_personal': PersonalEvento.ESTADOS,
        'catering_evento': catering_evento,
        'paquetes_buffet': PaqueteBuffet.objects.filter(activo=True, proveedor__empresa=empresa_dashboard) if empresa_dashboard else PaqueteBuffet.objects.none(),
        'alimentos': Alimento.objects.filter(activo=True).select_related('categoria'),
        'categorias_decoracion': ElementoDecoracion.CATEGORIAS,
        'estados_decoracion': ElementoDecoracion.ESTADOS,
        'decoracion_evento': decoracion_evento,
        'tipos_entretenimiento': EntretenimientoEvento.TIPOS,
        'estados_entretenimiento': EntretenimientoEvento.ESTADOS,
        'entretenimiento_evento': entretenimiento_evento,
        'canciones_evento': canciones_evento,
        'momentos_cancion': CancionEvento.TIPOS_MOMENTO,
        'estados_tarea': TareaEvento.ESTADOS,
        'prioridades_tarea': TareaEvento.PRIORIDADES,
        'categorias_tarea': TareaEvento.CATEGORIAS,
        'estados_gasto': GastoEvento.ESTADOS,
        'metodos_pago': PagoEvento.METODOS,
        'tipos_documento': DocumentoEvento.TIPOS,
        'tipos_aprobacion': AprobacionEvento.TIPOS,
        'estados_aprobacion': AprobacionEvento.ESTADOS,
        'preview_grupo': grupos[0] if grupos else None,
        'total_grupos': total_grupos,
        'total_lugares': total_lugares,
        'total_asistiran': total_asistiran,
        'total_no_asistiran': total_no_asistiran,
        'total_pendientes': total_pendientes,
        'total_adultos': total_adultos,
        'total_ninos': total_ninos,
        'porcentaje_asistencia': porcentaje_asistencia,
        'total_proveedores_evento': total_proveedores_evento,
        'total_servicios_evento': total_servicios_evento,
        'proveedores_pendientes': proveedores_pendientes,
        'total_personal_evento': total_personal_evento,
        'total_catering_evento': total_catering_evento,
        'total_paquetes_evento': total_paquetes_evento,
        'total_decoracion_evento': total_decoracion_evento,
        'decoracion_pendiente': decoracion_pendiente,
        'total_entretenimiento_evento': total_entretenimiento_evento,
        'total_canciones_evento': total_canciones_evento,
        'total_actividades_evento': total_actividades_evento,
        'actividades_pendientes': actividades_pendientes,
        'total_mesas_evento': total_mesas_evento,
        'mesas_excedidas': mesas_excedidas,
        'invitados_confirmados_sin_mesa': invitados_confirmados_sin_mesa,
        'total_gastos_evento': total_gastos_evento,
        'total_gasto_estimado': total_gasto_estimado,
        'total_gasto_real': total_gasto_real,
        'total_pagos_evento': total_pagos_evento,
        'gastos_vencidos': gastos_vencidos,
        'total_tareas_evento': total_tareas_evento,
        'tareas_pendientes': tareas_pendientes,
        'tareas_vencidas': tareas_vencidas,
        'total_documentos_evento': total_documentos_evento,
        'documentos_cliente': documentos_cliente,
        'total_aprobaciones_evento': total_aprobaciones_evento,
        'aprobaciones_pendientes': aprobaciones_pendientes,
        'notificaciones_no_leidas': notificaciones_no_leidas,
        'presupuesto_total': evento.presupuesto_total if evento else 0,
        'monto_pagado': evento.monto_pagado if evento else 0,
        'monto_pendiente': evento.monto_pendiente if evento else 0,
        'grupos': grupos,
        'base_url': base_url,
        'paletas': EventoBoda.PALETAS,
        'estilos_letra': EventoBoda.ESTILOS_LETRA,
        'tipos_evento': EventoBoda.TIPOS_EVENTO,
        'plantillas_evento': PLANTILLAS_EVENTO,
        'estados_evento': EventoBoda.ESTADOS_EVENTO,
        'tipos_regalo': EnlaceRegalo.TIPOS,
        'secciones_persona': PersonaCeremonia.SECCIONES,
        'tipos_invitacion': Grupoinvitacion.TIPO_INVITACION,
        'tipos_persona': Invitado.TIPO_PERSONA,
        'iconos_itinerario': ItinerarioEvento.ICONOS,
        'secciones_editor': sincronizar_secciones_invitacion(evento) if evento else [],
        'posiciones_fondo_seccion': SeccionInvitacion.POSICIONES_FONDO,
        'editor_invitacion_url': f'/dashboard/editor-invitacion/{evento.id}/' if evento else '',
        'api_dashboard_url': f'/api/dashboard/metricas/?evento={evento.id}' if evento else '',
    }

    return render(request, 'invitaciones/dashboard.html', context)


def construir_metricas_dashboard(evento):
    grupos = list(
        Grupoinvitacion.objects.filter(evento=evento)
        .prefetch_related('invitados')
    ) if evento else []
    total_lugares = sum(grupo.total_lugares for grupo in grupos)
    total_asistiran = sum(grupo.lugares_asistiran for grupo in grupos)
    total_no_asistiran = sum(grupo.lugares_no_asistiran for grupo in grupos)
    total_pendientes = sum(grupo.lugares_pendientes for grupo in grupos)
    total_adultos = sum(grupo.adultos_confirmados for grupo in grupos)
    total_ninos = sum(grupo.ninos_confirmados for grupo in grupos)

    gastos = GastoEvento.objects.filter(evento=evento) if evento else GastoEvento.objects.none()
    pagos = PagoEvento.objects.filter(gasto__evento=evento) if evento else PagoEvento.objects.none()
    tareas = TareaEvento.objects.filter(evento=evento) if evento else TareaEvento.objects.none()
    servicios = ServicioEvento.objects.filter(evento=evento) if evento else ServicioEvento.objects.none()

    gasto_estimado = gastos.aggregate(total=Sum('monto_estimado'))['total'] or 0
    gasto_real = gastos.aggregate(total=Sum('monto_real'))['total'] or 0
    total_pagado = pagos.aggregate(total=Sum('monto'))['total'] or 0
    gasto_objetivo = gasto_real or gasto_estimado
    saldo = gasto_objetivo - total_pagado

    return {
        'evento': str(evento) if evento else 'Sin evento',
        'resumen': {
            'total_lugares': total_lugares,
            'confirmados': total_asistiran,
            'pendientes': total_pendientes,
            'rechazados': total_no_asistiran,
            'adultos': total_adultos,
            'ninos': total_ninos,
            'gasto_estimado': float(gasto_estimado),
            'gasto_real': float(gasto_real),
            'pagado': float(total_pagado),
            'saldo': float(saldo if saldo > 0 else 0),
        },
        'charts': {
            'invitados': {
                'labels': ['Confirmados', 'Pendientes', 'No asisten'],
                'values': [total_asistiran, total_pendientes, total_no_asistiran],
            },
            'buffet': {
                'labels': ['Adultos', 'Ninos'],
                'values': [total_adultos, total_ninos],
            },
            'presupuesto': {
                'labels': ['Estimado', 'Real', 'Pagado', 'Saldo'],
                'values': [
                    float(gasto_estimado),
                    float(gasto_real),
                    float(total_pagado),
                    float(saldo if saldo > 0 else 0),
                ],
            },
            'tareas': {
                'labels': ['Pendiente', 'En proceso', 'En revision', 'Completada', 'Cancelada'],
                'values': [
                    tareas.filter(estado='PENDIENTE').count(),
                    tareas.filter(estado='EN_PROCESO').count(),
                    tareas.filter(estado='EN_REVISION').count(),
                    tareas.filter(estado='COMPLETADA').count(),
                    tareas.filter(estado='CANCELADA').count(),
                ],
            },
            'proveedores': {
                'labels': ['Pendientes', 'Contratados', 'Pagados/Listos', 'Cancelados'],
                'values': [
                    servicios.filter(estado__in=['SOLICITADO', 'COTIZADO', 'PENDIENTE_APROBACION', 'APROBADO']).count(),
                    servicios.filter(estado='CONTRATADO').count(),
                    servicios.filter(estado__in=['ANTICIPO_PAGADO', 'LIQUIDADO', 'SERVICIO_COMPLETADO']).count(),
                    servicios.filter(estado='CANCELADO').count(),
                ],
            },
        },
    }


def enlace_operativo_calendario(request, evento, admin_path):
    if usuario_es_dirtec(request.user):
        return admin_path
    return f'/dashboard/?evento={evento.id}#operacion' if evento else ''


@login_required(login_url=LOGIN_DASHBOARD_URL)
def dashboard_metricas_json(request):
    evento, _ = obtener_evento_dashboard(request)
    return JsonResponse(construir_metricas_dashboard(evento))

COMPONENTE_INVITACION_TIPOS = {'TEXTO', 'IMAGEN', 'BOTON'}


def propiedades_componente_default(tipo):
    if tipo == 'BOTON':
        return {'label': 'Boton', 'href': '#', 'style': 'primary'}
    if tipo == 'IMAGEN':
        return {'src': '', 'alt': 'Imagen'}
    return {'text': 'Nuevo texto', 'fontSize': 20, 'fontFamily': 'Playfair Display'}


def normalizar_propiedades_componente(tipo, properties):
    properties = properties if isinstance(properties, dict) else {}
    defaults = propiedades_componente_default(tipo)
    normalizadas = {**defaults, **properties}
    if tipo == 'TEXTO':
        normalizadas['text'] = str(normalizadas.get('text') or defaults['text'])[:500]
        normalizadas['fontFamily'] = str(normalizadas.get('fontFamily') or defaults['fontFamily'])[:80]
        normalizadas['fontSize'] = numero_rango(normalizadas.get('fontSize'), defaults['fontSize'], 8, 96)
        normalizadas['color'] = color_seguro(normalizadas.get('color')) or normalizadas.get('color') or ''
    elif tipo == 'IMAGEN':
        src = str(normalizadas.get('src') or '')[:1000]
        if src and not src.startswith(('/media/', 'http://', 'https://')):
            src = ''
        normalizadas['src'] = src
        normalizadas['alt'] = str(normalizadas.get('alt') or defaults['alt'])[:180]
        normalizadas['fit'] = normalizadas.get('fit') if normalizadas.get('fit') in EDITOR_MEDIA_FIT else 'contain'
    elif tipo == 'BOTON':
        href = str(normalizadas.get('href') or '#')[:1000]
        if href != '#' and not href.startswith(('http://', 'https://', 'mailto:', 'tel:', 'whatsapp://')):
            href = '#'
        normalizadas['label'] = str(normalizadas.get('label') or defaults['label'])[:120]
        normalizadas['href'] = href
        normalizadas['style'] = normalizadas.get('style') if normalizadas.get('style') in {'primary', 'secondary'} else 'primary'
    return normalizadas


def serializar_componente_invitacion(componente):
    return {
        'id': componente.id,
        'componentId': componente.id,
        'sectionId': componente.seccion_id,
        'sectionType': componente.seccion.tipo,
        'tipo': componente.tipo,
        'type': componente.tipo.lower(),
        'x': componente.x,
        'y': componente.y,
        'width': componente.width,
        'height': componente.height,
        'rotation': componente.rotation,
        'opacity': componente.opacity,
        'zIndex': componente.z_index,
        'locked': componente.locked,
        'hidden': componente.hidden,
        'properties': componente.properties or {},
        'createdAt': componente.created_at.isoformat() if componente.created_at else None,
        'updatedAt': componente.updated_at.isoformat() if componente.updated_at else None,
    }


def aplicar_payload_componente(componente, payload):
    tipo = payload.get('tipo') or payload.get('type') or componente.tipo or 'TEXTO'
    tipo = str(tipo).upper()
    if tipo not in COMPONENTE_INVITACION_TIPOS:
        tipo = 'TEXTO'
    componente.tipo = tipo
    componente.x = numero_rango(payload.get('x'), componente.x if componente.pk else 50, -40, 140, decimales=True)
    componente.y = numero_rango(payload.get('y'), componente.y if componente.pk else 50, -40, 140, decimales=True)
    componente.width = numero_rango(payload.get('width'), componente.width if componente.pk else 44, 4, 140, decimales=True)
    componente.height = numero_rango(payload.get('height'), componente.height if componente.pk else 12, 2, 140, decimales=True)
    componente.rotation = numero_rango(payload.get('rotation'), componente.rotation if componente.pk else 0, -180, 180, decimales=True)
    componente.opacity = numero_rango(payload.get('opacity'), componente.opacity if componente.pk else 1, 0, 1, decimales=True)
    componente.z_index = numero_rango(payload.get('zIndex', payload.get('z_index')), componente.z_index if componente.pk else 20, 1, 100)
    componente.locked = bool(payload.get('locked', componente.locked if componente.pk else False))
    componente.hidden = bool(payload.get('hidden', componente.hidden if componente.pk else False))
    componente.properties = normalizar_propiedades_componente(tipo, payload.get('properties'))
    return componente


@login_required(login_url=LOGIN_DASHBOARD_URL)
def componentes_invitacion_visual(request, evento_id):
    evento = get_object_or_404(eventos_visibles_usuario(request.user), id=evento_id)
    if request.method == 'GET':
        componentes = ComponenteInvitacion.objects.filter(evento=evento).select_related('seccion')
        return JsonResponse({
            'ok': True,
            'components': [serializar_componente_invitacion(componente) for componente in componentes],
        })
    if request.method != 'POST':
        return JsonResponse({'ok': False, 'error': 'Metodo no permitido.'}, status=405)
    try:
        payload = json.loads(request.body.decode('utf-8') or '{}')
    except json.JSONDecodeError:
        return JsonResponse({'ok': False, 'error': 'Solicitud invalida.'}, status=400)
    seccion = get_object_or_404(SeccionInvitacion, evento=evento, id=payload.get('sectionId'))
    componente = ComponenteInvitacion(evento=evento, seccion=seccion)
    aplicar_payload_componente(componente, payload)
    try:
        componente.full_clean()
    except ValidationError as exc:
        return JsonResponse({'ok': False, 'error': '; '.join(exc.messages)}, status=400)
    componente.save()
    registrar_auditoria(
        usuario=request.user,
        empresa=evento.empresa,
        evento=evento,
        accion='CREAR_COMPONENTE_INVITACION',
        modelo='ComponenteInvitacion',
        objeto_id=componente.id,
        descripcion=f'Creo componente {componente.get_tipo_display()} en editor visual.',
        request=request,
    )
    return JsonResponse({'ok': True, 'component': serializar_componente_invitacion(componente)}, status=201)


@login_required(login_url=LOGIN_DASHBOARD_URL)
def componente_invitacion_visual(request, evento_id, componente_id):
    evento = get_object_or_404(eventos_visibles_usuario(request.user), id=evento_id)
    componente = get_object_or_404(
        ComponenteInvitacion.objects.select_related('seccion'),
        evento=evento,
        id=componente_id,
    )
    if request.method == 'DELETE':
        componente.delete()
        registrar_auditoria(
            usuario=request.user,
            empresa=evento.empresa,
            evento=evento,
            accion='ELIMINAR_COMPONENTE_INVITACION',
            modelo='ComponenteInvitacion',
            objeto_id=componente_id,
            descripcion='Elimino componente del editor visual.',
            request=request,
        )
        return JsonResponse({'ok': True, 'componentId': componente_id})
    if request.method not in {'POST', 'PATCH'}:
        return JsonResponse({'ok': False, 'error': 'Metodo no permitido.'}, status=405)
    try:
        payload = json.loads(request.body.decode('utf-8') or '{}')
    except json.JSONDecodeError:
        return JsonResponse({'ok': False, 'error': 'Solicitud invalida.'}, status=400)
    if payload.get('action') == 'delete':
        componente.delete()
        return JsonResponse({'ok': True, 'componentId': componente_id})
    if payload.get('sectionId'):
        componente.seccion = get_object_or_404(SeccionInvitacion, evento=evento, id=payload.get('sectionId'))
    aplicar_payload_componente(componente, payload)
    try:
        componente.full_clean()
    except ValidationError as exc:
        return JsonResponse({'ok': False, 'error': '; '.join(exc.messages)}, status=400)
    componente.save()
    return JsonResponse({'ok': True, 'component': serializar_componente_invitacion(componente)})

@login_required(login_url=LOGIN_DASHBOARD_URL)
def editor_invitacion_visual(request, evento_id):
    evento = get_object_or_404(eventos_visibles_usuario(request.user), id=evento_id)
    diseno = obtener_diseno_invitacion(evento, request.user)
    config = sincronizar_diseno_con_secciones(evento, diseno)
    grupos = Grupoinvitacion.objects.filter(evento=evento).order_by('tipo', 'nombre_grupo')
    assets = AssetInvitacion.objects.filter(evento=evento, visible=True)
    context = {
        'evento': evento,
        'diseno': diseno,
        'editor_config': config,
        'editor_config_json': json.dumps(config),
        'editor_content': contenido_editor_payload(evento),
        'editor_guests': invitados_editor_payload(evento, request),
        'editor_versions': versiones_editor_payload(diseno),
        'assets_editor': assets,
        'preview_grupo': grupos.first(),
        'paletas': EventoBoda.PALETAS,
        'estilos_letra': EventoBoda.ESTILOS_LETRA,
        'posiciones_fondo_seccion': SeccionInvitacion.POSICIONES_FONDO,
        'secciones_persona': PersonaCeremonia.SECCIONES,
        'tipos_regalo': EnlaceRegalo.TIPOS,
        'iconos_itinerario': ItinerarioEvento.ICONOS,
        'plantillas_evento': PLANTILLAS_EVENTO,
        'guardar_editor_url': f'/dashboard/editor-invitacion/{evento.id}/guardar/',
        'publicar_editor_url': f'/dashboard/editor-invitacion/{evento.id}/publicar/',
        'aplicar_plantilla_url': f'/dashboard/editor-invitacion/{evento.id}/plantilla/aplicar/',
        'restaurar_version_url': f'/dashboard/editor-invitacion/{evento.id}/versiones/restaurar/',
        'guardar_contenido_url': f'/dashboard/editor-invitacion/{evento.id}/contenido/guardar/',
        'guardar_item_contenido_url': f'/dashboard/editor-invitacion/{evento.id}/contenido/item/',
        'guardar_grupo_invitado_url': f'/dashboard/editor-invitacion/{evento.id}/invitados/grupo/',
        'guardar_invitado_url': f'/dashboard/editor-invitacion/{evento.id}/invitados/persona/',
        'importar_invitados_url': f'/dashboard/editor-invitacion/{evento.id}/invitados/importar/',
        'subir_asset_url': f'/dashboard/editor-invitacion/{evento.id}/assets/subir/',
        'asignar_asset_url': f'/dashboard/editor-invitacion/{evento.id}/assets/asignar/',
        'eliminar_asset_url': f'/dashboard/editor-invitacion/{evento.id}/assets/eliminar/',
        'componentes_url': f'/dashboard/editor-invitacion/{evento.id}/componentes/',
        'preview_borrador_url': f'/invitacion/{grupos.first().codigo}/?preview=1&draft=1' if grupos.first() else '',
        'dashboard_url': f'/dashboard/?evento={evento.id}#personalizacion',
    }
    return render(request, 'invitaciones/editor_invitacion.html', context)


@login_required(login_url=LOGIN_DASHBOARD_URL)
@require_POST
def guardar_diseno_invitacion_visual(request, evento_id):
    evento = get_object_or_404(eventos_visibles_usuario(request.user), id=evento_id)
    diseno = obtener_diseno_invitacion(evento, request.user)
    try:
        payload = json.loads(request.body.decode('utf-8') or '{}')
    except json.JSONDecodeError:
        return JsonResponse({'ok': False, 'error': 'Configuracion invalida.'}, status=400)

    config = normalizar_configuracion_editor(evento, payload)
    diseno.configuracion_borrador = config
    diseno.estado = 'BORRADOR' if not diseno.tiene_publicacion else diseno.estado
    diseno.actualizado_por = request.user
    diseno.save(update_fields=['configuracion_borrador', 'estado', 'actualizado_por', 'fecha_actualizacion'])
    VersionDisenoInvitacion.objects.create(
        diseno=diseno,
        nombre=f'Borrador {timezone.now().strftime("%d/%m/%Y %H:%M")}',
        configuracion=config,
        publicado=False,
        creado_por=request.user,
    )
    registrar_auditoria(
        usuario=request.user,
        empresa=evento.empresa,
        evento=evento,
        accion='GUARDAR_BORRADOR_EDITOR_INVITACION',
        modelo='DisenoInvitacion',
        objeto_id=diseno.id,
        descripcion='Guardo un borrador del editor visual de invitacion.',
        request=request,
    )
    return JsonResponse({
        'ok': True,
        'estado': diseno.estado,
        'config': config,
        'versions': versiones_editor_payload(diseno),
    })


@login_required(login_url=LOGIN_DASHBOARD_URL)
@require_POST
def publicar_diseno_invitacion_visual(request, evento_id):
    evento = get_object_or_404(eventos_visibles_usuario(request.user), id=evento_id)
    diseno = obtener_diseno_invitacion(evento, request.user)
    try:
        payload = json.loads(request.body.decode('utf-8') or '{}')
    except json.JSONDecodeError:
        payload = diseno.configuracion_borrador or construir_configuracion_diseno(evento)

    config = normalizar_configuracion_editor(evento, payload)
    diseno.configuracion_borrador = config
    diseno.publicar(request.user)
    diseno.save(update_fields=[
        'configuracion_borrador',
        'configuracion_publicada',
        'estado',
        'publicado_en',
        'actualizado_por',
        'fecha_actualizacion',
    ])
    aplicar_diseno_publicado(evento, config)
    VersionDisenoInvitacion.objects.create(
        diseno=diseno,
        nombre=f'Publicado {timezone.now().strftime("%d/%m/%Y %H:%M")}',
        configuracion=config,
        publicado=True,
        creado_por=request.user,
    )
    registrar_auditoria(
        usuario=request.user,
        empresa=evento.empresa,
        evento=evento,
        accion='PUBLICAR_EDITOR_INVITACION',
        modelo='DisenoInvitacion',
        objeto_id=diseno.id,
        descripcion='Publico cambios del editor visual de invitacion.',
        request=request,
    )
    return JsonResponse({
        'ok': True,
        'estado': diseno.estado,
        'config': config,
        'versions': versiones_editor_payload(diseno),
        'publicado_en': diseno.publicado_en.isoformat(),
    })


@login_required(login_url=LOGIN_DASHBOARD_URL)
@require_POST
def restaurar_version_diseno_invitacion_visual(request, evento_id):
    evento = get_object_or_404(eventos_visibles_usuario(request.user), id=evento_id)
    diseno = obtener_diseno_invitacion(evento, request.user)
    try:
        payload = json.loads(request.body.decode('utf-8') or '{}')
    except json.JSONDecodeError:
        return JsonResponse({'ok': False, 'error': 'Solicitud invalida.'}, status=400)

    version = get_object_or_404(VersionDisenoInvitacion, diseno=diseno, id=payload.get('versionId'))
    config = normalizar_configuracion_editor(evento, version.configuracion)
    diseno.configuracion_borrador = config
    diseno.estado = 'BORRADOR'
    diseno.actualizado_por = request.user
    diseno.save(update_fields=['configuracion_borrador', 'estado', 'actualizado_por', 'fecha_actualizacion'])
    VersionDisenoInvitacion.objects.create(
        diseno=diseno,
        nombre=f'Restaurado desde {version.nombre}',
        configuracion=config,
        publicado=False,
        creado_por=request.user,
    )
    registrar_auditoria(
        usuario=request.user,
        empresa=evento.empresa,
        evento=evento,
        accion='RESTAURAR_VERSION_EDITOR_INVITACION',
        modelo='VersionDisenoInvitacion',
        objeto_id=version.id,
        descripcion=f'Restauro version del editor visual: {version.nombre}.',
        request=request,
    )
    return JsonResponse({
        'ok': True,
        'config': config,
        'versions': versiones_editor_payload(diseno),
    })


@login_required(login_url=LOGIN_DASHBOARD_URL)
@require_POST
def aplicar_plantilla_invitacion_visual(request, evento_id):
    evento = get_object_or_404(eventos_visibles_usuario(request.user), id=evento_id)
    diseno = obtener_diseno_invitacion(evento, request.user)
    try:
        payload = json.loads(request.body.decode('utf-8') or '{}')
    except json.JSONDecodeError:
        return JsonResponse({'ok': False, 'error': 'Solicitud invalida.'}, status=400)

    codigo = payload.get('template')
    if codigo not in CONFIGURACION_PLANTILLAS_EVENTO:
        return JsonResponse({'ok': False, 'error': 'Plantilla no disponible.'}, status=400)

    config = aplicar_plantilla_a_diseno_editor(evento, diseno, codigo, request.user)
    registrar_auditoria(
        usuario=request.user,
        empresa=evento.empresa,
        evento=evento,
        accion='APLICAR_PLANTILLA_EDITOR_INVITACION',
        modelo='EventoBoda',
        objeto_id=evento.id,
        descripcion=f'Aplico plantilla desde editor visual: {codigo}.',
        request=request,
    )
    return JsonResponse({
        'ok': True,
        'config': config,
        'content': contenido_editor_payload(evento),
        'versions': versiones_editor_payload(diseno),
    })


@login_required(login_url=LOGIN_DASHBOARD_URL)
@require_POST
def subir_asset_invitacion_visual(request, evento_id):
    evento = get_object_or_404(eventos_visibles_usuario(request.user), id=evento_id)
    archivo = request.FILES.get('archivo')
    if not archivo:
        return JsonResponse({'ok': False, 'error': 'Selecciona un archivo.'}, status=400)
    tipo = request.POST.get('tipo') or 'DECORACION'
    if tipo not in dict(AssetInvitacion.TIPOS):
        tipo = 'DECORACION'
    asset = AssetInvitacion(
        evento=evento,
        tipo=tipo,
        titulo=request.POST.get('titulo') or archivo.name,
        archivo=archivo,
        creado_por=request.user,
    )
    try:
        asset.full_clean()
    except ValidationError as exc:
        return JsonResponse({'ok': False, 'error': '; '.join(exc.messages)}, status=400)
    asset.save()
    registrar_auditoria(
        usuario=request.user,
        empresa=evento.empresa,
        evento=evento,
        accion='SUBIR_ASSET_EDITOR_INVITACION',
        modelo='AssetInvitacion',
        objeto_id=asset.id,
        descripcion=f'Subio asset para editor visual: {asset.titulo}.',
        request=request,
    )
    return JsonResponse({
        'ok': True,
        'asset': {
            'id': asset.id,
            'title': asset.titulo,
            'type': asset.tipo,
            'url': asset.archivo.url,
            'isVideo': asset.es_video,
        },
    })


@login_required(login_url=LOGIN_DASHBOARD_URL)
@require_POST
def guardar_contenido_invitacion_visual(request, evento_id):
    evento = get_object_or_404(eventos_visibles_usuario(request.user), id=evento_id)
    try:
        payload = json.loads(request.body.decode('utf-8') or '{}')
    except json.JSONDecodeError:
        return JsonResponse({'ok': False, 'error': 'Contenido invalido.'}, status=400)

    campos = {
        'eventName': ('nombre_evento', 180),
        'mainName': ('nombre_principal', 120),
        'secondaryName': ('nombre_secundario', 120),
        'mainLabel': ('etiqueta_principal', 80),
        'secondaryLabel': ('etiqueta_secundario', 80),
        'coverPhrase': ('frase_portada', 255),
        'generalMessage': ('mensaje_general', None),
        'invitationTitle': ('titulo_invitacion', 120),
        'invitationText': ('texto_invitacion', None),
        'detailsTitle': ('titulo_detalles', 120),
        'detailsText': ('texto_detalles', None),
        'rsvpTitle': ('titulo_rsvp', 120),
        'rsvpText': ('texto_rsvp', None),
        'ceremonyPlace': ('lugar_misa', 200),
        'ceremonyAddress': ('direccion_ceremonia', 255),
        'ceremonyMapUrl': ('link_mapa_misa', 200),
        'receptionPlace': ('lugar_fiesta', 200),
        'receptionAddress': ('direccion_recepcion', 255),
        'receptionMapUrl': ('link_mapa_fiesta', 200),
        'dressCode': ('dress_code', 150),
        'dressCodeText': ('dress_code_descripcion', None),
        'sharedAlbumTitle': ('titulo_album_compartido', 120),
        'sharedAlbumText': ('texto_album_compartido', None),
        'sharedAlbumUrl': ('link_album_compartido', 200),
    }
    for key, (campo, max_length) in campos.items():
        if key in payload:
            valor = limpiar_json_texto(payload, key, max_length)
            if campo in {'mapa_misa_embed', 'mapa_fiesta_embed'}:
                valor = google_maps_src(valor)
            setattr(evento, campo, valor or None)

    if 'ceremonyMapEmbed' in payload:
        evento.mapa_misa_embed = google_maps_src(limpiar_json_texto(payload, 'ceremonyMapEmbed'))
    if 'receptionMapEmbed' in payload:
        evento.mapa_fiesta_embed = google_maps_src(limpiar_json_texto(payload, 'receptionMapEmbed'))
    if 'ceremonyDate' in payload:
        evento.fecha_misa = fecha_hora_editor(payload.get('ceremonyDate'), evento.fecha_misa)
    if 'receptionDate' in payload:
        evento.fecha_fiesta = fecha_hora_editor(payload.get('receptionDate'), evento.fecha_fiesta)

    evento.mostrar_nombre_secundario = bool(payload.get('showSecondaryName'))
    evento.mostrar_album = bool(payload.get('showAlbum'))
    evento.mostrar_menu = bool(payload.get('showMenu'))
    evento.mostrar_regalos = bool(payload.get('showGifts'))
    evento.mostrar_mapa = bool(payload.get('showMaps'))
    evento.mostrar_album_compartido = bool(payload.get('showSharedAlbum'))
    evento.save()

    sincronizar_secciones_invitacion(evento)
    registrar_auditoria(
        usuario=request.user,
        empresa=evento.empresa,
        evento=evento,
        accion='GUARDAR_CONTENIDO_EDITOR_INVITACION',
        modelo='EventoBoda',
        objeto_id=evento.id,
        descripcion='Actualizo contenido rapido desde el editor visual.',
        request=request,
    )
    return JsonResponse({'ok': True, 'content': contenido_editor_payload(evento)})


@login_required(login_url=LOGIN_DASHBOARD_URL)
@require_POST
def guardar_item_contenido_invitacion_visual(request, evento_id):
    evento = get_object_or_404(eventos_visibles_usuario(request.user), id=evento_id)
    try:
        payload = json.loads(request.body.decode('utf-8') or '{}')
    except json.JSONDecodeError:
        return JsonResponse({'ok': False, 'error': 'Contenido invalido.'}, status=400)

    collection = payload.get('collection')
    action = payload.get('action') or 'save'
    item_id = convertir_entero(payload.get('id'), 0)

    if collection == 'people':
        if action == 'delete':
            get_object_or_404(PersonaCeremonia, evento=evento, id=item_id).delete()
        else:
            seccion = payload.get('section') if payload.get('section') in dict(PersonaCeremonia.SECCIONES) else 'PADRINOS'
            nombre = limpiar_json_texto(payload, 'name', 120)
            if not nombre:
                return JsonResponse({'ok': False, 'error': 'El nombre es obligatorio.'}, status=400)
            persona = PersonaCeremonia.objects.filter(evento=evento, id=item_id).first() if item_id else PersonaCeremonia(evento=evento)
            persona.seccion = seccion
            persona.etiqueta = limpiar_json_texto(payload, 'label', 80) or 'Nombre'
            persona.nombre = nombre
            persona.orden = convertir_entero(payload.get('order'), persona.orden if persona.pk else 0)
            persona.visible = bool(payload.get('visible', True))
            persona.save()
    elif collection == 'gifts':
        if action == 'delete':
            get_object_or_404(EnlaceRegalo, evento=evento, id=item_id).delete()
        else:
            tipo = payload.get('type') if payload.get('type') in dict(EnlaceRegalo.TIPOS) else 'TIENDA'
            nombre = limpiar_json_texto(payload, 'name', 100) or ('Deposito bancario' if tipo == 'DEPOSITO' else 'Mesa de regalos')
            regalo = EnlaceRegalo.objects.filter(evento=evento, id=item_id).first() if item_id else EnlaceRegalo(evento=evento)
            regalo.tipo = tipo
            regalo.nombre = nombre
            regalo.url = limpiar_json_texto(payload, 'url', 200) or None
            regalo.banco = limpiar_json_texto(payload, 'bank', 100) or None
            regalo.titular = limpiar_json_texto(payload, 'holder', 120) or None
            regalo.numero_cuenta = limpiar_json_texto(payload, 'account', 60) or None
            regalo.clabe = limpiar_json_texto(payload, 'clabe', 40) or None
            regalo.instrucciones = limpiar_json_texto(payload, 'instructions') or None
            regalo.visible = bool(payload.get('visible', True))
            regalo.save()
    elif collection == 'itinerary':
        if action == 'delete':
            get_object_or_404(ItinerarioEvento, evento=evento, id=item_id).delete()
        else:
            titulo = limpiar_json_texto(payload, 'title', 120)
            hora = payload.get('time')
            if not titulo or not hora:
                return JsonResponse({'ok': False, 'error': 'Hora y titulo son obligatorios.'}, status=400)
            item = ItinerarioEvento.objects.filter(evento=evento, id=item_id).first() if item_id else ItinerarioEvento(evento=evento)
            item.hora = hora
            item.titulo = titulo
            item.descripcion = limpiar_json_texto(payload, 'description') or None
            item.icono = payload.get('icon') or 'general'
            item.orden = convertir_entero(payload.get('order'), item.orden if item.pk else 0)
            item.visible = bool(payload.get('visible', True))
            item.save()
    else:
        return JsonResponse({'ok': False, 'error': 'Coleccion no permitida.'}, status=400)

    registrar_auditoria(
        usuario=request.user,
        empresa=evento.empresa,
        evento=evento,
        accion='GUARDAR_ITEM_CONTENIDO_EDITOR_INVITACION',
        modelo=collection,
        objeto_id=item_id or None,
        descripcion=f'Actualizo {collection} desde el editor visual.',
        request=request,
    )
    return JsonResponse({'ok': True, 'content': contenido_editor_payload(evento)})


@login_required(login_url=LOGIN_DASHBOARD_URL)
@require_POST
def guardar_grupo_invitado_visual(request, evento_id):
    evento = get_object_or_404(eventos_visibles_usuario(request.user), id=evento_id)
    try:
        payload = json.loads(request.body.decode('utf-8') or '{}')
    except json.JSONDecodeError:
        return JsonResponse({'ok': False, 'error': 'Solicitud invalida.'}, status=400)

    action = payload.get('action') or 'save'
    group_id = convertir_entero(payload.get('id'), 0)
    if action == 'delete':
        get_object_or_404(Grupoinvitacion, evento=evento, id=group_id).delete()
        return JsonResponse({'ok': True, 'guests': invitados_editor_payload(evento, request)})

    nombre = limpiar_json_texto(payload, 'name', 100)
    if not nombre:
        return JsonResponse({'ok': False, 'error': 'El nombre del invitado o familia es obligatorio.'}, status=400)
    tipo = payload.get('type') if payload.get('type') in dict(Grupoinvitacion.TIPO_INVITACION) else 'PERSONAL'
    grupo = Grupoinvitacion.objects.filter(evento=evento, id=group_id).first() if group_id else Grupoinvitacion(evento=evento)
    grupo.nombre_grupo = nombre
    grupo.tipo = tipo
    grupo.cantidad_extra_permitida = convertir_entero(payload.get('extraAllowed'), grupo.cantidad_extra_permitida if grupo.pk else 0)
    grupo.cantidad_maxima = max(convertir_entero(payload.get('maxGuests'), grupo.cantidad_maxima if grupo.pk else 1), 1)
    grupo.telefono_contacto = limpiar_json_texto(payload, 'phone', 20) or None
    grupo.correo_contacto = limpiar_json_texto(payload, 'email', 200) or None
    grupo.mesa = limpiar_json_texto(payload, 'tableName', 50) or None
    grupo.save()

    if grupo.es_familiar and payload.get('familyGuests') and not group_id:
        crear_invitados_desde_textarea(grupo, payload.get('familyGuests', ''))
    if grupo.es_personal:
        sincronizar_acompanantes_personales(grupo)
        try:
            asignar_mesa_a_grupo_personal(grupo, payload.get('tableId'))
        except ValidationError as exc:
            return JsonResponse({'ok': False, 'error': '; '.join(exc.messages)}, status=400)

    registrar_auditoria(
        usuario=request.user,
        empresa=evento.empresa,
        evento=evento,
        accion='GUARDAR_GRUPO_EDITOR_INVITACION',
        modelo='Grupoinvitacion',
        objeto_id=grupo.id,
        descripcion=f'Actualizo grupo desde editor visual: {grupo.nombre_grupo}.',
        request=request,
    )
    return JsonResponse({'ok': True, 'guests': invitados_editor_payload(evento, request)})


@login_required(login_url=LOGIN_DASHBOARD_URL)
@require_POST
def guardar_invitado_visual(request, evento_id):
    evento = get_object_or_404(eventos_visibles_usuario(request.user), id=evento_id)
    try:
        payload = json.loads(request.body.decode('utf-8') or '{}')
    except json.JSONDecodeError:
        return JsonResponse({'ok': False, 'error': 'Solicitud invalida.'}, status=400)

    action = payload.get('action') or 'save'
    invitado_id = convertir_entero(payload.get('id'), 0)
    if action == 'delete':
        get_object_or_404(Invitado, grupo__evento=evento, id=invitado_id).delete()
        return JsonResponse({'ok': True, 'guests': invitados_editor_payload(evento, request)})

    grupo = get_object_or_404(Grupoinvitacion, evento=evento, id=payload.get('groupId'))
    nombre = limpiar_json_texto(payload, 'name', 100)
    if not nombre:
        return JsonResponse({'ok': False, 'error': 'El nombre del invitado es obligatorio.'}, status=400)
    invitado = Invitado.objects.filter(grupo=grupo, id=invitado_id).first() if invitado_id else Invitado(grupo=grupo)
    invitado.nombre = nombre
    invitado.apellidos = limpiar_json_texto(payload, 'lastName', 120) or None
    invitado.tipo_persona = payload.get('type') if payload.get('type') in dict(Invitado.TIPO_PERSONA) else 'ADULTO'
    invitado.telefono = limpiar_json_texto(payload, 'phone', 30) or None
    invitado.correo = limpiar_json_texto(payload, 'email', 200) or None
    invitado.mesa = limpiar_json_texto(payload, 'tableName', 50) or None
    invitado.orden = convertir_entero(payload.get('order'), invitado.orden if invitado.pk else 0)
    invitado.alergias = limpiar_json_texto(payload, 'allergies') or None
    invitado.restricciones_alimentarias = limpiar_json_texto(payload, 'restrictions') or None
    invitado.menu_infantil = bool(payload.get('menuInfantil'))
    invitado.save()
    if grupo.es_personal:
        grupo.cantidad_extra_permitida = max(grupo.cantidad_extra_permitida, grupo.invitados.count())
        grupo.save(update_fields=['cantidad_extra_permitida'])
    try:
        asignar_mesa_a_invitado(invitado, payload.get('tableId'))
    except ValidationError as exc:
        return JsonResponse({'ok': False, 'error': '; '.join(exc.messages)}, status=400)

    registrar_auditoria(
        usuario=request.user,
        empresa=evento.empresa,
        evento=evento,
        accion='GUARDAR_INVITADO_EDITOR_INVITACION',
        modelo='Invitado',
        objeto_id=invitado.id,
        descripcion=f'Actualizo invitado desde editor visual: {invitado}.',
        request=request,
    )
    return JsonResponse({'ok': True, 'guests': invitados_editor_payload(evento, request)})


@login_required(login_url=LOGIN_DASHBOARD_URL)
@require_POST
def importar_invitados_visual(request, evento_id):
    evento = get_object_or_404(eventos_visibles_usuario(request.user), id=evento_id)
    archivo = request.FILES.get('archivo')
    if not archivo:
        return JsonResponse({'ok': False, 'error': 'Sube un archivo Excel o CSV.'}, status=400)
    nombre = (archivo.name or '').lower()
    if not nombre.endswith(('.xlsx', '.csv')):
        return JsonResponse({'ok': False, 'error': 'Formato no soportado. Usa .xlsx o .csv.'}, status=400)
    try:
        filas = filas_importadas_invitados(archivo)
        creados, actualizados = importar_invitados_desde_filas(evento, filas)
    except Exception as exc:
        return JsonResponse({'ok': False, 'error': f'No se pudo importar la lista: {exc}'}, status=400)
    registrar_auditoria(
        usuario=request.user,
        empresa=evento.empresa,
        evento=evento,
        accion='IMPORTAR_INVITADOS_EDITOR_INVITACION',
        modelo='Grupoinvitacion',
        descripcion=f'Importo invitados desde archivo. Creados: {creados}. Actualizados: {actualizados}.',
        request=request,
    )
    return JsonResponse({
        'ok': True,
        'message': f'Importacion lista: {creados} nuevo(s), {actualizados} actualizado(s).',
        'guests': invitados_editor_payload(evento, request),
    })


@login_required(login_url=LOGIN_DASHBOARD_URL)
@require_POST
def asignar_asset_invitacion_visual(request, evento_id):
    evento = get_object_or_404(eventos_visibles_usuario(request.user), id=evento_id)
    diseno = obtener_diseno_invitacion(evento, request.user)
    try:
        payload = json.loads(request.body.decode('utf-8') or '{}')
    except json.JSONDecodeError:
        return JsonResponse({'ok': False, 'error': 'Solicitud invalida.'}, status=400)

    asset = get_object_or_404(AssetInvitacion, evento=evento, id=payload.get('assetId'), visible=True)
    destino = payload.get('destino')
    config = normalizar_configuracion_editor(evento, diseno.configuracion_borrador or construir_configuracion_diseno(evento))
    asset_ref = ref_asset_editor(asset)

    theme_destinos = {
        'PORTADA': 'coverAsset',
        'CEREMONIA': 'ceremonyAsset',
        'RECEPCION': 'receptionAsset',
        'DRESS_PERMITIDO': 'dressAllowedAsset',
        'DRESS_PROHIBIDO': 'dressBlockedAsset',
    }
    if destino in theme_destinos:
        config['theme'][theme_destinos[destino]] = asset_ref
    elif destino == 'ALBUM':
        existentes = config['theme'].get('albumAssets') if isinstance(config['theme'].get('albumAssets'), list) else []
        if not any(item.get('id') == asset.id for item in existentes if isinstance(item, dict)):
            existentes.append(asset_ref)
        config['theme']['albumAssets'] = existentes[:80]
    elif destino in {'FONDO_SECCION', 'TITULO_SECCION'}:
        seccion_id = convertir_entero(payload.get('sectionId'), 0)
        seccion_objetivo = None
        for item in config.get('sections', []):
            if item.get('sectionId') == seccion_id:
                item_config = item.setdefault('config', {})
                item_config['backgroundAsset' if destino == 'FONDO_SECCION' else 'titleAsset'] = asset_ref
                if destino == 'FONDO_SECCION':
                    item_config['showBackgroundLayer'] = True
                else:
                    item_config['showTitleAsset'] = True
                    item_config['layoutMode'] = payload.get('layoutMode') or 'full-image'
                    item_config['keepRealContent'] = bool(
                        payload.get('keepRealContent', True)
                    )
                    item_config['showTextTitle'] = bool(
                        payload.get('showTextTitle', False)
                    )

                seccion_objetivo = SeccionInvitacion.objects.filter(
                    evento=evento,
                    id=seccion_id,
                ).first()

                break
        else:
            return JsonResponse({'ok': False, 'error': 'Selecciona una seccion valida.'}, status=400)
        if seccion_objetivo:
            if destino == 'FONDO_SECCION':
                seccion_objetivo.fondo = asset.archivo.name
                seccion_objetivo.save(update_fields=['fondo'])

            else:
                seccion_objetivo.imagen_titulo = asset.archivo.name
                seccion_objetivo.save(update_fields=['imagen_titulo'])

                # La sección PORTADA también alimenta la portada global del evento.
                if seccion_objetivo.tipo == 'PORTADA':
                    evento.foto_portada = asset.archivo.name
                    evento.save(update_fields=['foto_portada'])
    else:
        return JsonResponse({'ok': False, 'error': 'Destino no permitido.'}, status=400)

    diseno.configuracion_borrador = normalizar_configuracion_editor(evento, config)
    diseno.estado = 'BORRADOR' if not diseno.tiene_publicacion else diseno.estado
    diseno.actualizado_por = request.user
    diseno.save(update_fields=['configuracion_borrador', 'estado', 'actualizado_por', 'fecha_actualizacion'])
    registrar_auditoria(
        usuario=request.user,
        empresa=evento.empresa,
        evento=evento,
        accion='ASIGNAR_ASSET_EDITOR_INVITACION',
        modelo='AssetInvitacion',
        objeto_id=asset.id,
        descripcion=f'Asigno asset {asset.titulo or asset.id} a {destino}.',
        request=request,
    )
    return JsonResponse({'ok': True, 'config': diseno.configuracion_borrador})


@login_required(login_url=LOGIN_DASHBOARD_URL)
@require_POST
def eliminar_asset_invitacion_visual(request, evento_id):
    evento = get_object_or_404(eventos_visibles_usuario(request.user), id=evento_id)
    try:
        payload = json.loads(request.body.decode('utf-8') or '{}')
    except json.JSONDecodeError:
        return JsonResponse({'ok': False, 'error': 'Solicitud invalida.'}, status=400)
    asset = get_object_or_404(AssetInvitacion, evento=evento, id=payload.get('assetId'))
    asset.visible = False
    asset.save(update_fields=['visible'])
    registrar_auditoria(
        usuario=request.user,
        empresa=evento.empresa,
        evento=evento,
        accion='ELIMINAR_ASSET_EDITOR_INVITACION',
        modelo='AssetInvitacion',
        objeto_id=asset.id,
        descripcion=f'Elimino asset del editor: {asset.titulo or asset.id}.',
        request=request,
    )
    return JsonResponse({'ok': True, 'assetId': asset.id})


@login_required(login_url=LOGIN_DASHBOARD_URL)
def calendario_operativo(request):
    evento, eventos = obtener_evento_dashboard(request)
    context = {
        'evento': evento,
        'eventos': eventos,
        'calendar_events_url': f'/api/calendario/eventos/?evento={evento.id}' if evento else '',
        'es_dirtec': usuario_es_dirtec(request.user),
    }
    return render(request, 'invitaciones/calendario_operativo.html', context)


@login_required(login_url=LOGIN_DASHBOARD_URL)
def calendario_eventos_json(request):
    evento, _ = obtener_evento_dashboard(request)
    eventos_calendario = []

    if not evento:
        return JsonResponse(eventos_calendario, safe=False)

    for actividad in ActividadItinerario.objects.filter(evento=evento).select_related('proveedor', 'responsable'):
        inicio = datetime.combine(actividad.fecha, actividad.hora_inicio)
        fin = datetime.combine(actividad.fecha, actividad.hora_fin) if actividad.hora_fin else None
        eventos_calendario.append({
            'id': f'actividad-{actividad.id}',
            'title': actividad.titulo,
            'start': inicio.isoformat(),
            'end': fin.isoformat() if fin else None,
            'url': enlace_operativo_calendario(request, evento, f'/admin/itinerario/actividaditinerario/{actividad.id}/change/'),
            'backgroundColor': color_evento_calendario(actividad.estado, actividad.prioridad),
            'borderColor': color_evento_calendario(actividad.estado, actividad.prioridad),
            'extendedProps': {
                'tipo': 'Actividad',
                'estado': actividad.get_estado_display(),
                'categoria': actividad.get_categoria_display(),
                'ubicacion': actividad.ubicacion or '',
                'responsable': str(actividad.responsable) if actividad.responsable else '',
                'proveedor': actividad.proveedor.nombre_comercial if actividad.proveedor else '',
            },
        })

    for tarea in TareaEvento.objects.filter(evento=evento).exclude(fecha_limite__isnull=True):
        eventos_calendario.append({
            'id': f'tarea-{tarea.id}',
            'title': f'Tarea: {tarea.titulo}',
            'start': tarea.fecha_limite.isoformat(),
            'url': enlace_operativo_calendario(request, evento, f'/admin/tareas/tareaevento/{tarea.id}/change/'),
            'backgroundColor': '#9b4d36' if tarea.esta_vencida else '#d2b074',
            'borderColor': '#9b4d36' if tarea.esta_vencida else '#d2b074',
            'extendedProps': {
                'tipo': 'Tarea',
                'estado': tarea.get_estado_display(),
                'categoria': tarea.get_categoria_display(),
                'ubicacion': '',
                'responsable': str(tarea.responsable) if tarea.responsable else '',
                'proveedor': '',
            },
        })

    for gasto in GastoEvento.objects.filter(evento=evento).exclude(fecha_limite__isnull=True).select_related('categoria', 'proveedor'):
        eventos_calendario.append({
            'id': f'gasto-{gasto.id}',
            'title': f'Pago: {gasto.concepto}',
            'start': gasto.fecha_limite.isoformat(),
            'url': enlace_operativo_calendario(request, evento, f'/admin/presupuesto/gastoevento/{gasto.id}/change/'),
            'backgroundColor': '#9b4d36' if gasto.esta_vencido else '#52627d',
            'borderColor': '#9b4d36' if gasto.esta_vencido else '#52627d',
            'extendedProps': {
                'tipo': 'Pago',
                'estado': gasto.get_estado_display(),
                'categoria': gasto.categoria.nombre,
                'ubicacion': '',
                'responsable': '',
                'proveedor': gasto.proveedor.nombre_comercial if gasto.proveedor else '',
            },
        })

    return JsonResponse(eventos_calendario, safe=False)


def color_evento_calendario(estado, prioridad):
    if estado in {'COMPLETADA', 'CANCELADA'}:
        return '#93a79b'
    if estado == 'RETRASADA' or prioridad == 'URGENTE':
        return '#9b4d36'
    if prioridad == 'ALTA':
        return '#d2b074'
    if estado in {'CONFIRMADA', 'EN_PROGRESO'}:
        return '#2f7a4d'
    return '#52627d'


@login_required(login_url=LOGIN_DASHBOARD_URL)
def mesas_visual(request):
    evento, eventos = obtener_evento_dashboard(request)
    if request.method == 'POST':
        evento = get_object_or_404(eventos_visibles_usuario(request.user), id=request.POST.get('evento_id'))
        accion = request.POST.get('accion')
        tipos_mesa_validos = {valor for valor, _ in Mesa.TIPOS}
        tipo_mesa = request.POST.get('tipo_mesa')
        if tipo_mesa not in tipos_mesa_validos:
            tipo_mesa = 'REDONDA'

        if accion == 'crear_mesa':
            Mesa.objects.create(
                evento=evento,
                nombre=limpiar_texto(request, 'nombre_mesa') or 'Mesa',
                numero=convertir_entero(request.POST.get('numero_mesa'), 0) or None,
                tipo=tipo_mesa,
                capacidad=max(convertir_entero(request.POST.get('capacidad_mesa'), 10), 1),
                zona=limpiar_texto(request, 'zona_mesa'),
                notas=limpiar_texto(request, 'notas_mesa'),
            )
            messages.success(request, 'Mesa creada.')
        elif accion == 'editar_mesa':
            mesa = get_object_or_404(Mesa, evento=evento, id=request.POST.get('mesa_id'))
            mesa.nombre = limpiar_texto(request, 'nombre_mesa') or mesa.nombre
            mesa.numero = convertir_entero(request.POST.get('numero_mesa'), 0) or None
            mesa.tipo = tipo_mesa
            mesa.capacidad = max(convertir_entero(request.POST.get('capacidad_mesa'), mesa.capacidad), 1)
            mesa.zona = limpiar_texto(request, 'zona_mesa')
            mesa.notas = limpiar_texto(request, 'notas_mesa')
            mesa.save()
            messages.success(request, 'Mesa actualizada.')
        elif accion == 'eliminar_mesa':
            mesa = get_object_or_404(Mesa, evento=evento, id=request.POST.get('mesa_id'))
            nombre = mesa.nombre
            mesa.delete()
            messages.success(request, f'Mesa eliminada: {nombre}.')
        elif accion == 'asignar_mesa':
            mesa = get_object_or_404(Mesa, evento=evento, id=request.POST.get('mesa_id'))
            invitado_id = request.POST.get('invitado_id')
            grupo_id = request.POST.get('grupo_id')
            try:
                if invitado_id:
                    invitado = get_object_or_404(Invitado, id=invitado_id, grupo__evento=evento)
                    AsignacionMesa.objects.create(
                        mesa=mesa,
                        invitado=invitado,
                        numero_asiento=convertir_entero(request.POST.get('numero_asiento'), 0) or None,
                        notas=limpiar_texto(request, 'notas_asignacion'),
                    )
                elif grupo_id:
                    grupo = get_object_or_404(Grupoinvitacion, id=grupo_id, evento=evento, tipo='PERSONAL')
                    AsignacionMesa.objects.create(
                        mesa=mesa,
                        grupo_invitacion=grupo,
                        numero_asiento=convertir_entero(request.POST.get('numero_asiento'), 0) or None,
                        notas=limpiar_texto(request, 'notas_asignacion'),
                    )
                messages.success(request, 'Asignación guardada.')
            except ValidationError as exc:
                messages.error(request, ' '.join(exc.messages))
        elif accion == 'eliminar_asignacion':
            asignacion = get_object_or_404(AsignacionMesa, id=request.POST.get('asignacion_id'), mesa__evento=evento)
            asignacion.delete()
            messages.success(request, 'Asignación eliminada.')

        return redirect(f'/dashboard/mesas/?evento={evento.id}')

    mesas = (
        Mesa.objects.filter(evento=evento)
        .select_related('evento', 'mesero')
        .prefetch_related('asignaciones__invitado', 'asignaciones__grupo_invitacion')
        .order_by('numero', 'nombre')
    ) if evento else []
    invitados_sin_mesa = Invitado.objects.none()
    grupos_personales_sin_mesa = Grupoinvitacion.objects.none()
    if evento:
        invitados_sin_mesa = Invitado.objects.filter(grupo__evento=evento).filter(asignaciones_mesa__isnull=True).order_by('grupo__nombre_grupo', 'orden', 'nombre')
        grupos_personales_sin_mesa = Grupoinvitacion.objects.filter(evento=evento, tipo='PERSONAL', asignaciones_mesa__isnull=True).order_by('nombre_grupo')

    context = {
        'evento': evento,
        'eventos': eventos,
        'mesas': mesas,
        'tipos_mesa': Mesa.TIPOS,
        'invitados_sin_mesa': invitados_sin_mesa,
        'grupos_personales_sin_mesa': grupos_personales_sin_mesa,
        'es_dirtec': usuario_es_dirtec(request.user),
    }
    return render(request, 'invitaciones/mesas_visual.html', context)


@require_POST
@login_required(login_url=LOGIN_DASHBOARD_URL)
def guardar_posiciones_mesas(request):
    evento = get_object_or_404(eventos_visibles_usuario(request.user), id=request.POST.get('evento_id'))
    try:
        posiciones = json.loads(request.POST.get('posiciones', '[]'))
    except json.JSONDecodeError:
        return JsonResponse({'ok': False, 'error': 'Datos invalidos'}, status=400)

    mesas_actualizadas = 0
    for item in posiciones:
        mesa_id = item.get('id')
        if not mesa_id:
            continue

        mesa = Mesa.objects.filter(id=mesa_id, evento=evento).first()
        if not mesa:
            continue

        mesa.posicion_x = convertir_entero(item.get('x'), mesa.posicion_x)
        mesa.posicion_y = convertir_entero(item.get('y'), mesa.posicion_y)
        mesa.ancho = max(convertir_entero(item.get('ancho'), mesa.ancho), 90)
        mesa.alto = max(convertir_entero(item.get('alto'), mesa.alto), 90)
        mesa.save(update_fields=['posicion_x', 'posicion_y', 'ancho', 'alto'])
        mesas_actualizadas += 1

    return JsonResponse({'ok': True, 'mesas_actualizadas': mesas_actualizadas})


def guardar_personalizacion_evento(request, evento):
    campos_texto = [
        'paleta_colores',
        'paleta_sobre',
        'estilo_letra',
        'tipo_evento',
        'estado',
        'nombre_evento',
        'nombre_principal',
        'nombre_secundario',
        'etiqueta_principal',
        'etiqueta_secundario',
        'frase_portada',
        'titulo_invitacion',
        'texto_invitacion',
        'titulo_cuenta_regresiva',
        'titulo_detalles',
        'texto_detalles',
        'titulo_album',
        'titulo_menu',
        'titulo_regalos',
        'titulo_rsvp',
        'texto_rsvp',
        'lugar_misa',
        'direccion_ceremonia',
        'link_mapa_misa',
        'mapa_misa_embed',
        'lugar_fiesta',
        'direccion_recepcion',
        'link_mapa_fiesta',
        'mapa_fiesta_embed',
        'link_whatsapp',
        'dress_code',
        'dress_code_descripcion',
        'monograma_sobre',
        'texto_boton_sobre',
        'titulo_album_compartido',
        'texto_album_compartido',
        'link_album_compartido',
    ]
    campos_archivo = [
        'foto_portada',
        'foto_ceremonia',
        'foto_recepcion',
        'logo_portada',
        'sello_sobre',
        'cancion',
        'dress_code_permitido_imagen',
        'dress_code_prohibido_imagen',
        'fondo_invitacion',
        'fondo_cuenta_regresiva',
        'fondo_detalles',
        'fondo_album',
        'fondo_menu',
        'fondo_regalos',
        'fondo_rsvp',
    ]

    evento.mostrar_album_compartido = request.POST.get('mostrar_album_compartido') == 'on'
    evento.mostrar_nombre_secundario = request.POST.get('mostrar_nombre_secundario') == 'on'
    evento.mostrar_album = request.POST.get('mostrar_album') == 'on'
    evento.mostrar_menu = request.POST.get('mostrar_menu') == 'on'
    evento.mostrar_regalos = request.POST.get('mostrar_regalos') == 'on'
    evento.mostrar_mapa = request.POST.get('mostrar_mapa') == 'on'
    empresa_id = request.POST.get('empresa_id')
    sede_id = request.POST.get('sede_id')
    if empresa_id:
        evento.empresa = empresa_autorizada_para_evento(request, evento, empresa_id)
    if sede_id:
        evento.sede = get_object_or_404(SedeEvento, id=sede_id, empresa=evento.empresa)
    elif 'sede_id' in request.POST:
        evento.sede = None
    if 'capacidad_contratada' in request.POST:
        evento.capacidad_contratada = convertir_entero(request.POST.get('capacidad_contratada'), 0)
    if 'precio_por_persona' in request.POST:
        evento.precio_por_persona = convertir_decimal(request.POST.get('precio_por_persona'), 0)

    for campo in campos_texto:
        if campo in request.POST:
            valor = request.POST.get(campo)
            defaults = {
                'frase_portada': 'Nuestra celebracion',
                'titulo_invitacion': 'Tu invitacion',
                'texto_invitacion': 'Hemos reservado este espacio para celebrar juntos este dia tan especial.',
                'titulo_cuenta_regresiva': 'Faltan',
                'titulo_detalles': 'Detalles del evento',
                'texto_detalles': 'Aqui tienes ceremonia, fiesta, ubicacion y mapas en un solo lugar.',
                'titulo_album': 'Album',
                'titulo_menu': 'Menu',
                'titulo_regalos': 'Regalos',
                'titulo_rsvp': 'Confirma tu asistencia',
                'texto_rsvp': 'Tu respuesta nos ayuda a organizar lugares, mesas y buffet.',
                'lugar_misa': 'Ceremonia por confirmar',
                'lugar_fiesta': 'Recepcion por confirmar',
            }
            if campo in defaults:
                valor = valor or defaults[campo]
            if campo == 'texto_boton_sobre':
                valor = valor or 'Abrir invitación'
            if campo == 'titulo_album_compartido':
                valor = valor or 'Comparte tus fotos'
            if campo == 'texto_album_compartido':
                valor = valor or 'Ayúdanos a guardar tus mejores momentos. Sube tus fotos y videos al álbum compartido.'
            if campo in {'mapa_misa_embed', 'mapa_fiesta_embed'}:
                valor = google_maps_src(valor)
            setattr(evento, campo, valor or None)

    for campo in campos_archivo:
        if request.POST.get(f'eliminar_{campo}') == 'on':
            archivo_actual = getattr(evento, campo, None)
            if archivo_actual:
                archivo_actual.delete(save=False)
            setattr(evento, campo, None)

    for campo in campos_archivo:
        archivo = request.FILES.get(campo)
        if archivo:
            if not archivo_pasa_validadores(EventoBoda, campo, archivo):
                continue
            setattr(evento, campo, archivo)

    plantilla_evento = request.POST.get('plantilla_evento')
    aplicar_plantilla_evento(evento, plantilla_evento)
    evento.save()
    aplicar_estructura_plantilla_evento(evento, plantilla_evento)

    if evento.mostrar_album_compartido:
        SeccionInvitacion.objects.update_or_create(
            evento=evento,
            tipo='ALBUM_COMPARTIDO',
            defaults={
                'titulo': evento.titulo_album_compartido,
                'descripcion': evento.texto_album_compartido,
                'orden': SECCIONES_INVITACION_DEFAULTS['ALBUM_COMPARTIDO']['orden'],
                'activa': True,
            },
        )


def agregar_regalo_dashboard(request, evento):
    tipo = request.POST.get('tipo_regalo') or 'TIENDA'
    tiene_datos_bancarios = any(
        request.POST.get(campo)
        for campo in ['banco', 'titular', 'numero_cuenta', 'clabe']
    )
    if tiene_datos_bancarios and not request.POST.get('url_regalo'):
        tipo = 'DEPOSITO'
    nombre = request.POST.get('nombre_regalo') or ('Deposito bancario' if tipo == 'DEPOSITO' else 'Mesa de regalos')
    EnlaceRegalo.objects.create(
        evento=evento,
        tipo=tipo,
        nombre=nombre,
        url=request.POST.get('url_regalo') or None,
        banco=request.POST.get('banco') or None,
        titular=request.POST.get('titular') or None,
        numero_cuenta=request.POST.get('numero_cuenta') or None,
        clabe=request.POST.get('clabe') or None,
        instrucciones=request.POST.get('instrucciones') or None,
        visible=True,
    )


def agregar_album_dashboard(request, evento):
    archivo = request.FILES.get('archivo_album')
    if not archivo:
        return
    if not archivo_pasa_validadores(FotoEvento, 'imagen', archivo):
        return

    FotoEvento.objects.create(
        evento=evento,
        titulo=request.POST.get('titulo_album_media') or None,
        imagen=archivo,
        orden=convertir_entero(request.POST.get('orden_album_media'), 0),
        visible=True,
    )


def agregar_itinerario_dashboard(request, evento):
    hora = request.POST.get('hora_itinerario')
    titulo = request.POST.get('titulo_itinerario')
    if not hora or not titulo:
        return

    ItinerarioEvento.objects.create(
        evento=evento,
        hora=hora,
        titulo=titulo,
        descripcion=request.POST.get('descripcion_itinerario') or None,
        icono=request.POST.get('icono_itinerario') or 'general',
        orden=convertir_entero(request.POST.get('orden_itinerario'), 0),
        visible=True,
    )


def preparar_links_grupo(grupo, base_url):
    link_invitacion = f"{base_url}/invitacion/{grupo.codigo}/"
    saludo = f"Hola {grupo.nombre_grupo}"
    if grupo.es_familiar:
        saludo = f"Hola Familia {grupo.nombre_grupo}"

    mensaje_invitacion = (
        f"{saludo}, te compartimos tu invitación digital.\n\n"
        f"Puedes verla aquí:\n{link_invitacion}"
    )
    mensaje_recordatorio = (
        f"{saludo}, este es un recordatorio de tu invitación digital.\n\n"
        f"Puedes revisarla aquí:\n{link_invitacion}"
    )
    telefono = (grupo.telefono_contacto or "").replace(" ", "").replace("+", "").replace("-", "")

    grupo.link_invitacion = link_invitacion
    grupo.whatsapp_invitacion_url = ""
    grupo.whatsapp_recordatorio_url = ""
    if telefono:
        grupo.whatsapp_invitacion_url = f"https://wa.me/{telefono}?text={quote(mensaje_invitacion)}"
        grupo.whatsapp_recordatorio_url = f"https://wa.me/{telefono}?text={quote(mensaje_recordatorio)}"


@login_required(login_url=LOGIN_DASHBOARD_URL)
def exportar_excel(request):
    evento, _ = obtener_evento_dashboard(request)
    grupos = (
        Grupoinvitacion.objects.filter(evento=evento)
        .prefetch_related('invitados')
        .order_by('nombre_grupo')
    ) if evento else []

    wb = Workbook()
    ws = wb.active
    ws.title = 'Confirmaciones'
    ws.append([
        'Evento',
        'Grupo',
        'Tipo de invitación',
        'Mesa',
        'Persona / acompañantes',
        'Adulto o niño',
        'Asistirá',
        'Comentario',
        'Código',
    ])

    for grupo in grupos:
        if grupo.es_personal:
            ws.append([
                str(evento),
                grupo.nombre_grupo,
                grupo.tipo,
                grupo.mesa or '',
                grupo.nombre_grupo,
                'ADULTO',
                estado_asistencia(grupo.asistira),
                grupo.comentario or '',
                str(grupo.codigo),
            ])
            if grupo.acompanantes_adultos:
                ws.append([str(evento), grupo.nombre_grupo, grupo.tipo, grupo.mesa or '', f'{grupo.acompanantes_adultos} acompañante(s)', 'ADULTO', 'Sí', '', str(grupo.codigo)])
            if grupo.acompanantes_ninos:
                ws.append([str(evento), grupo.nombre_grupo, grupo.tipo, grupo.mesa or '', f'{grupo.acompanantes_ninos} acompañante(s)', 'NINO', 'Sí', '', str(grupo.codigo)])
        else:
            for invitado in grupo.invitados.all():
                ws.append([
                    str(evento),
                    grupo.nombre_grupo,
                    grupo.tipo,
                    invitado.mesa or grupo.mesa or '',
                    invitado.nombre,
                    invitado.tipo_persona,
                    estado_asistencia(invitado.asistira),
                    invitado.comentario or '',
                    str(grupo.codigo),
                ])

    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename=confirmaciones_boda.xlsx'
    wb.save(response)
    return response


@login_required(login_url=LOGIN_DASHBOARD_URL)
def exportar_resumen_evento(request):
    evento, _ = obtener_evento_dashboard(request)
    metricas = construir_metricas_dashboard(evento)

    wb = Workbook()
    ws = wb.active
    ws.title = 'Resumen del evento'

    ws.append(['Evento', metricas['evento']])
    ws.append([])
    ws.append(['Indicador', 'Valor'])
    for clave, valor in metricas['resumen'].items():
        ws.append([clave.replace('_', ' ').title(), valor])

    ws.append([])
    ws.append(['Proveedores'])
    ws.append(['Servicio', 'Proveedor', 'Estado', 'Costo', 'Anticipo', 'Saldo'])
    for servicio in ServicioEvento.objects.filter(evento=evento).select_related('proveedor'):
        ws.append([
            servicio.nombre_servicio,
            servicio.proveedor.nombre_comercial if servicio.proveedor else '',
            servicio.get_estado_display(),
            servicio.costo_total,
            servicio.anticipo,
            servicio.saldo_pendiente,
        ])

    ws.append([])
    ws.append(['Gastos'])
    ws.append(['Concepto', 'Categoria', 'Estado', 'Estimado', 'Real', 'Pagado', 'Saldo', 'Vence'])
    for gasto in GastoEvento.objects.filter(evento=evento).select_related('categoria'):
        ws.append([
            gasto.concepto,
            gasto.categoria.nombre,
            gasto.get_estado_display(),
            gasto.monto_estimado,
            gasto.monto_real,
            gasto.total_pagado,
            gasto.saldo_pendiente,
            gasto.fecha_limite.isoformat() if gasto.fecha_limite else '',
        ])

    ws.append([])
    ws.append(['Tareas'])
    ws.append(['Titulo', 'Categoria', 'Prioridad', 'Estado', 'Avance', 'Vence'])
    for tarea in TareaEvento.objects.filter(evento=evento):
        ws.append([
            tarea.titulo,
            tarea.get_categoria_display(),
            tarea.get_prioridad_display(),
            tarea.get_estado_display(),
            tarea.porcentaje_avance,
            tarea.fecha_limite.isoformat() if tarea.fecha_limite else '',
        ])

    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename=resumen_evento.xlsx'
    wb.save(response)
    return response


def estado_asistencia(valor):
    if valor is True:
        return 'Sí'
    if valor is False:
        return 'No'
    return 'Pendiente'


@login_required(login_url=LOGIN_DASHBOARD_URL)
def marcar_envio_invitacion(request, grupo_id):
    grupo = get_object_or_404(Grupoinvitacion, id=grupo_id, evento__in=eventos_visibles_usuario(request.user))
    grupo.estado_envio = 'INVITACION_PREPARADA'
    grupo.fecha_ultimo_envio = timezone.now()
    grupo.save()
    return redirect(f'/dashboard/?evento={grupo.evento_id}' if grupo.evento_id else 'dashboard')


@login_required(login_url=LOGIN_DASHBOARD_URL)
def marcar_recordatorio(request, grupo_id):
    grupo = get_object_or_404(Grupoinvitacion, id=grupo_id, evento__in=eventos_visibles_usuario(request.user))
    grupo.estado_envio = 'RECORDATORIO_PREPARADO'
    grupo.fecha_ultimo_recordatorio = timezone.now()
    grupo.save()
    return redirect(f'/dashboard/?evento={grupo.evento_id}' if grupo.evento_id else 'dashboard')
