"""PHASE J.1.1 — Invitation Bindings + RSVP Adaptive UI."""
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def run(cmd):
    print("\n> " + " ".join(map(str, cmd)))
    result = subprocess.run(cmd, cwd=ROOT)
    if result.returncode:
        raise SystemExit(result.returncode)


run([sys.executable, ROOT / "scripts/verify_phase_j1.py"])
run(["node", "--test", "DIRTEC_STUDIO_BUILD/builder/tests/*.mjs"])
run([sys.executable, ROOT / "DIRTEC_STUDIO_BUILD/scripts/build_builder.py"])
run([sys.executable, ROOT / "DIRTEC_STUDIO_BUILD/scripts/verify_builder_build.py"])
run([sys.executable, ROOT / "manage.py", "test", "invitaciones.tests_builder_j1_1"])
run([sys.executable, ROOT / "manage.py", "check"])
run([sys.executable, ROOT / "manage.py", "makemigrations", "--check"])
print("\nPHASE J.1.1 GATE OK")
