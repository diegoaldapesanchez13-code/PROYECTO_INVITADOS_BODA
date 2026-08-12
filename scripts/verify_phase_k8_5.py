import os, subprocess, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)
py = sys.executable
commands = [
    [py, "manage.py", "check"],
    [py, "manage.py", "makemigrations", "--check"],
    [py, "manage.py", "test", "colaboracion.tests_k84", "--verbosity", "1"],
]
for cmd in commands:
    print("\n>", " ".join(cmd))
    result = subprocess.run(cmd)
    if result.returncode:
        raise SystemExit(result.returncode)
print("\nK.8.5 verification: OK")
