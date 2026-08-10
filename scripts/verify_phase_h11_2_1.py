"""Gate PHASE H.11.2.1 — Experience Live Controls."""
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
WORKSPACE=ROOT/"DIRTEC_STUDIO_BUILD"

def run(cmd,cwd=ROOT,shell=False):
    printable=cmd if isinstance(cmd,str) else " ".join(map(str,cmd))
    print(f"\n> {printable}")
    result=subprocess.run(cmd,cwd=cwd,shell=shell)
    if result.returncode:
        raise SystemExit(result.returncode)

run("node --test builder/tests/*.mjs",cwd=WORKSPACE,shell=True)
run([sys.executable,WORKSPACE/"scripts/build_builder.py"])
run([sys.executable,WORKSPACE/"scripts/verify_builder_build.py"])
run([sys.executable,ROOT/"manage.py","check"])
run([sys.executable,ROOT/"manage.py","makemigrations","--check"])

print("\nPHASE H.11.2.1 GATE OK")
