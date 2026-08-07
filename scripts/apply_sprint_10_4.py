"""Actualiza de forma idempotente el template y CSS del Canvas Workspace."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "invitaciones" / "templates" / "invitaciones" / "editor_builder_engine.html"
CSS = ROOT / "invitaciones" / "static" / "invitaciones" / "css" / "builder_engine_editor.css"


def patch_template():
    text = TEMPLATE.read_text(encoding="utf-8")

    old_nav = """                <nav>
                    <button class="active" type="button">Lienzos</button>
                    <button type="button" disabled>Componentes</button>
                    <button type="button" disabled>Assets</button>
                    <button type="button" disabled>Capas</button>
                </nav>"""
    new_nav = """                <div class="engine-canvas-navigator" data-engine-canvas-nav></div>

                <nav>
                    <button type="button" disabled>Componentes</button>
                    <button type="button" disabled>Assets</button>
                    <button type="button" disabled>Capas</button>
                </nav>"""
    if "data-engine-canvas-nav" not in text:
        if old_nav not in text:
            raise SystemExit("No se encontró el bloque de navegación esperado.")
        text = text.replace(old_nav, new_nav, 1)

    old_canvas = '<div class="engine-canvas-list" data-engine-canvases>'
    if old_canvas in text:
        start = text.index(old_canvas)
        end_marker = "                </div>\n            </section>"
        end = text.index(end_marker, start)
        replacement = (
            '                <div class="engine-active-canvas" '
            'data-engine-active-canvas></div>\n'
        )
        text = text[:start] + replacement + text[end + len("                </div>\n"):]

    text = text.replace(
        "<h2>Sin selección</h2>",
        '<h2 data-engine-inspector-title>Sin selección</h2>',
    )

    inspector_marker = """                <p>
                    El montaje visual ya utiliza BuilderApp y Persistence Engine.
                    Canvas, Components e Inspector se conectarán progresivamente.
                </p>"""
    inspector_fields = """                <p>
                    Selecciona un lienzo para editar sus propiedades básicas.
                </p>

                <label class="engine-field">
                    Nombre del lienzo
                    <input type="text" data-engine-canvas-name disabled>
                </label>"""
    if "data-engine-canvas-name" not in text:
        text = text.replace(inspector_marker, inspector_fields, 1)

    TEMPLATE.write_text(text, encoding="utf-8")


def patch_css():
    text = CSS.read_text(encoding="utf-8")
    addition = r"""
.engine-canvas-navigator { margin: 26px 0 18px; }
.engine-canvas-nav-head {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 10px;
}
.engine-canvas-nav-head button,
.engine-canvas-item-actions button {
    border: 1px solid #343c4c;
    background: #202632;
    color: #d4dae4;
    border-radius: 7px;
    cursor: pointer;
}
.engine-canvas-nav-head button { width: 30px; height: 30px; }
.engine-canvas-nav-list { display: grid; gap: 8px; }
.engine-canvas-nav-item {
    border: 1px solid #2d3542;
    border-radius: 10px;
    background: #191e27;
    overflow: hidden;
}
.engine-canvas-nav-item.active {
    border-color: #d2b074;
    box-shadow: 0 0 0 1px rgba(210,176,116,.25);
}
.engine-canvas-select {
    width: 100%;
    display: flex;
    align-items: center;
    gap: 9px;
    padding: 10px;
    border: 0;
    background: transparent;
    color: inherit;
    text-align: left;
    cursor: pointer;
}
.engine-canvas-select > span {
    display: grid;
    width: 24px;
    height: 24px;
    place-content: center;
    border-radius: 50%;
    background: #2b3240;
    color: #d2b074;
    font-size: 11px;
}
.engine-canvas-select div { min-width: 0; }
.engine-canvas-select strong,
.engine-canvas-select small {
    display: block;
    overflow: hidden;
    white-space: nowrap;
    text-overflow: ellipsis;
}
.engine-canvas-select small { margin-top: 2px; color: #838d9e; font-size: 10px; }
.engine-canvas-item-actions {
    display: grid;
    grid-template-columns: repeat(5, 1fr);
    gap: 4px;
    padding: 0 8px 8px;
}
.engine-canvas-item-actions button { min-height: 26px; font-size: 11px; }
.engine-active-canvas {
    width: min(700px, calc(100% - 60px));
    margin: 38px auto;
}
.engine-live-canvas {
    position: relative;
    overflow: hidden;
    width: 100%;
    border: 1px solid #303847;
    border-radius: 22px;
    background: #fff;
    color: #24201a;
    box-shadow: 0 22px 70px rgba(0,0,0,.35);
}
.engine-preview-node { box-sizing: border-box; max-width: none; }
.engine-preview-node[data-node-type="TEXT"] { white-space: pre-wrap; }
.engine-preview-node[data-node-type="BUTTON"] {
    padding: 12px 18px;
    border: 0;
    border-radius: 999px;
    background: #2f7a4d;
    color: #fff;
}
.engine-preview-countdown { display: flex; justify-content: center; gap: 12px; }
.engine-preview-countdown > .engine-preview-node {
    position: relative !important;
    left: auto !important;
    top: auto !important;
    width: auto !important;
    transform: none !important;
}
.engine-live-empty {
    position: absolute;
    inset: 0;
    display: grid;
    place-content: center;
    text-align: center;
    color: #7a7265;
}
.engine-live-empty span { display: block; margin-top: 4px; font-size: 12px; }
.engine-field {
    display: grid;
    gap: 7px;
    margin-top: 22px;
    color: #aab3c2;
    font-size: 12px;
}
.engine-field input {
    width: 100%;
    padding: 10px 11px;
    border: 1px solid #343c4c;
    border-radius: 8px;
    background: #0f131a;
    color: #eef1f7;
}
"""
    if ".engine-canvas-navigator" not in text:
        CSS.write_text(text.rstrip() + "\n\n" + addition.lstrip(), encoding="utf-8")


if __name__ == "__main__":
    patch_template()
    patch_css()
    print("Sprint 10.4 aplicado correctamente.")
