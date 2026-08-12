import os
import subprocess
import sys


def run(*args, env=None):
    cmd = [sys.executable, 'manage.py', *args]
    print('> ' + ' '.join(cmd))
    subprocess.run(cmd, check=True, env=env)


# Gate local/desarrollo sobre la base actual.
run('check')
run('makemigrations', '--check', '--dry-run')
run(
    'test',
    'eventos.tests_production_hardening_k878',
    'core.tests_tenant_authorization_k',
    'eventos.tests_operational_clarity_k8712',
    'eventos.tests_client_portal_v3',
    'eventos.tests_provider_portal_v3',
    'eventos.tests_client_guests_v3',
    'presupuesto.tests_client_payments_k8741',
    'colaboracion.tests_k877_collaboration_ux',
    '--verbosity=1',
)

# Gate global. Si una prueba legacy queda obsoleta, este paso debe fallar antes del commit.
run('test', '--verbosity=1')

print('K.8.7.8 STABLE GATE: OK')
