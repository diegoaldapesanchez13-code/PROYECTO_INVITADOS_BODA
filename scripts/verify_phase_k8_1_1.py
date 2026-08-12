"""K.8.1.1 — Collaboration auth/session hotfix gate."""
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def run(cmd):
    print("\n> " + " ".join(map(str, cmd)))
    result = subprocess.run(cmd, cwd=ROOT)
    if result.returncode:
        raise SystemExit(result.returncode)


run([
    sys.executable,
    ROOT / "manage.py",
    "test",
    "colaboracion.tests",
    "colaboracion.tests_hotfix_k8_1_1",
])
run([
    sys.executable,
    ROOT / "manage.py",
    "test",
    "invitaciones.tests_client_portal_k6",
    "invitaciones.tests_provider_portal_k7",
    "invitaciones.tests_planner_workspace_k5",
])
run([
    sys.executable,
    ROOT / "manage.py",
    "check",
])
run([
    sys.executable,
    ROOT / "manage.py",
    "makemigrations",
    "--check",
])
print("\nPHASE K.8.1.1 GATE OK")
