"""Aplica de forma idempotente las rutas del Sprint 10.2."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
URLS = ROOT / "invitaciones" / "urls.py"


def apply():
    text = URLS.read_text(encoding="utf-8")

    import_line = "from . import builder_engine_editor_views\n"
    if import_line not in text:
        marker = "from . import builder_engine_views\n"
        if marker in text:
            text = text.replace(marker, marker + import_line, 1)
        else:
            text = text.replace(
                "from . import views\n",
                "from . import views\n" + import_line,
                1,
            )

    route_marker = "name='builder_engine_editor'"
    if route_marker not in text:
        marker = (
            "    path('dashboard/editor-invitacion/<int:evento_id>/', "
            "views.editor_invitacion_visual, name='editor_invitacion_visual'),\n"
        )
        route = (
            "    path(\n"
            "        'dashboard/editor-invitacion/<int:evento_id>/engine/',\n"
            "        builder_engine_editor_views.editor_builder_engine,\n"
            "        name='builder_engine_editor',\n"
            "    ),\n"
        )
        if marker not in text:
            raise SystemExit(
                "No se encontró la ruta del editor actual en invitaciones/urls.py."
            )
        text = text.replace(marker, marker + route, 1)

    URLS.write_text(text, encoding="utf-8")
    print("Rutas del Builder Engine 10.2 aplicadas.")


if __name__ == "__main__":
    apply()
