#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys


def main():
    """Run administrative tasks."""
    # Configura la variable de entorno para que Django use la configuración del proyecto.
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    try:
        # Importa la función que ejecuta los comandos de Django desde la línea de comandos.
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        # Si Django no está disponible, muestra un mensaje de error claro.
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    # Ejecuta el comando recibido en sys.argv (por ejemplo: runserver, migrate, createsuperuser).
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    # Solo se ejecuta cuando el archivo se lanza directamente.
    main()
