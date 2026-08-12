from django.db.models import Q

from core.services.permisos import usuario_es_dirtec_operativo
from core.services.authorization import Actions, usuario_tiene_permiso
from organizaciones.models import EmpresaSuscriptora, MembresiaEmpresa

from .models import EventoBoda


def usuario_en_grupo(user, nombre_grupo):
    return user.is_authenticated and user.groups.filter(name=nombre_grupo).exists()


def usuario_es_dirtec(user):
    return usuario_es_dirtec_operativo(user)


def empresas_para_usuario(user):
    if not user.is_authenticated:
        return EmpresaSuscriptora.objects.none()
    if usuario_es_dirtec(user):
        return EmpresaSuscriptora.objects.filter(activo=True).order_by('nombre_comercial')
    return EmpresaSuscriptora.objects.filter(
        membresias__usuario=user,
        membresias__activo=True,
        activo=True,
    ).distinct().order_by('nombre_comercial')


def roles_activos_empresa(user, empresa):
    if not user.is_authenticated or not empresa:
        return set()
    return set(
        MembresiaEmpresa.objects.filter(
            usuario=user,
            empresa=empresa,
            activo=True,
        ).values_list('rol', flat=True)
    )


def empresas_ids_por_roles(user, roles):
    if not user.is_authenticated:
        return []
    return list(
        MembresiaEmpresa.objects.filter(
            usuario=user,
            activo=True,
            empresa__activo=True,
            rol__in=roles,
        ).values_list('empresa_id', flat=True)
    )


def usuario_puede_gestionar_catalogos(user, empresa):
    return usuario_tiene_permiso(
        user,
        Actions.COMPANY_MANAGE_CATALOGS,
        empresa=empresa,
    )


def usuario_puede_gestionar_usuarios(user, empresa):
    return usuario_tiene_permiso(
        user,
        Actions.COMPANY_MANAGE_USERS,
        empresa=empresa,
    )


def eventos_visibles_usuario(user):
    eventos = EventoBoda.objects.all().order_by('-activo', '-fecha_fiesta')

    if not user.is_authenticated:
        return EventoBoda.objects.none()

    if usuario_es_dirtec(user):
        return eventos

    empresas_admin = empresas_ids_por_roles(user, ['ADMIN_EMPRESA', 'VENTAS'])
    empresas_planner = empresas_ids_por_roles(user, ['WEDDING_PLANNER'])
    empresas_cliente = empresas_ids_por_roles(user, ['CLIENTE'])
    empresas_proveedor = empresas_ids_por_roles(user, ['PROVEEDOR'])

    filtro = Q(clientes=user)
    if empresas_admin:
        filtro |= Q(empresa_id__in=empresas_admin)
    if empresas_planner:
        filtro |= Q(empresa_id__in=empresas_planner, wedding_planner=user)
    if empresas_cliente:
        filtro |= Q(empresa_id__in=empresas_cliente, clientes=user)
    if empresas_proveedor:
        filtro |= Q(
            empresa_id__in=empresas_proveedor,
            servicios_contratados__proveedor__usuario=user,
        )

    return eventos.filter(filtro).distinct()
