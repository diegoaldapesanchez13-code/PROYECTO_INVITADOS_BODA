"""K.5.1 — Operations layout and agenda gate."""
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
        raise SystemExit(result.returncode)


run([
    sys.executable,
    ROOT / "manage.py",
    "test",
    "tareas.tests_k5_1_agenda",
    "invitaciones.tests_operations_layout_k5_1",
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

print("\nPHASE K.5.1 GATE OK")
