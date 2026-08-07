"""Monta el Renderer Lab aislado sin modificar las rutas oficiales."""
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
URLS = ROOT / "invitaciones" / "urls.py"
VIEWS = ROOT / "invitaciones" / "builder_engine_editor_views.py"

VIEW_FUNCTION = r"""

@login_required
def renderer_lab(request, evento_id):
    evento = get_object_or_404(
        eventos_visibles_usuario(request.user),
        id=evento_id,
    )
    bootstrap = {
        "eventId": evento.id,
        "engineVersion": "0.31.1",
        "readOnly": True,
        "endpoints": {
            "load": reverse("builder_engine_document_load", args=[evento.id]),
        },
    }
    return render(
        request,
        "invitaciones/renderer_lab.html",
        {
            "evento": evento,
            "renderer_lab_bootstrap": bootstrap,
            "renderer_modes": ("EDIT", "PREVIEW", "PUBLIC"),
            "editor_url": reverse("builder_engine_editor", args=[evento.id]),
        },
    )
"""

ROUTE = r"""    path(
        'dashboard/editor-invitacion/<int:evento_id>/engine/renderer-lab/',
        builder_engine_editor_views.renderer_lab,
        name='builder_engine_renderer_lab',
    ),
"""

def patch_views():
    text = VIEWS.read_text(encoding="utf-8")
    if "def renderer_lab(" not in text:
        VIEWS.write_text(text.rstrip() + VIEW_FUNCTION + "\n", encoding="utf-8")

def patch_urls():
    text = URLS.read_text(encoding="utf-8")
    if "name='builder_engine_renderer_lab'" not in text:
        marker = "    path('dashboard/editor-invitacion/<int:evento_id>/engine/', builder_engine_editor_views.editor_builder_engine, name='builder_engine_editor',),\n"
        if marker not in text:
            raise SystemExit("No se encontró la ruta del Builder Engine.")
        URLS.write_text(text.replace(marker, marker + ROUTE, 1), encoding="utf-8")

if __name__ == "__main__":
    patch_views()
    patch_urls()
    print("Sprint 11.2.1 aplicado correctamente.")
