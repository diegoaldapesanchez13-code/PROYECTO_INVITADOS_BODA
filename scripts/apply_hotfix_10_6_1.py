"""Corrige la sincronización del frame de transformación."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CSS = (
    ROOT
    / "invitaciones"
    / "static"
    / "invitaciones"
    / "css"
    / "builder_engine_editor.css"
)


def apply_css():
    text = CSS.read_text(encoding="utf-8")

    addition = """
.engine-live-canvas {
    position: relative;
}

.engine-transform-overlay {
    margin: 0;
    transform: none;
    box-sizing: border-box;
}

.engine-transform-overlay,
.engine-transform-overlay * {
    box-sizing: border-box;
}
"""

    if "Hotfix 10.6.1" not in text:
        text = (
            text.rstrip()
            + "\n\n/* Hotfix 10.6.1 — overlay sincronizado */\n"
            + addition.lstrip()
        )
        CSS.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    apply_css()
    print("Hotfix 10.6.1 aplicado correctamente.")
