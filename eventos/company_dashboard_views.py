from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from core.services.app_context import build_app_context
from core.services.tenant_context import validar_slug_tenant

from .company_dashboard import construir_dashboard_empresa_k9


@login_required(login_url="/login/")
def company_dashboard(request, empresa_slug):
    """
    R3A Company Home.

    GET usa la nueva experiencia.
    POST se delega temporalmente al dashboard legacy para no romper acciones
    administrativas que todavía no han migrado a pantallas canónicas.
    """
    if request.method == "POST":
        from invitaciones.views import dashboard_empresa_slug
        return dashboard_empresa_slug(request, empresa_slug)

    tenant = validar_slug_tenant(
        request,
        empresa_slug,
        roles={"ADMIN_EMPRESA", "VENTAS"},
    )
    empresa = tenant.empresa

    context = build_app_context(
        request,
        empresa=empresa,
        page_title="Inicio",
        section_label=empresa.nombre_comercial,
        active_key="inicio",
    )
    context.update(construir_dashboard_empresa_k9(empresa=empresa))
    return render(request, "eventos/company_dashboard/home.html", context)
