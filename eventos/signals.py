from django.db.models.signals import m2m_changed, post_save
from django.dispatch import receiver

from invitaciones.models import EventoBoda

from .services import sincronizar_participantes_legacy


@receiver(post_save, sender=EventoBoda)
def sync_planner_legacy_to_event_domain(sender, instance, raw=False, **kwargs):
    if raw:
        return
    sincronizar_participantes_legacy(instance)


@receiver(m2m_changed, sender=EventoBoda.clientes.through)
def sync_clients_legacy_to_event_domain(sender, instance, action, **kwargs):
    if action in {'post_add', 'post_remove', 'post_clear'}:
        sincronizar_participantes_legacy(instance)
