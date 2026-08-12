"""Gate PHASE R.4 — Guest Analytics V2."""
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]

def run(cmd, cwd=ROOT):
    print("\n> " + " ".join(map(str, cmd)))
    result = subprocess.run(cmd, cwd=cwd)
    if result.returncode:
        raise SystemExit(result.returncode)

run([sys.executable, ROOT / "scripts/verify_phase_r3.py"])
run([
    sys.executable,
    ROOT / "manage.py",
    "test",
    "invitaciones.tests_guest_analytics_v2",
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

print("\nPHASE R.4 GATE OK")
