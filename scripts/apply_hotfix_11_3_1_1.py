"""Evita que un clic simple desplace el nodo en Transform Lab."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = (
    ROOT
    / "invitaciones"
    / "templates"
    / "invitaciones"
    / "transform_lab.html"
)


def patch_template():
    text = TEMPLATE.read_text(encoding="utf-8")
    text = text.replace(
        "transform_lab_mount.js' %}?v=0.32.0",
        "transform_lab_mount.js' %}?v=0.32.1",
    )
    TEMPLATE.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    patch_template()
    print("Hotfix 11.3.1.1 aplicado correctamente.")
