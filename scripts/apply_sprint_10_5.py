"""Aplica el panel de capas y el Inspector de nodos del Sprint 10.5."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "invitaciones" / "templates" / "invitaciones" / "editor_builder_engine.html"
CSS = ROOT / "invitaciones" / "static" / "invitaciones" / "css" / "builder_engine_editor.css"


def patch_template():
    text = TEMPLATE.read_text(encoding="utf-8")

    nav_marker = """                <nav>
                    <button type="button" disabled>Componentes</button>
                    <button type="button" disabled>Assets</button>
                    <button type="button" disabled>Capas</button>
                </nav>"""
    layers = """                <nav>
                    <button type="button" disabled>Componentes</button>
                    <button type="button" disabled>Assets</button>
                </nav>

                <section class="engine-layers-panel">
                    <div class="engine-canvas-nav-head">
                        <strong>Capas</strong>
                    </div>
                    <div data-engine-layers-panel></div>
                </section>"""
    if "data-engine-layers-panel" not in text:
        if nav_marker not in text:
            raise SystemExit("No se encontró el bloque lateral esperado.")
        text = text.replace(nav_marker, layers, 1)

    inspector_start = '<aside class="engine-inspector">'
    inspector_end = "</aside>"
    start = text.index(inspector_start)
    end = text.index(inspector_end, start)
    new_inspector = """<aside class="engine-inspector">
                <span class="section-kicker">Inspector</span>
                <div data-engine-node-inspector></div>
            """
    if "data-engine-node-inspector" not in text:
        text = text[:start] + new_inspector + text[end:]

    TEMPLATE.write_text(text, encoding="utf-8")


def patch_css():
    text = CSS.read_text(encoding="utf-8")
    addition = r"""
.engine-layers-panel { margin-top: 18px; }
.engine-layers-empty { color: #7f8999; font-size: 12px; }
.engine-layers-tree { display: grid; gap: 4px; }
.engine-layer-select {
    width: 100%;
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 8px 8px 8px calc(8px + (var(--layer-depth) * 14px));
    border: 1px solid transparent;
    border-radius: 8px;
    background: transparent;
    color: #cfd5df;
    text-align: left;
    cursor: pointer;
}
.engine-layer-select:hover { background: #1d232d; }
.engine-layer-select.active {
    border-color: #d2b074;
    background: #2a241b;
    color: #f4d58d;
}
.engine-layer-icon {
    display: grid;
    width: 22px;
    height: 22px;
    place-content: center;
    border-radius: 6px;
    background: #2a313e;
    font-size: 10px;
}
.engine-layer-copy { min-width: 0; flex: 1; }
.engine-layer-copy strong,
.engine-layer-copy small {
    display: block;
    overflow: hidden;
    white-space: nowrap;
    text-overflow: ellipsis;
}
.engine-layer-copy small { color: #7f8999; font-size: 9px; margin-top: 2px; }
.engine-layer-state { font-size: 9px; color: #9ca6b6; }
.engine-preview-node.is-selected {
    outline: 2px solid #8f5cff;
    outline-offset: 4px;
}
.engine-node-inspector-head {
    display: grid;
    gap: 12px;
    padding-bottom: 16px;
    border-bottom: 1px solid #2b3240;
}
.engine-node-inspector-head span {
    color: #d2b074;
    font-size: 10px;
    font-weight: 800;
    letter-spacing: .1em;
}
.engine-node-inspector-head strong { display: block; margin-top: 4px; }
.engine-node-inspector-actions {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 5px;
}
.engine-node-inspector-actions button {
    padding: 7px;
    border: 1px solid #343c4c;
    border-radius: 7px;
    background: #202632;
    color: #d4dae4;
    font-size: 10px;
    cursor: pointer;
}
.engine-node-inspector-actions button.danger {
    border-color: #5b3338;
    color: #ff9aa4;
}
.engine-property-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 10px;
}
.engine-field textarea,
.engine-field input {
    width: 100%;
    padding: 9px 10px;
    border: 1px solid #343c4c;
    border-radius: 8px;
    background: #0f131a;
    color: #eef1f7;
}
.engine-field textarea { resize: vertical; }
.engine-inspector-empty {
    display: grid;
    gap: 6px;
    padding-top: 16px;
    color: #8e98a8;
}
.engine-inspector-empty span { font-size: 12px; line-height: 1.5; }
"""
    if ".engine-layer-select" not in text:
        CSS.write_text(text.rstrip() + "\n\n" + addition.lstrip(), encoding="utf-8")


if __name__ == "__main__":
    patch_template()
    patch_css()
    print("Sprint 10.5 aplicado correctamente.")
