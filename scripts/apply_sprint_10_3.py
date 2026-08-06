"""Aplica de forma idempotente el aviso visual del Sprint 10.3."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "invitaciones" / "templates" / "invitaciones" / "editor_builder_engine.html"
CSS = ROOT / "invitaciones" / "static" / "invitaciones" / "css" / "builder_engine_editor.css"


def apply_template():
    text = TEMPLATE.read_text(encoding="utf-8")
    marker = '<div class="engine-workspace">'
    notice = (
        '        <div class="engine-migration-notice" '
        'data-engine-migration-notice hidden></div>\n\n'
    )
    if "data-engine-migration-notice" not in text:
        if marker not in text:
            raise SystemExit("No se encontró engine-workspace en el template.")
        text = text.replace(marker, notice + "        " + marker, 1)
        TEMPLATE.write_text(text, encoding="utf-8")


def apply_css():
    text = CSS.read_text(encoding="utf-8")
    addition = """
.engine-migration-notice {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 18px;
    padding: 10px 22px;
    border-bottom: 1px solid #4d432e;
    background: #2b2519;
    color: #f4d58d;
    font-size: 12px;
}
.engine-migration-notice[hidden] { display: none; }
.engine-migration-notice span { color: #c8b88f; }
.engine-node-summary {
    display: flex;
    flex-wrap: wrap;
    justify-content: center;
    gap: 8px;
    padding: 28px;
}
.engine-node-chip {
    display: inline-flex;
    padding: 7px 10px;
    border: 1px solid #d6cbb8;
    border-radius: 999px;
    background: #fffaf0;
    color: #665d4f;
    font-size: 11px;
}
"""
    if ".engine-migration-notice" not in text:
        CSS.write_text(text.rstrip() + "\n\n" + addition.lstrip(), encoding="utf-8")


if __name__ == "__main__":
    apply_template()
    apply_css()
    print("Sprint 10.3 aplicado correctamente.")
