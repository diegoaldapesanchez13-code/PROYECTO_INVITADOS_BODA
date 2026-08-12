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
    'eventos.tests_company_dashboard_v3',
    'invitaciones.tests_company_dashboard_k4_2',
    'invitaciones.tests_company_dashboard_k4_3',
    'eventos.tests_planner_dashboard_v3',
    'eventos.tests_dashboard_v3',
    '--verbosity=1',
)
print('K.8.7.3 verification: OK')
