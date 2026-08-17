from core.services.authorization import Actions, usuario_tiene_permiso
from core.services.permisos import roles_usuario_empresa

from .models import ProveedorServicioCatalogo, ServicioCatalogo


def puede_ver_catalogo(user, empresa):
    roles = roles_usuario_empresa(user, empresa)
    return bool(
        usuario_tiene_permiso(user, Actions.COMPANY_VIEW, empresa=empresa)
        or 'WEDDING_PLANNER' in roles
    )


def puede_gestionar_catalogo(user, empresa):
    return usuario_tiene_permiso(user, Actions.COMPANY_MANAGE_CATALOGS, empresa=empresa)


def relaciones_proveedor_servicio_qs(empresa):
    return ProveedorServicioCatalogo.objects.filter(
        proveedor__empresa=empresa,
        servicio_catalogo__empresa=empresa,
    ).select_related('proveedor', 'servicio_catalogo')


def proveedores_disponibles_para_servicio(servicio_catalogo):
    if not servicio_catalogo or not servicio_catalogo.empresa_id:
        return ProveedorServicioCatalogo.objects.none()
    return relaciones_proveedor_servicio_qs(servicio_catalogo.empresa).filter(
        servicio_catalogo=servicio_catalogo,
        servicio_catalogo__activo=True,
        proveedor__activo=True,
        activo=True,
    )


def servicios_disponibles_para_proveedor(proveedor):
    if not proveedor or not proveedor.empresa_id:
        return ServicioCatalogo.objects.none()
    return ServicioCatalogo.objects.filter(
        proveedores_servicio_catalogo__proveedor=proveedor,
        proveedores_servicio_catalogo__activo=True,
        proveedores_servicio_catalogo__proveedor__activo=True,
        empresa_id=proveedor.empresa_id,
        activo=True,
    ).distinct().order_by('categoria', 'nombre')
