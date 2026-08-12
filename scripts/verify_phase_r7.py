"""Gate PHASE R.7 — Product Dashboard UX."""
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
    ROOT / "scripts/verify_phase_r6.py",
])
run([
    sys.executable,
    ROOT / "manage.py",
    "test",
    "invitaciones.tests_dashboard_product_v2",
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

print("\nPHASE R.7 GATE OK")
