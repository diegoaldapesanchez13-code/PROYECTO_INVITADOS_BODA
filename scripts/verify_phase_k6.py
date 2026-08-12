"""K.6 — Client Portal V2 gate."""
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
    ROOT / "manage.py",
    "test",
    "invitaciones.tests_client_portal_k6",
    "invitaciones.tests_client_portal_layout_k6",
])
run([
    sys.executable,
    ROOT / "manage.py",
    "test",
    "invitaciones.tests_role_redirect_k3",
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

print("\nPHASE K.6 GATE OK")
