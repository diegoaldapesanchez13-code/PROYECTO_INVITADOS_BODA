"""Gate PHASE R.1 — Guest Domain V2."""
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def run(args):
    print('\n> ' + ' '.join(map(str, args)))
    result = subprocess.run(args, cwd=ROOT)
    if result.returncode:
        raise SystemExit(result.returncode)


run([sys.executable, ROOT / 'manage.py', 'check'])
run([sys.executable, ROOT / 'manage.py', 'makemigrations', '--check'])
run([sys.executable, ROOT / 'manage.py', 'test', 'invitaciones.tests_guest_domain_v2'])
run([sys.executable, ROOT / 'manage.py', 'test', 'invitaciones.tests_builder_public'])

print('\nPHASE R.1 GATE OK')
