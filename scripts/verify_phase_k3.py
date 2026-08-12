"""K.3 — Identity & Login gate."""
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def run(cmd):
    print("\n> " + " ".join(map(str, cmd)))
    result = subprocess.run(
        cmd,
        cwd=ROOT,
    )
    if result.returncode:
        raise SystemExit(
            result.returncode
        )


run([
    sys.executable,
    ROOT / "scripts/verify_phase_k1_k2.py",
])

run([
    sys.executable,
    ROOT / "manage.py",
    "test",
    "core.tests_identity_k3",
    "invitaciones.tests_role_redirect_k3",
    "invitaciones.tests_identity_forms_k3",
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

print("\nPHASE K.3 GATE OK")
