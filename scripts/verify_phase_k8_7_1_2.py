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
    ROOT / 'itinerario' / 'migrations' / '0003_agenda_semantics_k8712.py',
    ROOT / 'itinerario' / 'services.py',
    ROOT / 'eventos' / 'dashboard_v3.py',
    ROOT / 'eventos' / 'tests_operational_clarity_k8712.py',
    ROOT / 'invitaciones' / 'templates' / 'invitaciones' / 'dashboard' / 'v3' / '_servicios.html',
    ROOT / 'invitaciones' / 'templates' / 'invitaciones' / 'dashboard' / 'v3' / '_agenda.html',
    ROOT / 'invitaciones' / 'templates' / 'invitaciones' / 'dashboard' / 'v3' / '_tareas.html',
]
for path in required:
    if not path.exists():
        raise SystemExit(f'Falta archivo K.8.7.1.2: {path}')

# Gate explícito: el Event Dashboard ya no puede incluir los parciales legacy.
dashboard = (ROOT / 'invitaciones' / 'templates' / 'invitaciones' / 'dashboard.html').read_text(encoding='utf-8')
for forbidden in ['Compatibilidad temporal', '_tab_operacion.html', '_tab_contenido.html']:
    if forbidden in dashboard:
        raise SystemExit(f'Legacy todavía activo en Event Dashboard: {forbidden}')

run(sys.executable, 'manage.py', 'check')
run(sys.executable, 'manage.py', 'makemigrations', '--check', '--dry-run')
run(sys.executable, 'manage.py', 'showmigrations', 'itinerario')
run(
    sys.executable, 'manage.py', 'test',
    'eventos.tests_dashboard_v3',
    'eventos.tests_operational_clarity_k8712',
    'colaboracion.tests_k86',
    'tareas.tests_k5_1_agenda',
    '--verbosity=1',
)
print('K.8.7.1.2 verification: OK')
