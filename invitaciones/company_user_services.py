"""Company user/membership operations shared by DIRTEC and company legacy boundaries."""

from core.services.auditoria import registrar_auditoria
from core.services.identity import (
    actualizar_identidad_usuario,
    crear_identidad_usuario,
)
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404
from django.utils.crypto import get_random_string
from organizaciones.models import MembresiaEmpresa
from .shared_dashboard_services import (
    bool_post,
    limpiar_texto,
)

def aplicar_datos_usuario_empresa(
    request,
    user,
    *,
    created=False,
    activar_default=True,
):
    username = (
        limpiar_texto(
            request,
            'username_usuario',
        )
        or user.username
    )
    email = limpiar_texto(
        request,
        'email_usuario',
    )
    phone = limpiar_texto(
        request,
        'telefono_usuario',
    )
    first_name = limpiar_texto(
        request,
        'first_name_usuario',
    )
    last_name = limpiar_texto(
        request,
        'last_name_usuario',
    )

    password = (
        request.POST.get(
            'password_usuario'
        )
        or ''
    ).strip()

    password_generada = None
    if (
        not password
        and (
            created
            or not user.has_usable_password()
        )
    ):
        password_generada = (
            get_random_string(12)
        )
        password = password_generada

    active = (
        bool_post(
            request,
            'activo_usuario',
        )
        if 'activo_usuario'
        in request.POST
        else activar_default
    )

    try:
        actualizar_identidad_usuario(
            user,
            username=username,
            email=email,
            phone=phone,
            first_name=first_name,
            last_name=last_name,
            password=password or None,
            active=active,
        )
    except ValidationError as exc:
        messages.error(
            request,
            '; '.join(exc.messages),
        )
        return None

    if password_generada:
        messages.warning(
            request,
            (
                'Contraseña temporal generada para '
                f'{user.username}: {password_generada}. '
                'Compártela ahora por un canal seguro.'
            ),
        )

    return user

def crear_o_actualizar_usuario_empresa(request, empresa, rol_default='WEDDING_PLANNER'):
    username = limpiar_texto(request, 'username_usuario')
    if not empresa or not username:
        return None

    roles_validos = {valor for valor, _ in MembresiaEmpresa.ROLES}
    rol = request.POST.get('rol_usuario') if request.POST.get('rol_usuario') in roles_validos else rol_default
    User = get_user_model()
    user = User.objects.filter(
        username__iexact=username
    ).first()
    created = False

    if user is None:
        password = (
            request.POST.get(
                'password_usuario'
            )
            or get_random_string(12)
        )
        try:
            user = crear_identidad_usuario(
                username=username,
                email=limpiar_texto(
                    request,
                    'email_usuario',
                ),
                phone=limpiar_texto(
                    request,
                    'telefono_usuario',
                ),
                first_name=limpiar_texto(
                    request,
                    'first_name_usuario',
                ),
                last_name=limpiar_texto(
                    request,
                    'last_name_usuario',
                ),
                password=password,
                active=(
                    bool_post(
                        request,
                        'activo_usuario',
                    )
                    if 'activo_usuario'
                    in request.POST
                    else True
                ),
            )
            created = True
        except ValidationError as exc:
            messages.error(
                request,
                '; '.join(exc.messages),
            )
            return None
    else:
        user = aplicar_datos_usuario_empresa(
            request,
            user,
            created=False,
        )
        if user is None:
            return None

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

def actualizar_usuario_empresa_dashboard(
    request,
    empresa,
):
    membresia = get_object_or_404(
        MembresiaEmpresa.objects.select_related(
            'usuario'
        ),
        empresa=empresa,
        id=request.POST.get(
            'membresia_id'
        ),
    )

    roles_validos = {
        valor
        for valor, _
        in MembresiaEmpresa.ROLES
    }
    rol = (
        request.POST.get(
            'rol_usuario'
        )
        if request.POST.get(
            'rol_usuario'
        ) in roles_validos
        else membresia.rol
    )

    activo = bool_post(
        request,
        'activo_usuario',
    )
    puede_catalogos = bool_post(
        request,
        'puede_gestionar_catalogos_usuario',
    )
    user = membresia.usuario

    try:
        actualizar_identidad_usuario(
            user,
            username=(
                limpiar_texto(
                    request,
                    'username_usuario',
                )
                or user.username
            ),
            email=limpiar_texto(
                request,
                'email_usuario',
            ),
            phone=limpiar_texto(
                request,
                'telefono_usuario',
            ),
            first_name=limpiar_texto(
                request,
                'first_name_usuario',
            ),
            last_name=limpiar_texto(
                request,
                'last_name_usuario',
            ),
            password=(
                request.POST.get(
                    'password_usuario'
                )
                or None
            ),
            active=activo,
        )
    except ValidationError as exc:
        messages.error(
            request,
            '; '.join(exc.messages),
        )
        return membresia

    if rol != membresia.rol:
        destino = (
            MembresiaEmpresa.objects
            .filter(
                empresa=empresa,
                usuario=user,
                rol=rol,
            )
            .exclude(
                id=membresia.id
            )
            .first()
        )
        if destino:
            destino.activo = activo
            destino.puede_gestionar_catalogos = (
                puede_catalogos
            )
            destino.save(
                update_fields=[
                    'activo',
                    'puede_gestionar_catalogos',
                ]
            )
            membresia.activo = False
            membresia.save(
                update_fields=['activo']
            )
            return destino
        membresia.rol = rol

    membresia.activo = activo
    membresia.puede_gestionar_catalogos = (
        puede_catalogos
    )
    membresia.save(
        update_fields=[
            'rol',
            'activo',
            'puede_gestionar_catalogos',
        ]
    )
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
