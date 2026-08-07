"""Aplica controles responsive y manipulación directa del Sprint 10.6."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "invitaciones" / "templates" / "invitaciones" / "editor_builder_engine.html"
CSS = ROOT / "invitaciones" / "static" / "invitaciones" / "css" / "builder_engine_editor.css"


def patch_template():
    text = TEMPLATE.read_text(encoding="utf-8")

    text = text.replace(
        '<button class="active" type="button">iPhone</button>',
        '<button class="active" type="button" data-engine-device="mobile">iPhone</button>',
    )
    text = text.replace(
        '<button type="button" disabled>Tablet</button>',
        '<button type="button" data-engine-device="tablet">Tablet</button>',
    )
    text = text.replace(
        '<button type="button" disabled>Desktop</button>',
        '<button type="button" data-engine-device="desktop">Desktop</button>',
    )

    mount_script = """    <script
        type="module"
        src="{% static 'invitaciones/builder_engine/integrations/django/direct_manipulation_mount.js' %}?v=0.18.0"
    ></script>
"""
    if "direct_manipulation_mount.js" not in text:
        text = text.replace("</body>", mount_script + "</body>", 1)

    TEMPLATE.write_text(text, encoding="utf-8")


def patch_css():
    text = CSS.read_text(encoding="utf-8")
    addition = r"""
.engine-active-canvas {
    width: min(var(--preview-width, 390px), calc(100% - 60px));
    transition: width .2s ease;
}
.engine-transform-overlay {
    position: absolute;
    z-index: 10000;
    pointer-events: none;
    border: 1px solid #8f5cff;
}
.engine-transform-overlay[hidden] { display: none; }
.engine-transform-box { position: absolute; inset: 0; }
.engine-transform-handle {
    position: absolute;
    width: 13px;
    height: 13px;
    padding: 0;
    border: 2px solid #fff;
    border-radius: 50%;
    background: #8f5cff;
    box-shadow: 0 1px 5px rgba(0,0,0,.35);
    pointer-events: auto;
    touch-action: none;
    cursor: nwse-resize;
}
.engine-transform-handle.nw { left: -7px; top: -7px; }
.engine-transform-handle.ne { right: -7px; top: -7px; cursor: nesw-resize; }
.engine-transform-handle.sw { left: -7px; bottom: -7px; cursor: nesw-resize; }
.engine-transform-handle.se { right: -7px; bottom: -7px; }
.engine-transform-handle.rotate {
    left: 50%;
    top: -36px;
    width: 24px;
    height: 24px;
    transform: translateX(-50%);
    color: #fff;
    font-size: 13px;
    cursor: grab;
}
.engine-transform-handle.rotate::after {
    content: "";
    position: absolute;
    left: 50%;
    top: 22px;
    width: 1px;
    height: 13px;
    background: #8f5cff;
}
.engine-shell[data-transforming="true"] {
    user-select: none;
    cursor: grabbing;
}
.engine-live-canvas[data-preview-device="mobile"] { border-radius: 24px; }
.engine-live-canvas[data-preview-device="tablet"] { border-radius: 18px; }
.engine-live-canvas[data-preview-device="desktop"] { border-radius: 12px; }
"""
    if ".engine-transform-overlay" not in text:
        CSS.write_text(text.rstrip() + "\n\n" + addition.lstrip(), encoding="utf-8")


if __name__ == "__main__":
    patch_template()
    patch_css()
    print("Sprint 10.6 aplicado correctamente.")
