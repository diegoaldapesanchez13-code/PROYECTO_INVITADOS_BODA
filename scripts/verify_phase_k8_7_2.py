import subprocess
import sys

def run(*args):
    cmd = [sys.executable, 'manage.py', *args]
    print('> ' + ' '.join(cmd))
    subprocess.run(cmd, check=True)

run('check')
run('makemigrations', '--check', '--dry-run')
run(
    'test',
    'eventos.tests_planner_dashboard_v3',
    'invitaciones.tests_planner_workspace_k5',
    'eventos.tests_dashboard_v3',
    'eventos.tests_operational_clarity_k8712',
    '--verbosity=1',
)
print('K.8.7.2 verification: OK')
