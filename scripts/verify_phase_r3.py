"""Gate PHASE R.3 — Individual RSVP V2."""
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]

def run(cmd, cwd=ROOT):
    print("\n> " + " ".join(map(str, cmd)))
    result = subprocess.run(cmd, cwd=cwd)
    if result.returncode:
        raise SystemExit(result.returncode)

run(["node", "--test", "DIRTEC_STUDIO_BUILD/builder/tests/*.mjs"])
run([sys.executable, ROOT / "DIRTEC_STUDIO_BUILD/scripts/build_builder.py"])
run([sys.executable, ROOT / "DIRTEC_STUDIO_BUILD/scripts/verify_builder_build.py"])
run([sys.executable, ROOT / "manage.py", "check"])
run([sys.executable, ROOT / "manage.py", "makemigrations", "--check"])
run([
    sys.executable,
    ROOT / "manage.py",
    "test",
    "invitaciones.tests_guest_domain_v2",
    "invitaciones.tests_guest_dashboard_v2",
    "invitaciones.tests_guest_rsvp_v2",
    "invitaciones.tests_builder_public",
])

print("\nPHASE R.3 GATE OK")
