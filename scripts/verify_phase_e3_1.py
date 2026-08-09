from pathlib import Path
import subprocess,sys,re
ROOT=Path(__file__).resolve().parents[1]
WORKSPACE=ROOT/"DIRTEC_STUDIO_BUILD"
VIEWS=ROOT/"invitaciones/views.py"
FORBIDDEN=("editor_invitacion_visual","ver_invitacion","guardar_diseno_invitacion_visual","publicar_diseno_invitacion_visual","componentes_invitacion_visual","componente_invitacion_visual")
def run(cmd,cwd=ROOT,shell=False):
    print("\n>",cmd if isinstance(cmd,str) else " ".join(map(str,cmd)))
    r=subprocess.run(cmd,cwd=cwd,shell=shell)
    if r.returncode: raise SystemExit(r.returncode)
s=VIEWS.read_text(encoding="utf8")
for name in FORBIDDEN:
    if re.search(rf"^def\s+{re.escape(name)}\b",s,re.M): raise SystemExit(f"Legacy Python presente: {name}")
run("node --test builder/tests/*.mjs",cwd=WORKSPACE,shell=True)
run([sys.executable,WORKSPACE/"scripts/build_builder.py"])
run([sys.executable,WORKSPACE/"scripts/verify_builder_build.py"])
run([sys.executable,ROOT/"manage.py","check"])
run([sys.executable,ROOT/"manage.py","makemigrations","--check"])
run([sys.executable,ROOT/"manage.py","test","invitaciones.tests_builder_django","invitaciones.tests_builder_assets","invitaciones.tests_builder_public","invitaciones.tests_legacy_source_purge"])
print("\nPHASE E.3.1 GATE OK")
