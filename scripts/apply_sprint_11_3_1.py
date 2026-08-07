"""Monta Transform Lab sin sustituir el editor oficial."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
URLS = ROOT / "invitaciones" / "urls.py"
VIEWS = ROOT / "invitaciones" / "builder_engine_editor_views.py"

VIEW = r"""
@login_required
def transform_lab(request, evento_id):
    evento = get_object_or_404(
        eventos_visibles_usuario(request.user),
        id=evento_id,
    )

    bootstrap = {
        "eventId": evento.id,
        "readOnly": True,
        "engineVersion": "0.32.0",
        "endpoints": {
            "load": reverse(
                "builder_engine_document_load",
                args=[evento.id],
            ),
        },
    }

    return render(
        request,
        "invitaciones/transform_lab.html",
        {
            "evento": evento,
            "transform_lab_bootstrap": bootstrap,
            "renderer_lab_url": reverse(
                "builder_engine_renderer_lab",
                args=[evento.id],
            ),
        },
    )
"""

ROUTE = r"""    path(
        'dashboard/editor-invitacion/<int:evento_id>/engine/transform-lab/',
        builder_engine_editor_views.transform_lab,
        name='builder_engine_transform_lab',
    ),
"""


def patch_views():
    text = VIEWS.read_text(encoding="utf-8")
    if "def transform_lab(" not in text:
        VIEWS.write_text(text.rstrip() + "\n\n" + VIEW.strip() + "\n", encoding="utf-8")


def patch_urls():
    text = URLS.read_text(encoding="utf-8")
    if "name='builder_engine_transform_lab'" in text:
        return

    marker = "name='builder_engine_renderer_lab',"
    position = text.find(marker)
    if position == -1:
        raise SystemExit(
            "No se encontró Renderer Lab. Aplica primero Sprint 11.2.1."
        )

    close_position = text.find("    ),", position)
    if close_position == -1:
        raise SystemExit("No se pudo localizar el cierre de Renderer Lab.")

    insert_at = close_position + len("    ),")
    text = text[:insert_at] + "\n" + ROUTE.rstrip() + text[insert_at:]
    URLS.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    patch_views()
    patch_urls()
    print("Sprint 11.3.1 aplicado correctamente.")
