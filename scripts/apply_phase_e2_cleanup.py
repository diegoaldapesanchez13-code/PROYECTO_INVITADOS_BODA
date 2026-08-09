"""PHASE E.2 — elimina runtime visual legacy y fuentes duplicadas."""
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]

DELETE_FILES = [
    "invitaciones/templates/invitaciones/editor_invitacion.html",
    "invitaciones/templates/invitaciones/ver_invitacion.html",
    "invitaciones/templates/invitaciones/dashboard/partials/_secciones_invitacion.html",
    "invitaciones/static/invitaciones/js/editor_invitacion.js",
    "invitaciones/static/invitaciones/js/invitacion.js",
    "invitaciones/static/invitaciones/css/editor_invitacion.css",
    "invitaciones/static/invitaciones/css/invitacion.css",
]

DELETE_DIRS = [
    "invitaciones/static/invitaciones/js/builder_v3",
    "builder_engine",
]

for rel in DELETE_FILES:
    path = ROOT / rel
    if path.exists():
        path.unlink()
        print(f"DELETE file: {rel}")

for rel in DELETE_DIRS:
    path = ROOT / rel
    if path.exists():
        shutil.rmtree(path)
        print(f"DELETE dir: {rel}")

print("PHASE E.2 cleanup aplicada.")
print("Source Builder: DIRTEC_STUDIO_BUILD/builder")
print("Runtime build: invitaciones/static/invitaciones/builder")
