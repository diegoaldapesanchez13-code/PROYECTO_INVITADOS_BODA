"""Gate PHASE E.2 — Legacy Runtime Removal."""
from pathlib import Path
import subprocess, sys

ROOT=Path(__file__).resolve().parents[1]
WORKSPACE=ROOT/"DIRTEC_STUDIO_BUILD"

FORBIDDEN_PATHS=[
    ROOT/"invitaciones/templates/invitaciones/editor_invitacion.html",
    ROOT/"invitaciones/templates/invitaciones/ver_invitacion.html",
    ROOT/"invitaciones/templates/invitaciones/dashboard/partials/_secciones_invitacion.html",
    ROOT/"invitaciones/static/invitaciones/js/builder_v3",
    ROOT/"builder_engine",
]
FORBIDDEN_URL_NAMES=[
    "editor_invitacion_visual_legacy",
    "ver_invitacion_legacy",
    "guardar_diseno_invitacion_visual",
    "publicar_diseno_invitacion_visual",
    "componentes_invitacion_visual",
]
def run(cmd,cwd=ROOT,shell=False):
    print("\\n>", cmd if isinstance(cmd,str) else " ".join(map(str,cmd)))
    r=subprocess.run(cmd,cwd=cwd,shell=shell)
    if r.returncode: raise SystemExit(r.returncode)

for p in FORBIDDEN_PATHS:
    if p.exists():
        raise SystemExit(f"LEGACY PATH PRESENTE: {p.relative_to(ROOT)}")

urls=(ROOT/"invitaciones/urls.py").read_text(encoding="utf8")
for name in FORBIDDEN_URL_NAMES:
    if name in urls:
        raise SystemExit(f"LEGACY URL PRESENTE: {name}")

public=(ROOT/"invitaciones/builder/public_views.py").read_text(encoding="utf8")
if "from invitaciones.views import ver_invitacion" in public:
    raise SystemExit("Fallback legacy aún presente en public_views.py")

editor=(ROOT/"invitaciones/templates/invitaciones/builder/editor.html").read_text(encoding="utf8")
if "legacy_editor_url" in editor or ">Legacy<" in editor:
    raise SystemExit("Enlace Legacy aún presente en Builder")

run("node --test builder/tests/*.mjs",cwd=WORKSPACE,shell=True)
run([sys.executable,WORKSPACE/"scripts/build_builder.py"])
run([sys.executable,WORKSPACE/"scripts/verify_builder_build.py"])
run([sys.executable,ROOT/"manage.py","check"])
run([sys.executable,ROOT/"manage.py","makemigrations","--check"])
run([sys.executable,ROOT/"manage.py","test",
     "invitaciones.tests_builder_django",
     "invitaciones.tests_builder_assets",
     "invitaciones.tests_builder_public"])

print("\\nPHASE E.2 GATE OK")
