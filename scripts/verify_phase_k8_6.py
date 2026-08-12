"""Gate local K.8.6 para DIRTEC Event Studio.
Ejecutar desde la raiz del proyecto con el venv activo:
    python scripts/verify_phase_k8_6.py
"""
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable


def run(*args):
    cmd = [PYTHON, str(ROOT / 'manage.py'), *args]
    print('\n>', ' '.join(map(str, cmd)))
    result = subprocess.run(cmd, cwd=ROOT)
    if result.returncode:
        raise SystemExit(result.returncode)


run('check')
run('makemigrations', '--check', '--dry-run')
run(
    'test',
    'colaboracion.tests_hotfix_k8_1_1',
    'eventos.tests',
    'paquetes.tests_k83',
    'proveedores.tests_k831',
    'colaboracion.tests_k84',
    'colaboracion.tests_k86',
    '--verbosity', '1',
)
print('\nK.8.6 verification: OK')
