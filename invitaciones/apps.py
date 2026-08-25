from django.apps import AppConfig


class InvitacionesConfig(AppConfig):
    # Nombre interno de la aplicación.
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'invitaciones'

    def import_models(self):
        super().import_models()
        # K9.R4F-B keeps RSVP governance in a focused model module while
        # registering it under the existing invitaciones app label.
        from . import rsvp_models  # noqa: F401
