"""Hotfix 10.7.1: inserción, drag & drop y layout fijo del Builder."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CSS = ROOT / "invitaciones" / "static" / "invitaciones" / "css" / "builder_engine_editor.css"


def patch_css():
    text = CSS.read_text(encoding="utf-8")
    addition = r"""
/* Hotfix 10.7.1 — workspace sin scroll vertical global */
.engine-shell {
    height: 100vh;
    max-height: 100vh;
    overflow: hidden;
}

.engine-shell main,
.engine-shell .engine-main,
.engine-shell .engine-workspace,
.engine-shell [data-engine-workspace] {
    min-height: 0;
}

.engine-shell .engine-sidebar,
.engine-shell aside {
    min-height: 0;
    max-height: calc(100vh - 70px);
    overflow-y: auto;
    overscroll-behavior: contain;
    scrollbar-gutter: stable;
}

.engine-component-library {
    margin: 10px 0;
}

.engine-component-library-groups {
    max-height: min(38vh, 430px);
    overflow-y: auto;
    overflow-x: hidden;
}

.engine-layers-panel {
    min-height: 140px;
    max-height: min(34vh, 360px);
    overflow-y: auto;
    overscroll-behavior: contain;
}

.engine-active-canvas {
    min-height: 0;
    max-height: calc(100vh - 110px);
    overflow: auto;
    overscroll-behavior: contain;
}

.engine-component-item[draggable="true"] {
    user-select: none;
    -webkit-user-drag: element;
}

.engine-component-item[draggable="true"]:active {
    cursor: grabbing;
}

@media (max-width: 900px) {
    .engine-shell {
        height: auto;
        max-height: none;
        overflow: visible;
    }

    .engine-shell .engine-sidebar,
    .engine-shell aside,
    .engine-active-canvas {
        max-height: none;
    }
}
"""
    if "Hotfix 10.7.1" not in text:
        CSS.write_text(text.rstrip() + "\n\n" + addition.lstrip(), encoding="utf-8")


if __name__ == "__main__":
    patch_css()
    print("Hotfix 10.7.1 aplicado correctamente.")
