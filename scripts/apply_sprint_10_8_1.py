"""Aplica Asset Manager 10.8.1 de forma idempotente."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
URLS = ROOT / "invitaciones" / "urls.py"
VIEW = ROOT / "invitaciones" / "builder_engine_editor_views.py"
TEMPLATE = ROOT / "invitaciones" / "templates" / "invitaciones" / "editor_builder_engine.html"
CSS = ROOT / "invitaciones" / "static" / "invitaciones" / "css" / "builder_engine_editor.css"


def patch_urls():
    text = URLS.read_text(encoding="utf-8")
    import_line = "from . import builder_asset_views\n"
    if import_line not in text:
        anchor = "from . import builder_engine_editor_views\n"
        if anchor in text:
            text = text.replace(anchor, anchor + import_line, 1)
        else:
            text = text.replace("from . import views\n", "from . import views\n" + import_line, 1)

    route = """    path(
        'dashboard/editor-invitacion/<int:evento_id>/engine/assets/',
        builder_asset_views.listar_assets_builder,
        name='builder_engine_assets_list',
    ),
"""
    if "name='builder_engine_assets_list'" not in text:
        marker = "    # DIRTEC Builder Engine — Persistence Contract v1.\n"
        if marker not in text:
            raise SystemExit("No se encontró el bloque del Builder Engine en urls.py.")
        text = text.replace(marker, route + "\n" + marker, 1)

    URLS.write_text(text, encoding="utf-8")


def patch_view():
    text = VIEW.read_text(encoding="utf-8")

    if '"assets": reverse(' not in text:
        insertion = """            "assets": reverse(
                "builder_engine_assets_list",
                args=[evento.id],
            ),
"""
        marker = '            "load": reverse('
        if marker not in text:
            raise SystemExit("No se encontró endpoints.load en builder_engine_editor_views.py.")
        text = text.replace(marker, insertion + marker, 1)

    VIEW.write_text(text, encoding="utf-8")


def patch_template():
    text = TEMPLATE.read_text(encoding="utf-8")
    text = text.replace(
        '<button type="button" disabled>Assets</button>',
        '<button type="button" class="active">Assets</button>',
    )

    panel = """                <section class="engine-asset-library" data-engine-asset-library></section>

"""
    marker = '                <section class="engine-layers-panel">'
    if "data-engine-asset-library" not in text:
        if marker not in text:
            raise SystemExit("No se encontró el panel de Capas.")
        text = text.replace(marker, panel + marker, 1)

    script = """    <script
        type="module"
        src="{% static 'invitaciones/builder_engine/integrations/django/asset_library_mount.js' %}?v=0.20.0"
    ></script>
"""
    if "asset_library_mount.js" not in text:
        text = text.replace("</body>", script + "</body>", 1)

    TEMPLATE.write_text(text, encoding="utf-8")


def patch_css():
    text = CSS.read_text(encoding="utf-8")
    addition = r"""
.engine-asset-library {
    margin: 10px 0;
    padding: 14px;
    border: 1px solid #2d3542;
    border-radius: 12px;
    background: #11161e;
}
.engine-assets-head {
    display: grid;
    gap: 9px;
    margin-bottom: 10px;
}
.engine-assets-head small {
    display: block;
    margin-top: 3px;
    color: #7f8999;
    font-size: 10px;
}
.engine-assets-head input {
    width: 100%;
    padding: 9px 10px;
    border: 1px solid #343c4c;
    border-radius: 8px;
    background: #0b0f15;
    color: #eef1f7;
}
.engine-assets-filters {
    display: flex;
    gap: 5px;
    margin-bottom: 10px;
}
.engine-assets-filters button {
    padding: 6px 9px;
    border: 1px solid #343c4c;
    border-radius: 999px;
    background: #1a202a;
    color: #9da7b7;
    font-size: 9px;
}
.engine-assets-filters button.active {
    border-color: #d2b074;
    color: #f0ca78;
}
.engine-assets-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 7px;
    max-height: min(34vh, 360px);
    overflow-y: auto;
}
.engine-asset-card {
    min-width: 0;
    padding: 0;
    overflow: hidden;
    border: 1px solid #303847;
    border-radius: 9px;
    background: #1a202a;
    color: #dce2ec;
    text-align: left;
    cursor: pointer;
}
.engine-asset-card:hover { border-color: #d2b074; }
.engine-asset-preview {
    display: block;
    aspect-ratio: 1.25;
    background: #0b0f15;
}
.engine-asset-preview img,
.engine-asset-preview video {
    width: 100%;
    height: 100%;
    object-fit: cover;
}
.engine-asset-copy {
    display: block;
    padding: 7px;
}
.engine-asset-copy strong,
.engine-asset-copy small {
    display: block;
    overflow: hidden;
    white-space: nowrap;
    text-overflow: ellipsis;
}
.engine-asset-copy strong { font-size: 10px; }
.engine-asset-copy small {
    margin-top: 3px;
    color: #778191;
    font-size: 8px;
}
.engine-assets-empty,
.engine-assets-message {
    grid-column: 1 / -1;
    padding: 18px;
    color: #7f8999;
    text-align: center;
    font-size: 10px;
}
.engine-assets-empty span,
.engine-assets-empty strong,
.engine-assets-empty small { display: block; }
.engine-assets-empty span { font-size: 28px; }
.engine-assets-empty small { margin-top: 4px; }
.engine-assets-message.error { color: #ff9aa4; }
"""
    if ".engine-asset-library {" not in text:
        CSS.write_text(text.rstrip() + "\n\n" + addition.lstrip(), encoding="utf-8")


if __name__ == "__main__":
    patch_urls()
    patch_view()
    patch_template()
    patch_css()
    print("Sprint 10.8.1 aplicado correctamente.")
