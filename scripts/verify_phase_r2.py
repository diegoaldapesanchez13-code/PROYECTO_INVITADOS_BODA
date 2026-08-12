"""Gate PHASE R.2 — Guest Dashboard V2."""
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]

def run(cmd):
    print("\n> " + " ".join(map(str, cmd)))
    result = subprocess.run(cmd, cwd=ROOT)
    if result.returncode:
        raise SystemExit(result.returncode)

run([sys.executable, ROOT / "manage.py", "check"])
run([sys.executable, ROOT / "manage.py", "makemigrations", "--check"])
run([sys.executable, ROOT / "manage.py", "test",
     "invitaciones.tests_guest_domain_v2",
     "invitaciones.tests_guest_dashboard_v2"])

print("\nPHASE R.2 GATE OK")
