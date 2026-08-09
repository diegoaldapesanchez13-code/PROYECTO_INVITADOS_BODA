from pathlib import Path
import subprocess, sys

ROOT=Path(__file__).resolve().parents[1]
WORKSPACE=ROOT/"DIRTEC_STUDIO_BUILD"

def run(cmd,cwd=ROOT,shell=False):
    text=cmd if isinstance(cmd,str) else " ".join(map(str,cmd))
    print(f"\n> {text}")
    r=subprocess.run(cmd,cwd=cwd,shell=shell)
    if r.returncode: raise SystemExit(r.returncode)

run("node --test builder/tests/*.mjs",cwd=WORKSPACE,shell=True)
run([sys.executable,WORKSPACE/"scripts/build_builder.py"])
run([sys.executable,WORKSPACE/"scripts/verify_builder_build.py"])
run([sys.executable,ROOT/"manage.py","check"])
run([sys.executable,ROOT/"manage.py","makemigrations","--check"])
run([sys.executable,ROOT/"manage.py","test",
     "invitaciones.tests_builder_django",
     "invitaciones.tests_builder_assets",
     "invitaciones.tests_builder_public",
     "invitaciones.tests_builder_v4"])
print("\nPHASE F.2 GATE OK")
