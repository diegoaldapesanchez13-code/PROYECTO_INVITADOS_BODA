from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.views.decorators.http import require_GET

from core.services.app_context import build_app_context
from core.services.tenant_context import validar_slug_tenant

from .planner_dashboard import construir_planner_home_k9


@login_required(login_url="/login/")
@require_GET
def planner_dashboard(request, empresa_slug):
    """R3B Planner Home canónico K9.

    Las escrituras legacy se mantienen exclusivamente en el endpoint de
    compatibilidad; la ruta canónica no delega a ``invitaciones.views``.
    """
    tenant = validar_slug_tenant(
        request,
        empresa_slug,
        roles={"WEDDING_PLANNER"},
    )
    empresa = tenant.empresa

    context = build_app_context(
        request,
        empresa=empresa,
        page_title="Inicio",
        section_label="Planner",
        active_key="inicio",
    )
    context.update(
        construir_planner_home_k9(
            empresa=empresa,
            planner=request.user,
        )
    )
    return render(request, "eventos/planner_dashboard/home.html", context)

@login_required(login_url="/login/")
def planner_dashboard_legacy(request, empresa_slug):
    """Compatibility endpoint for the retired K8 planner URL.

    GET always converges to the K9 canonical URL. POST is still accepted while
    legacy forms exist, but the delegated operation now redirects back to the
    canonical planner URL.
    """
    validar_slug_tenant(
        request,
        empresa_slug,
        roles={"WEDDING_PLANNER"},
    )
    if request.method == "POST":
        from invitaciones.views import dashboard_planner_slug
        return dashboard_planner_slug(request, empresa_slug)

    return redirect(
        "planner_dashboard_empresa",
        empresa_slug=empresa_slug,
    )
