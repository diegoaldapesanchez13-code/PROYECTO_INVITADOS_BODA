from core.services.branding import get_brand_context
from core.services.navigation import build_navigation
from core.services.permisos import empresa_principal_usuario


ROLE_LABELS = {
    "DIRTEC": "DIRTEC",
    "EMPRESA": "Empresa",
    "PLANNER": "Planner",
    "CLIENTE": "Cliente",
    "PROVEEDOR": "Proveedor",
    "SIN_ROL": "Cuenta",
}


def build_app_context(
    request,
    *,
    empresa=None,
    page_title="Inicio",
    section_label="DIRTEC Event Studio",
    active_key="inicio",
):
    """
    Single presentation context for the new K9 app shell.

    It deliberately composes existing tenant/role services instead of creating
    a second authorization system.
    """
    user = request.user
    empresa = empresa or empresa_principal_usuario(user)
    navigation = build_navigation(user, empresa=empresa, active_key=active_key)
    brand_context = get_brand_context(empresa)

    return {
        "empresa": empresa,
        "brand_context": brand_context,
        "navigation": navigation,
        "app_context": {
            "page_title": page_title,
            "section_label": section_label,
            "role": navigation["role"],
            "role_label": ROLE_LABELS.get(navigation["role"], navigation["role"]),
        },
    }
