"""
ASGI config for config project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.0/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application

# Configura la variable de entorno para usar la configuración de Django.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Crea la aplicación ASGI que se utiliza para despliegues modernos.
application = get_asgi_application()
