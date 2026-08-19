from dataclasses import dataclass

from django.urls import reverse

from core.services.permisos import (
    empresa_principal_usuario,
    roles_usuario_empresa,
    usuario_es_dirtec_operativo,
)


@dataclass(frozen=True)
class NavigationItem:
    key: str
    label: str
    url: str
    icon: str = ""
    short_label: str = ""
    active: bool = False
    badge: str = ""

    def as_dict(self):
        return {
            "key": self.key,
            "label": self.label,
            "url": self.url,
            "icon": self.icon,
            "short_label": self.short_label or self.label,
            "active": self.active,
            "badge": self.badge,
        }


def _item(key, label, url, icon="", short_label="", active_key=""):
    return NavigationItem(
        key=key,
        label=label,
        url=url,
        icon=icon,
        short_label=short_label,
        active=(key == active_key),
    ).as_dict()


def _company_navigation(empresa, active_key="inicio"):
    dashboard = reverse("empresa_dashboard", kwargs={"empresa_slug": empresa.slug})
    legacy = reverse("dashboard_empresa") + f"?empresa={empresa.id}"
    return [
        _item("inicio", "Inicio", dashboard, "⌂", active_key=active_key),
        _item("eventos", "Eventos", reverse("k9_evento_list", kwargs={"empresa_slug": empresa.slug}), "◇", active_key=active_key),
        # R3A mantiene temporalmente estos módulos en el dashboard legacy hasta
        # que sus fases específicas los migren a pantallas canónicas.
        _item("clientes", "Clientes", legacy + "#clientes", "◎", active_key=active_key),
        _item("equipo", "Planners", legacy + "#equipo", "◌", active_key=active_key),
        _item("proveedores", "Proveedores", legacy + "#proveedores", "◈", active_key=active_key),
        _item("catalogo", "Catálogo", legacy + "#catalogos", "▦", active_key=active_key),
        _item("configuracion", "Configuración", legacy + "#configuracion", "⚙", active_key=active_key),
    ]


def _planner_navigation(empresa, active_key="inicio"):
    dashboard = reverse("planner_dashboard_empresa_alias", kwargs={"empresa_slug": empresa.slug})
    return [
        _item("inicio", "Inicio", dashboard, "⌂", active_key=active_key),
        _item("eventos", "Mis eventos", reverse("k9_evento_list", kwargs={"empresa_slug": empresa.slug}), "◇", short_label="Eventos", active_key=active_key),
        _item("agenda", "Agenda", dashboard + "#agenda", "◷", active_key=active_key),
        _item("tareas", "Mis tareas", dashboard + "#tareas", "✓", short_label="Tareas", active_key=active_key),
    ]


def _dirtec_navigation(active_key="inicio"):
    dashboard = reverse("dirtec_dashboard")
    return [
        _item("inicio", "Inicio", dashboard + "#resumen", "⌂", active_key=active_key),
        _item("empresas", "Empresas", dashboard + "#empresas", "▣", active_key=active_key),
        _item("usuarios", "Usuarios", dashboard + "#usuarios", "◎", active_key=active_key),
        _item("suscripciones", "Suscripciones", dashboard + "#suscripciones", "◫", active_key=active_key),
        _item("planes", "Planes", dashboard + "#planes", "▤", active_key=active_key),
    ]


def _client_navigation(active_key="inicio"):
    dashboard = reverse("cliente_dashboard")
    return [
        _item("inicio", "Mi evento", dashboard, "⌂", short_label="Inicio", active_key=active_key),
    ]


def _provider_navigation(active_key="inicio"):
    dashboard = reverse("proveedor_dashboard")
    return [
        _item("inicio", "Mis servicios", dashboard, "⌂", short_label="Inicio", active_key=active_key),
    ]


def _mobile_subset(items, keys):
    mapping = {item["key"]: item for item in items}
    return [mapping[key] for key in keys if key in mapping]


def build_navigation(user, *, empresa=None, active_key="inicio"):
    """
    Presentation navigation contract for K9.

    This does not replace authorization. Every destination must continue to
    validate permissions server-side. It only decides which navigation choices
    to render for the current identity.
    """
    if usuario_es_dirtec_operativo(user):
        items = _dirtec_navigation(active_key)
        return {
            "role": "DIRTEC",
            "items": items,
            "mobile_items": _mobile_subset(items, ["inicio", "empresas", "suscripciones"]),
        }

    empresa = empresa or empresa_principal_usuario(user)
    roles = roles_usuario_empresa(user, empresa)

    if "CLIENTE" in roles or getattr(user, "eventos_cliente", None) and user.eventos_cliente.exists():
        items = _client_navigation(active_key)
        return {"role": "CLIENTE", "items": items, "mobile_items": items}

    if "PROVEEDOR" in roles or hasattr(user, "perfil_proveedor"):
        items = _provider_navigation(active_key)
        return {"role": "PROVEEDOR", "items": items, "mobile_items": items}

    if empresa and roles.intersection({"ADMIN_EMPRESA", "VENTAS"}):
        items = _company_navigation(empresa, active_key)
        return {
            "role": "EMPRESA",
            "items": items,
            "mobile_items": _mobile_subset(items, ["inicio", "eventos", "clientes", "proveedores"]),
        }

    if empresa and "WEDDING_PLANNER" in roles:
        items = _planner_navigation(empresa, active_key)
        return {
            "role": "PLANNER",
            "items": items,
            "mobile_items": _mobile_subset(items, ["inicio", "eventos", "agenda", "tareas"]),
        }

    return {
        "role": "SIN_ROL",
        "items": [],
        "mobile_items": [],
    }
