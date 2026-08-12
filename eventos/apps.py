from django.apps import AppConfig


class EventosConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'eventos'
    verbose_name = 'Dominio de eventos'

    def ready(self):
        from . import signals  # noqa: F401
