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
    return [
        _item("inicio", "Inicio", dashboard, "I", active_key=active_key),
        _item(
            "eventos",
            "Eventos",
            reverse("k9_evento_list", kwargs={"empresa_slug": empresa.slug}),
            "E",
            active_key=active_key,
        ),
        _item(
            "clientes",
            "Clientes",
            reverse("empresa_clientes", kwargs={"empresa_slug": empresa.slug}),
            "C",
            active_key=active_key,
        ),
        _item(
            "equipo",
            "Equipo",
            reverse("empresa_equipo", kwargs={"empresa_slug": empresa.slug}),
            "Eq",
            active_key=active_key,
        ),
        _item(
            "proveedores",
            "Proveedores",
            reverse("empresa_proveedores", kwargs={"empresa_slug": empresa.slug}),
            "P",
            active_key=active_key,
        ),
        _item(
            "catalogo",
            "Catalogo",
            reverse("empresa_catalogo", kwargs={"empresa_slug": empresa.slug}),
            "Ca",
            active_key=active_key,
        ),
        _item(
            "paquetes",
            "Paquetes",
            reverse("paquetes_paquete_list", kwargs={"empresa_slug": empresa.slug}),
            "Pa",
            active_key=active_key,
        ),
        _item(
            "configuracion",
            "Configuracion",
            reverse("empresa_configuracion", kwargs={"empresa_slug": empresa.slug}),
            "Co",
            active_key=active_key,
        ),
    ]


def _company_mobile_navigation(empresa, items, active_key="inicio"):
    mobile_items = _mobile_subset(items, ["inicio", "eventos", "clientes"])
    mobile_items.append(
        NavigationItem(
            key="mas",
            label="Mas",
            url=reverse("empresa_configuracion", kwargs={"empresa_slug": empresa.slug}),
            icon="+",
            short_label="Mas",
            active=active_key in {"equipo", "proveedores", "catalogo", "paquetes", "configuracion"},
        ).as_dict()
    )
    return mobile_items


def _planner_navigation(empresa, active_key="inicio"):
    dashboard = reverse("planner_dashboard_empresa", kwargs={"empresa_slug": empresa.slug})
    return [
        _item("inicio", "Inicio", dashboard, "I", active_key=active_key),
        _item(
            "eventos",
            "Mis eventos",
            reverse("k9_evento_list", kwargs={"empresa_slug": empresa.slug}),
            "E",
            short_label="Eventos",
            active_key=active_key,
        ),
        _item("agenda", "Agenda", dashboard + "#agenda", "A", active_key=active_key),
        _item("tareas", "Mis tareas", dashboard + "#tareas", "T", short_label="Tareas", active_key=active_key),
    ]


def _dirtec_navigation(active_key="inicio"):
    dashboard = reverse("dirtec_dashboard")
    return [
        _item("inicio", "Inicio", dashboard + "#resumen", "I", active_key=active_key),
        _item("empresas", "Empresas", dashboard + "#empresas", "Em", active_key=active_key),
        _item("usuarios", "Usuarios", dashboard + "#usuarios", "U", active_key=active_key),
        _item("suscripciones", "Suscripciones", dashboard + "#suscripciones", "S", active_key=active_key),
        _item("planes", "Planes", dashboard + "#planes", "P", active_key=active_key),
    ]


def _client_navigation(active_key="inicio"):
    dashboard = reverse("cliente_dashboard")
    return [
        _item("inicio", "Mi evento", dashboard, "I", short_label="Inicio", active_key=active_key),
    ]


def _provider_navigation(active_key="inicio"):
    dashboard = reverse("proveedor_dashboard")
    return [
        _item("inicio", "Mis servicios", dashboard, "I", short_label="Inicio", active_key=active_key),
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
            "mobile_items": _company_mobile_navigation(empresa, items, active_key),
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
