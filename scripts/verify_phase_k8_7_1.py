import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)


def run(*args):
    print('>', ' '.join(args), flush=True)
    result = subprocess.run(args)
    if result.returncode:
        raise SystemExit(result.returncode)

required = [
    ROOT / 'eventos' / 'dashboard_v3.py',
    ROOT / 'invitaciones' / 'templates' / 'invitaciones' / 'dashboard' / 'v3' / '_resumen.html',
    ROOT / 'invitaciones' / 'templates' / 'invitaciones' / 'dashboard' / 'v3' / '_servicios.html',
]
for path in required:
    if not path.exists():
        raise SystemExit(f'Falta archivo K.8.7.1: {path}')

run(sys.executable, 'manage.py', 'check')
run(sys.executable, 'manage.py', 'makemigrations', '--check', '--dry-run')
run(sys.executable, 'manage.py', 'test', 'eventos.tests_dashboard_v3', '--verbosity=1')
print('K.8.7.1 verification: OK')
