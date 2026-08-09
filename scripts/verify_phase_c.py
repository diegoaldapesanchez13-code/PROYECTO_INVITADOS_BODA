"""Gate de PHASE C."""

from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = ROOT / "DIRTEC_STUDIO_BUILD"


def run(command, cwd=ROOT, shell=False):
    printable = command if isinstance(command, str) else " ".join(map(str, command))
    print(f"\n> {printable}")
    result = subprocess.run(command, cwd=cwd, shell=shell)
    if result.returncode:
        raise SystemExit(result.returncode)


def main():
    run("node --test builder/tests/*.mjs", cwd=WORKSPACE, shell=True)
    run([sys.executable, WORKSPACE / "scripts" / "build_builder.py"])
    run([sys.executable, WORKSPACE / "scripts" / "verify_builder_build.py"])
    run([sys.executable, ROOT / "manage.py", "check"])
    run([sys.executable, ROOT / "manage.py", "makemigrations", "--check"])
    run([
        sys.executable,
        ROOT / "manage.py",
        "test",
        "invitaciones.tests_builder_django",
        "invitaciones.tests_builder_assets",
    ])
    print("\nPHASE C GATE OK")


if __name__ == "__main__":
    main()
