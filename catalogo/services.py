from core.services.authorization import Actions, usuario_tiene_permiso
from core.services.permisos import roles_usuario_empresa


def puede_ver_catalogo(user, empresa):
    roles = roles_usuario_empresa(user, empresa)
    return bool(
        usuario_tiene_permiso(user, Actions.COMPANY_VIEW, empresa=empresa)
        or 'WEDDING_PLANNER' in roles
    )


def puede_gestionar_catalogo(user, empresa):
    return usuario_tiene_permiso(user, Actions.COMPANY_MANAGE_CATALOGS, empresa=empresa)
