"""Aplica la biblioteca visual de componentes del Sprint 10.7."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "invitaciones" / "templates" / "invitaciones" / "editor_builder_engine.html"
CSS = ROOT / "invitaciones" / "static" / "invitaciones" / "css" / "builder_engine_editor.css"


def patch_template():
    text = TEMPLATE.read_text(encoding="utf-8")

    text = text.replace(
        '<button type="button" disabled>Componentes</button>',
        '<button type="button" class="active" data-engine-panel-toggle="components">Componentes</button>',
    )

    panel = """                <section class="engine-component-library" data-engine-component-library></section>

"""
    marker = '                <section class="engine-layers-panel">'
    if "data-engine-component-library" not in text:
        if marker not in text:
            raise SystemExit("No se encontró el panel de Capas.")
        text = text.replace(marker, panel + marker, 1)

    mount_script = """    <script
        type="module"
        src="{% static 'invitaciones/builder_engine/integrations/django/component_library_mount.js' %}?v=0.19.0"
    ></script>
"""
    if "component_library_mount.js" not in text:
        text = text.replace("</body>", mount_script + "</body>", 1)

    TEMPLATE.write_text(text, encoding="utf-8")


def patch_css():
    text = CSS.read_text(encoding="utf-8")
    addition = r"""
.engine-component-library {
    margin: 18px 0;
    padding: 14px;
    border: 1px solid #2d3542;
    border-radius: 12px;
    background: #11161e;
}
.engine-component-library-head {
    display: grid;
    gap: 10px;
    margin-bottom: 14px;
}
.engine-component-library-head strong { display: block; }
.engine-component-library-head small {
    display: block;
    margin-top: 3px;
    color: #7f8999;
    font-size: 10px;
}
.engine-component-library-head input {
    width: 100%;
    padding: 9px 10px;
    border: 1px solid #343c4c;
    border-radius: 8px;
    background: #0b0f15;
    color: #eef1f7;
}
.engine-component-library-groups {
    display: grid;
    gap: 16px;
    max-height: 420px;
    overflow: auto;
    padding-right: 3px;
}
.engine-component-group h3 {
    margin: 0 0 8px;
    color: #8993a3;
    font-size: 10px;
    letter-spacing: .08em;
    text-transform: uppercase;
}
.engine-component-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 7px;
}
.engine-component-item {
    display: grid;
    grid-template-columns: 28px 1fr;
    grid-template-rows: auto auto;
    gap: 1px 8px;
    min-width: 0;
    padding: 9px;
    border: 1px solid #303847;
    border-radius: 9px;
    background: #1a202a;
    color: #dce2ec;
    text-align: left;
    cursor: grab;
}
.engine-component-item:hover {
    border-color: #d2b074;
    background: #29241c;
}
.engine-component-item > span {
    grid-row: 1 / 3;
    display: grid;
    width: 28px;
    height: 28px;
    place-content: center;
    align-self: center;
    border-radius: 7px;
    background: #2a313e;
    color: #f0ca78;
    font-weight: 800;
}
.engine-component-item strong {
    overflow: hidden;
    font-size: 11px;
    white-space: nowrap;
    text-overflow: ellipsis;
}
.engine-component-item small {
    color: #778191;
    font-size: 8px;
}
.engine-library-empty {
    color: #7f8999;
    font-size: 11px;
}
.engine-media-placeholder {
    display: grid;
    min-height: 160px;
    place-content: center;
    gap: 5px;
    border: 2px dashed #aaa194;
    background:
        linear-gradient(135deg, rgba(0,0,0,.03) 25%, transparent 25%) -10px 0/20px 20px,
        linear-gradient(225deg, rgba(0,0,0,.03) 25%, transparent 25%) -10px 0/20px 20px,
        #eee8dd;
    color: #72695d;
    text-align: center;
}
.engine-media-placeholder span { font-size: 30px; }
.engine-media-placeholder strong { font-size: 12px; }
.engine-media-placeholder small { font-size: 9px; }
.engine-preview-countdown {
    flex-direction: row !important;
    justify-content: space-between !important;
    gap: 8px;
}
.engine-preview-card {
    box-shadow: 0 8px 22px rgba(0,0,0,.09);
}
"""
    if ".engine-component-library {" not in text:
        CSS.write_text(text.rstrip() + "\n\n" + addition.lstrip(), encoding="utf-8")


if __name__ == "__main__":
    patch_template()
    patch_css()
    print("Sprint 10.7 aplicado correctamente.")
