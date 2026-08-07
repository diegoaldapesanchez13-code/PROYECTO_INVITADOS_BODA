"""Hotfix 10.8.1.1: corrige el contexto de window.fetch."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = (
    ROOT
    / "invitaciones"
    / "templates"
    / "invitaciones"
    / "editor_builder_engine.html"
)


def patch_template():
    text = TEMPLATE.read_text(encoding="utf-8")

    text = text.replace(
        "asset_library_mount.js' %}?v=0.20.0",
        "asset_library_mount.js' %}?v=0.20.1",
    )

    TEMPLATE.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    patch_template()
    print("Hotfix 10.8.1.1 aplicado correctamente.")
