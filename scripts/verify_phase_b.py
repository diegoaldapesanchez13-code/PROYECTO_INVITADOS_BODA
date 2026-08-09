"""Gate de aceptación para PHASE B — Django Integration."""

from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
STUDIO = ROOT / "DIRTEC_STUDIO_BUILD"


def run(command, *, cwd=ROOT, shell=False):
    printable = command if isinstance(command, str) else " ".join(map(str, command))
    print(f"\n> {printable}")
    result = subprocess.run(command, cwd=cwd, shell=shell)
    if result.returncode:
        raise SystemExit(result.returncode)


def main():
    run("node --test builder/tests/*.mjs", cwd=STUDIO, shell=True)
    run([sys.executable, STUDIO / "scripts" / "build_builder.py"])
    run([sys.executable, STUDIO / "scripts" / "verify_builder_build.py"])
    run([sys.executable, ROOT / "manage.py", "check"])
    run([sys.executable, ROOT / "manage.py", "makemigrations", "--check", "--dry-run"])
    run([sys.executable, ROOT / "manage.py", "migrate", "--plan"])
    run([sys.executable, ROOT / "manage.py", "test", "invitaciones.tests_builder_django"])
    print("\nPHASE B GATE OK")


if __name__ == "__main__":
    main()
