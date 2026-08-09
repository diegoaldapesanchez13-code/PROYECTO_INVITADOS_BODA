"""Aplica PHASE B sobre el baseline builder-v3-clean-rebuild.

Es idempotente:
- agrega campos Builder a DisenoInvitacion;
- cambia la ruta oficial del editor a DIRTEC Builder;
- conserva editor legacy en /legacy/;
- agrega APIs document/publish.
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODELS = ROOT / "invitaciones" / "models.py"
URLS = ROOT / "invitaciones" / "urls.py"


FIELDS = """    documento_builder_borrador = models.JSONField(default=dict, blank=True)
    documento_builder_publicado = models.JSONField(default=dict, blank=True)
    builder_revision = models.PositiveIntegerField(default=0)
"""


def patch_models():
    text = MODELS.read_text(encoding="utf-8")

    if "documento_builder_borrador" in text:
        print("models.py: campos Builder ya presentes.")
        return

    marker = "    configuracion_publicada = models.JSONField(default=dict, blank=True)\n"
    if marker not in text:
        raise SystemExit("No se encontró DisenoInvitacion.configuracion_publicada.")

    text = text.replace(marker, marker + FIELDS, 1)
    MODELS.write_text(text, encoding="utf-8")
    print("models.py: campos Builder agregados.")


def patch_urls():
    text = URLS.read_text(encoding="utf-8")

    import_line = "from .builder import views as builder_views\n"
    if import_line not in text:
        text = text.replace(
            "from . import views\n",
            "from . import views\n" + import_line,
            1,
        )

    old = (
        "    path('dashboard/editor-invitacion/<int:evento_id>/', "
        "views.editor_invitacion_visual, name='editor_invitacion_visual'),\n"
    )

    new = (
        "    path('dashboard/editor-invitacion/<int:evento_id>/legacy/', "
        "views.editor_invitacion_visual, name='editor_invitacion_visual_legacy'),\n"
        "    path('dashboard/editor-invitacion/<int:evento_id>/', "
        "builder_views.editor, name='editor_invitacion_visual'),\n"
        "    path('dashboard/editor-invitacion/<int:evento_id>/api/document/', "
        "builder_views.document_api, name='builder_document_api'),\n"
        "    path('dashboard/editor-invitacion/<int:evento_id>/api/publish/', "
        "builder_views.publish_api, name='builder_publish_api'),\n"
    )

    if "name='builder_document_api'" not in text:
        if old not in text:
            raise SystemExit("No se encontró la ruta legacy esperada del editor.")
        text = text.replace(old, new, 1)

    URLS.write_text(text, encoding="utf-8")
    print("urls.py: DIRTEC Builder establecido como editor oficial.")


if __name__ == "__main__":
    patch_models()
    patch_urls()
    print("PHASE B aplicada correctamente.")
