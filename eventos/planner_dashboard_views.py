from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from core.services.app_context import build_app_context
from core.services.tenant_context import validar_slug_tenant

from .planner_dashboard import construir_planner_home_k9


@login_required(login_url="/login/")
def planner_dashboard(request, empresa_slug):
    """
    R3B Planner Home.

    GET uses the new App Shell. POST remains delegated to the legacy dashboard
    until the old inline operations are migrated to canonical screens.
    """
    if request.method == "POST":
        from invitaciones.views import dashboard_planner_slug
        return dashboard_planner_slug(request, empresa_slug)

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
