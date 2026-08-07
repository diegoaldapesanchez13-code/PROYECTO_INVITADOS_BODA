"""Hotfix 10.7.2: mantiene foco y cursor en el Inspector."""

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


def patch_css():
    text = CSS.read_text(encoding="utf-8")

    addition = r"""
/* Hotfix 10.7.2 — edición continua del Inspector */
.engine-inspector input:focus,
.engine-inspector textarea:focus {
    border-color: #8f5cff;
    outline: 2px solid rgba(143, 92, 255, .22);
    outline-offset: 1px;
}

.engine-inspector input,
.engine-inspector textarea {
    scroll-margin-block: 80px;
}
"""

    if "Hotfix 10.7.2" not in text:
        CSS.write_text(
            text.rstrip() + "\n\n" + addition.lstrip(),
            encoding="utf-8",
        )


if __name__ == "__main__":
    patch_css()
    print("Hotfix 10.7.2 aplicado correctamente.")
