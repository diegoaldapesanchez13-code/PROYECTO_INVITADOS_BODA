"""Central product authorization matrix."""

from organizaciones.models import MembresiaEmpresa


class Actions:
    DJANGO_ADMIN = "django_admin"

    COMPANY_VIEW = "company.view"
    COMPANY_MANAGE_USERS = "company.manage_users"
    COMPANY_MANAGE_CATALOGS = "company.manage_catalogs"

    EVENT_CREATE = "event.create"
    EVENT_VIEW = "event.view"
    EVENT_EDIT = "event.edit"
    EVENT_GUESTS = "event.guests"
    EVENT_TABLES = "event.tables"
    EVENT_BUILDER = "event.builder"
    EVENT_OPERATIONS = "event.operations"

    CLIENT_PORTAL = "client.portal"
    CLIENT_APPROVE = "client.approve"

    PROVIDER_PORTAL = "provider.portal"
    PROVIDER_SERVICE_UPDATE = "provider.service_update"


ROLE_ACTIONS = {
    "ADMIN_EMPRESA": {
        Actions.COMPANY_VIEW,
        Actions.COMPANY_MANAGE_USERS,
        Actions.COMPANY_MANAGE_CATALOGS,
        Actions.EVENT_CREATE,
        Actions.EVENT_VIEW,
        Actions.EVENT_EDIT,
        Actions.EVENT_GUESTS,
        Actions.EVENT_TABLES,
        Actions.EVENT_BUILDER,
        Actions.EVENT_OPERATIONS,
    },
    "VENTAS": {
        Actions.COMPANY_VIEW,
        Actions.EVENT_CREATE,
        Actions.EVENT_VIEW,
        Actions.EVENT_EDIT,
    },
    "WEDDING_PLANNER": {
        Actions.EVENT_CREATE,
        Actions.EVENT_VIEW,
        Actions.EVENT_EDIT,
        Actions.EVENT_GUESTS,
        Actions.EVENT_TABLES,
        Actions.EVENT_BUILDER,
        Actions.EVENT_OPERATIONS,
    },
    "CLIENTE": {
        Actions.CLIENT_PORTAL,
        Actions.CLIENT_APPROVE,
        Actions.EVENT_VIEW,
    },
    "PROVEEDOR": {
        Actions.PROVIDER_PORTAL,
        Actions.PROVIDER_SERVICE_UPDATE,
    },
}


def roles_activos(user, empresa):
    if not (
        getattr(user, "is_authenticated", False)
        and empresa
    ):
        return set()
    return set(
        MembresiaEmpresa.objects.filter(
            usuario=user,
            empresa=empresa,
            activo=True,
        ).values_list("rol", flat=True)
    )


def usuario_tiene_permiso(
    user,
    action,
    *,
    empresa=None,
):
    from core.services.permisos import usuario_es_dirtec_operativo

    if not getattr(user, "is_authenticated", False):
        return False
    if usuario_es_dirtec_operativo(user):
        return True

    roles = roles_activos(user, empresa)

    if action == Actions.COMPANY_MANAGE_CATALOGS:
        if "ADMIN_EMPRESA" in roles:
            return True
        return MembresiaEmpresa.objects.filter(
            usuario=user,
            empresa=empresa,
            activo=True,
            puede_gestionar_catalogos=True,
        ).exists()

    return any(
        action in ROLE_ACTIONS.get(role, set())
        for role in roles
    )


def usuario_puede_evento(
    user,
    evento,
    action=Actions.EVENT_VIEW,
):
    from core.services.permisos import usuario_es_dirtec_operativo

    if not (
        getattr(user, "is_authenticated", False)
        and evento
    ):
        return False
    if usuario_es_dirtec_operativo(user):
        return True

    roles = roles_activos(user, evento.empresa)

    if "ADMIN_EMPRESA" in roles:
        return action in ROLE_ACTIONS["ADMIN_EMPRESA"]

    if "VENTAS" in roles:
        return action in ROLE_ACTIONS["VENTAS"]

    if "WEDDING_PLANNER" in roles:
        return bool(
            evento.wedding_planner_id == user.id
            and action in ROLE_ACTIONS["WEDDING_PLANNER"]
        )

    if (
        action == Actions.EVENT_VIEW
        and evento.clientes.filter(id=user.id).exists()
    ):
        return True

    if (
        action in {
            Actions.PROVIDER_PORTAL,
            Actions.PROVIDER_SERVICE_UPDATE,
        }
        and evento.servicios_contratados.filter(
            proveedor__usuario=user,
            proveedor__activo=True,
        ).exists()
    ):
        return True

    return False
