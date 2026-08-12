"""Gate PHASE R.5 — Individual Table Assignments V2."""
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]

def run(cmd):
    print("\n> " + " ".join(map(str, cmd)))
    result = subprocess.run(cmd, cwd=ROOT)
    if result.returncode:
        raise SystemExit(result.returncode)

run([sys.executable, ROOT / "scripts/verify_phase_r4.py"])
run([
    sys.executable,
    ROOT / "manage.py",
    "migrate",
    "--plan",
])
run([
    sys.executable,
    ROOT / "manage.py",
    "makemigrations",
    "--check",
])
run([
    sys.executable,
    ROOT / "manage.py",
    "test",
    "mesas.tests",
    "invitaciones.tests_guest_analytics_v2",
])
run([sys.executable, ROOT / "manage.py", "check"])

print("\nPHASE R.5 GATE OK")
