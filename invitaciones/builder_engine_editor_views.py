from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render
from django.urls import reverse

from .permissions import eventos_visibles_usuario


@login_required
def editor_builder_engine(request, evento_id):
    evento = get_object_or_404(
        eventos_visibles_usuario(request.user),
        id=evento_id,
    )

    bootstrap = {
        "eventId": evento.id,
        "engineVersion": "0.14.0",
        "endpoints": {
            "load": reverse(
                "builder_engine_document_load",
                args=[evento.id],
            ),
            "save": reverse(
                "builder_engine_document_save",
                args=[evento.id],
            ),
            "publish": reverse(
                "builder_engine_document_publish",
                args=[evento.id],
            ),
        },
        "legacyEditorUrl": reverse(
            "editor_invitacion_visual",
            args=[evento.id],
        ),
        "dashboardUrl": reverse("dashboard"),
    }

    return render(
        request,
        "invitaciones/editor_builder_engine.html",
        {
            "evento": evento,
            "builder_bootstrap": bootstrap,
            "legacy_editor_url": bootstrap["legacyEditorUrl"],
            "dashboard_url": bootstrap["dashboardUrl"],
        },
    )
