from dataclasses import dataclass

from django.urls import reverse

from core.services.authorization import Actions, usuario_puede_evento
from core.services.permisos import roles_usuario_empresa, usuario_es_dirtec_operativo


@dataclass(frozen=True)
class WorkspaceTab:
    key: str
    label: str
    url: str | None
    group: str
    enabled: bool = True
    badge: str = ""

    def as_dict(self):
        return {
            "key": self.key,
            "label": self.label,
            "url": self.url,
            "group": self.group,
            "enabled": self.enabled,
            "badge": self.badge,
        }


def _url(name, empresa, evento):
    return reverse(
        name,
        kwargs={"empresa_slug": empresa.slug, "evento_id": evento.id},
    )


def build_workspace_tabs(*, user, empresa, evento, active_key="resumen"):
    """
    Single source of truth for Event Workspace navigation.

    R4A enables only sections already migrated to canonical K9 screens.
    Remaining modules are registered now but disabled until their R4 subphase.
    """
    can_view = usuario_puede_evento(user, evento, Actions.EVENT_VIEW)
    can_edit = usuario_puede_evento(user, evento, Actions.EVENT_EDIT)

    if not can_view:
        return {"active_key": active_key, "tabs": [], "groups": []}

    roles = roles_usuario_empresa(user, empresa)
    is_internal = bool(
        usuario_es_dirtec_operativo(user)
        or roles.intersection({"ADMIN_EMPRESA", "VENTAS", "WEDDING_PLANNER"})
    )

    tabs = [
        WorkspaceTab("resumen", "Resumen", _url("k9_evento_resumen", empresa, evento), "principal"),
        WorkspaceTab("datos", "Datos", _url("k9_evento_datos", empresa, evento), "principal", enabled=can_edit),
        WorkspaceTab("comercial", "Comercial", _url("k9_evento_comercial", empresa, evento), "negocio", enabled=True),
        WorkspaceTab("servicios", "Servicios", _url("k9_evento_servicios", empresa, evento), "operacion", enabled=True),
        WorkspaceTab("tareas", "Tareas", None, "operacion", enabled=False),
        WorkspaceTab("agenda", "Agenda", None, "operacion", enabled=False),
        WorkspaceTab("invitados", "Invitados", None, "experiencia", enabled=False),
        WorkspaceTab("documentos", "Documentos", None, "operacion", enabled=False),
        WorkspaceTab("finanzas", "Finanzas", None, "negocio", enabled=False),
        WorkspaceTab("invitacion", "Invitación", None, "experiencia", enabled=False),
        WorkspaceTab("actividad", "Actividad", None, "control", enabled=False),
        WorkspaceTab(
            "configuracion",
            "Configuración",
            _url("k9_evento_configuracion", empresa, evento),
            "control",
            enabled=can_edit and is_internal,
        ),
    ]

    return {
        "active_key": active_key,
        "tabs": [tab.as_dict() for tab in tabs],
        "groups": [
            {"key": "principal", "label": "Evento"},
            {"key": "negocio", "label": "Comercial"},
            {"key": "operacion", "label": "Operación"},
            {"key": "experiencia", "label": "Experiencia"},
            {"key": "control", "label": "Control"},
        ],
    }
