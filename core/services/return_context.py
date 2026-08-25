from urllib.parse import urlparse

from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme

from core.services.permisos import roles_usuario_empresa, usuario_es_dirtec_operativo


RETURN_PARAM = "return_to"


def _default_return(user, empresa):
    if usuario_es_dirtec_operativo(user):
        return reverse("dirtec_dashboard")

    roles = roles_usuario_empresa(user, empresa)
    if "WEDDING_PLANNER" in roles and not roles.intersection({"ADMIN_EMPRESA", "VENTAS"}):
        return reverse(
            "planner_dashboard_empresa",
            kwargs={"empresa_slug": empresa.slug},
        )
    return reverse("empresa_dashboard", kwargs={"empresa_slug": empresa.slug})


def _allowed_prefixes(empresa):
    slug = empresa.slug
    return (
        f"/empresa/{slug}/dashboard/",
        f"/empresa/{slug}/planner/dashboard/",
        f"/empresa/{slug}/wedding-planner/dashboard/",
        f"/empresa/{slug}/eventos/",
    )


def safe_return_to(request, *, empresa, raw=None, default=None):
    """
    Resolve a safe internal return destination for the K9 product shell.

    - External origins are rejected.
    - Cross-tenant company paths are rejected.
    - Only known product areas inside the current tenant are accepted.
    - Query string / fragment are preserved for local UI context.
    """
    candidate = (raw or "").strip()
    if not candidate:
        return default or _default_return(request.user, empresa)

    if not url_has_allowed_host_and_scheme(
        candidate,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return default or _default_return(request.user, empresa)

    parsed = urlparse(candidate)
    if parsed.scheme or parsed.netloc:
        return default or _default_return(request.user, empresa)

    path = parsed.path or "/"
    if not any(path.startswith(prefix) for prefix in _allowed_prefixes(empresa)):
        return default or _default_return(request.user, empresa)

    return candidate


def request_return_to(request, *, empresa, default=None):
    raw = request.POST.get(RETURN_PARAM) or request.GET.get(RETURN_PARAM)
    return safe_return_to(
        request,
        empresa=empresa,
        raw=raw,
        default=default,
    )
