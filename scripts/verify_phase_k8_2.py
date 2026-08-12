from pathlib import Path
import os
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
ENV = os.environ.copy()
windows_site_packages = ROOT / 'venv' / 'Lib' / 'site-packages'
if windows_site_packages.exists():
    ENV['PYTHONPATH'] = str(windows_site_packages) + os.pathsep + ENV.get('PYTHONPATH', '')


def run(*args):
    print('>', ' '.join(args))
    subprocess.run(args, cwd=ROOT, env=ENV, check=True)


def main():
    run(sys.executable, 'manage.py', 'check')
    run(sys.executable, 'manage.py', 'makemigrations', '--check', '--dry-run')
    run(sys.executable, 'manage.py', 'migrate', '--plan')
    run(sys.executable, 'manage.py', 'test', 'eventos', 'proveedores.tests_event_domain_k82', '--verbosity', '1')
    print('K.8.2 verification: OK')


if __name__ == '__main__':
    main()
