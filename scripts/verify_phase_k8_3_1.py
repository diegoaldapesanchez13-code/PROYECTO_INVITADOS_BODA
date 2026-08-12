import os
import subprocess
import sys


def run(*args):
    print('>', ' '.join(args))
    subprocess.run(args, check=True)


def main():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    run(sys.executable, 'manage.py', 'check')
    run(sys.executable, 'manage.py', 'makemigrations', '--check', '--dry-run')
    run(sys.executable, 'manage.py', 'test', 'proveedores.tests_k831', 'paquetes.tests_k83', '--verbosity=1')
    print('K.8.3.1 verification: OK')


if __name__ == '__main__':
    main()
