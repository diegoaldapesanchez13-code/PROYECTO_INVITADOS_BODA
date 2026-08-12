"""Guest Domain V2 helpers.

R.1 establishes the roster contract without replacing the public RSVP UI yet:
- Grupoinvitacion is access/grouping metadata.
- Invitado is every real/authorized person.
- Unknown extra companions are represented by Invitado placeholders.
"""
from django.core.exceptions import ValidationError
from django.db import transaction

from .models import Invitado


def nombre_acompanante(indice):
    return f'Acompañante {indice}'


@transaction.atomic
def asegurar_roster_grupo(grupo):
    """Ensure the group has a deterministic person roster.

    PERSONAL gets exactly one nominal person (created from nombre_grupo when
    missing). Extra companion placeholders are controlled only by organizer
    fields on Grupoinvitacion.

    FAMILIAR keeps its named integrantes; optional extras are appended as
    placeholders and never replace named people.
    """
    if not grupo.pk:
        raise ValidationError('Guarda el grupo antes de sincronizar sus personas.')

    if grupo.es_personal:
        nominales = list(
            grupo.invitados.filter(es_acompanante_extra=False).order_by('orden', 'id')
        )
        if not nominales:
            Invitado.objects.create(
                grupo=grupo,
                nombre=grupo.nombre_grupo,
                tipo_persona='ADULTO',
                es_acompanante_extra=False,
                orden=0,
            )
        else:
            principal = nominales[0]
            if principal.nombre != grupo.nombre_grupo:
                principal.nombre = grupo.nombre_grupo
                principal.save(update_fields=['nombre'])
            # We do not delete additional nominal rows silently. R.2 will surface
            # any historical anomaly to the organizer for explicit resolution.

    _sincronizar_acompanantes_extra(grupo)
    return grupo


@transaction.atomic
def _sincronizar_acompanantes_extra(grupo):
    deseados = grupo.cantidad_acompanantes_autorizados
    extras = list(
        grupo.invitados.filter(es_acompanante_extra=True).order_by('orden', 'id')
    )

    if len(extras) < deseados:
        base_orden = max(
            list(grupo.invitados.values_list('orden', flat=True)) or [0]
        )
        for offset in range(len(extras) + 1, deseados + 1):
            Invitado.objects.create(
                grupo=grupo,
                nombre=nombre_acompanante(offset),
                tipo_persona='ADULTO',
                es_acompanante_extra=True,
                orden=base_orden + offset,
            )
        return

    if len(extras) <= deseados:
        return

    sobrantes = extras[deseados:]
    bloqueados = []
    for invitado in sobrantes:
        tiene_mesa = invitado.asignaciones_mesa.exists()
        if invitado.asistira is not None or tiene_mesa:
            bloqueados.append(invitado)

    if bloqueados:
        nombres = ', '.join(str(invitado) for invitado in bloqueados)
        raise ValidationError(
            'No puedes reducir acompañantes porque ya tienen RSVP o mesa: '
            f'{nombres}.'
        )

    Invitado.objects.filter(pk__in=[item.pk for item in sobrantes]).delete()


@transaction.atomic
def sincronizar_rsvp_personal_legacy(grupo, attending, confirmed, fecha=None):
    """Compatibility bridge until R.3 replaces group-level public RSVP.

    It only applies to PERSONAL, where the old API already knew a numeric
    confirmed count. It preserves that aggregate by projecting it onto the V2
    roster deterministically. FAMILIAR is intentionally not guessed here.
    """
    if not grupo.es_personal:
        return

    asegurar_roster_grupo(grupo)
    nominal = (
        grupo.invitados.filter(es_acompanante_extra=False)
        .order_by('orden', 'id')
        .first()
    )
    extras = list(
        grupo.invitados.filter(es_acompanante_extra=True).order_by('orden', 'id')
    )

    if nominal:
        nominal.asistira = bool(attending)
        nominal.fecha_confirmacion = fecha
        nominal.save(update_fields=['asistira', 'fecha_confirmacion'])

    asistentes_extra = max(int(confirmed or 0) - (1 if attending else 0), 0)
    for index, invitado in enumerate(extras):
        invitado.asistira = bool(attending and index < asistentes_extra)
        invitado.fecha_confirmacion = fecha
        invitado.save(update_fields=['asistira', 'fecha_confirmacion'])
