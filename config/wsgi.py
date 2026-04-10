"""
WSGI config for config project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.0/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

# Configura la variable de entorno para cargar los ajustes del proyecto.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Crea la aplicación WSGI que el servidor usará para manejar peticiones.
application = get_wsgi_application()
