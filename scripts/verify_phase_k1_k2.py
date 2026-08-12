"""K.1 + K.2 — Tenant Context & Permission Matrix."""
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
    "core.tests_tenant_authorization_k",
    "invitaciones.tests_tenant_k1",
])
run([
    sys.executable,
    ROOT / "manage.py",
    "test",
    "core.tests",
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

print("\nPHASE K.1 + K.2 GATE OK")
