from django.db import transaction

from .models import ParticipanteEvento


@transaction.atomic
def sincronizar_participantes_legacy(evento):
    """Sincroniza las relaciones legacy hacia ParticipanteEvento.

    Durante K.8.2 `EventoBoda.wedding_planner` y `EventoBoda.clientes` siguen
    funcionando para no romper vistas existentes. Este servicio mantiene el
    nuevo dominio alineado y es idempotente.
    """
    creados = 0
    actualizados = 0

    planner_ids = {evento.wedding_planner_id} if evento.wedding_planner_id else set()
    ParticipanteEvento.objects.filter(evento=evento, rol='PLANNER').exclude(
        usuario_id__in=planner_ids
    ).update(activo=False)

    if evento.wedding_planner_id:
        _, created = ParticipanteEvento.objects.update_or_create(
            evento=evento,
            usuario_id=evento.wedding_planner_id,
            rol='PLANNER',
            defaults={
                'activo': True,
                'puede_ver_finanzas': True,
                'puede_aprobar': True,
                'puede_gestionar_invitados': True,
                'puede_gestionar_servicios': True,
            },
        )
        creados += int(created)
        actualizados += int(not created)

    cliente_ids = set(evento.clientes.values_list('id', flat=True))
    ParticipanteEvento.objects.filter(evento=evento, rol='CLIENTE').exclude(
        usuario_id__in=cliente_ids
    ).update(activo=False)

    for usuario_id in cliente_ids:
        _, created = ParticipanteEvento.objects.update_or_create(
            evento=evento,
            usuario_id=usuario_id,
            rol='CLIENTE',
            defaults={
                'activo': True,
                'puede_aprobar': True,
                'puede_gestionar_invitados': True,
            },
        )
        creados += int(created)
        actualizados += int(not created)

    return {'creados': creados, 'actualizados': actualizados}
