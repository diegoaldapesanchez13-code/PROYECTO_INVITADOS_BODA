"""Aplica PHASE C — Persistent Asset Library."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
URLS = ROOT / "invitaciones" / "urls.py"


ROUTES = """    path(
        'dashboard/editor-invitacion/<int:evento_id>/api/assets/',
        builder_views.assets_api,
        name='builder_assets_api',
    ),
    path(
        'dashboard/editor-invitacion/<int:evento_id>/api/assets/<int:asset_id>/',
        builder_views.asset_detail_api,
        name='builder_asset_detail_api',
    ),
"""


def patch_urls():
    text = URLS.read_text(encoding="utf-8")

    if "name='builder_assets_api'" in text:
        print("urls.py: rutas de assets ya presentes.")
        return

    marker = (
        "    path('dashboard/editor-invitacion/<int:evento_id>/api/publish/', "
        "builder_views.publish_api, name='builder_publish_api'),\n"
    )

    if marker not in text:
        raise SystemExit(
            "No se encontró PHASE B. Aplica primero Django Integration."
        )

    text = text.replace(marker, marker + ROUTES, 1)
    URLS.write_text(text, encoding="utf-8")
    print("urls.py: API persistente de assets agregada.")


if __name__ == "__main__":
    patch_urls()
    print("PHASE C aplicada correctamente.")
