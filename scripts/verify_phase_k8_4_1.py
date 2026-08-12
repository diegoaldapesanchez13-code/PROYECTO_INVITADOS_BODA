import os
import sys

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django
from django.core.management import call_command


def main():
    django.setup()
    print("[K.8.4.1] manage.py check")
    call_command("check")
    print("[K.8.4.1] makemigrations --check")
    call_command("makemigrations", check=True, dry_run=True, verbosity=1)
    print("[K.8.4.1] regression tests")
    failures = call_command(
        "test",
        "colaboracion.tests",
        "colaboracion.tests_hotfix_k8_1_1",
        "colaboracion.tests_k84",
        "paquetes.tests_k83",
        "proveedores.tests_k831",
        "eventos.tests",
        verbosity=1,
    )
    if failures:
        raise SystemExit(failures)
    print("K.8.4.1 verification: OK")


if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    main()
