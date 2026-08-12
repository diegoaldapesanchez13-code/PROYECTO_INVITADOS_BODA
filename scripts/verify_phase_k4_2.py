"""K.4.2 — Events as operational nucleus."""
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
    "invitaciones.tests_company_dashboard_k4_2",
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

print("\nPHASE K.4.2 GATE OK")
