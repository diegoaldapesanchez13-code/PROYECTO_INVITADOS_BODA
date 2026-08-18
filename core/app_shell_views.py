from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from core.services.app_context import build_app_context


@login_required(login_url="/login/")
def app_shell_preview(request):
    """
    Temporary R1C visual checkpoint.

    It proves the shared shell/navigation contract before R3 migrates the real
    Company/Planner dashboards. No business data is written here.
    """
    context = build_app_context(
        request,
        page_title="Foundation Preview",
        section_label="Nueva experiencia K9",
        active_key="inicio",
    )

    role = context["app_context"]["role"]
    preview = {
        "DIRTEC": {
            "title": "Control de plataforma",
            "text": "La nueva shell está preparada para administrar empresas, usuarios y suscripciones.",
            "primary_label": "Abrir DIRTEC actual",
            "primary_url": "/dirtec/dashboard/",
        },
        "EMPRESA": {
            "title": "Tu negocio, organizado",
            "text": "Esta será la base del nuevo Dashboard Empresa y del acceso a cada Event Workspace.",
            "primary_label": "Abrir dashboard actual",
            "primary_url": (
                f"/empresa/{context['empresa'].slug}/dashboard/"
                if context["empresa"]
                else "/redirigir/"
            ),
        },
        "PLANNER": {
            "title": "Tu operación diaria",
            "text": "Eventos, tareas, agenda y alertas vivirán sobre esta misma navegación.",
            "primary_label": "Abrir dashboard actual",
            "primary_url": (
                f"/empresa/{context['empresa'].slug}/planner/dashboard/"
                if context["empresa"]
                else "/redirigir/"
            ),
        },
        "CLIENTE": {
            "title": "Tu evento",
            "text": "El portal de cliente conservará una proyección simple, segura y enfocada.",
            "primary_label": "Abrir portal actual",
            "primary_url": "/cliente/dashboard/",
        },
        "PROVEEDOR": {
            "title": "Tus servicios",
            "text": "El portal de proveedor mostrará únicamente operación autorizada.",
            "primary_label": "Abrir portal actual",
            "primary_url": "/proveedor/dashboard/",
        },
    }.get(
        role,
        {
            "title": "DIRTEC Event Studio",
            "text": "Tu cuenta todavía no tiene una navegación de producto asignada.",
            "primary_label": "Continuar",
            "primary_url": "/redirigir/",
        },
    )

    context["preview"] = preview
    return render(request, "core/app/shell_preview.html", context)
