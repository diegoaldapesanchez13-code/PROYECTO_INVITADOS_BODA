"""Gate PHASE R.6 — Countdown Data Binding."""
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]

def run(cmd, cwd=ROOT):
    print("\n> " + " ".join(map(str, cmd)))
    result = subprocess.run(cmd, cwd=cwd)
    if result.returncode:
        raise SystemExit(result.returncode)

run([sys.executable, ROOT / "scripts/verify_phase_r5.py"])
run([
    "node",
    "--test",
    "DIRTEC_STUDIO_BUILD/builder/tests/*.mjs",
])
run([
    sys.executable,
    ROOT / "DIRTEC_STUDIO_BUILD/scripts/build_builder.py",
])
run([
    sys.executable,
    ROOT / "DIRTEC_STUDIO_BUILD/scripts/verify_builder_build.py",
])
run([
    sys.executable,
    ROOT / "manage.py",
    "test",
    "invitaciones.tests_builder_countdown_v2",
])
run([sys.executable, ROOT / "manage.py", "check"])
run([
    sys.executable,
    ROOT / "manage.py",
    "makemigrations",
    "--check",
])

print("\nPHASE R.6 GATE OK")
