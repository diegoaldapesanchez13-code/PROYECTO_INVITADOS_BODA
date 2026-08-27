from .models import ContratoEvento, ParticipanteEvento


# D2 canonical contract lifecycle.
#
# CONTRATADO is the K9 runtime state created by the current contract flow.
# FIRMADO remains active only for compatibility with historical/legacy rows.
# New D2 code must use these helpers rather than inventing another definition
# of "current contract".
CONTRATO_ESTADOS_VIGENTES = ("CONTRATADO", "FIRMADO")
CONTRATO_ESTADOS_HISTORICOS = ("CANCELADO", "REEMPLAZADO")


def participantes_activos(evento, rol=None):
    qs = ParticipanteEvento.objects.filter(evento=evento, activo=True).select_related("usuario")
    if rol:
        qs = qs.filter(rol=rol)
    return qs


def contratos_evento(evento):
    return (
        ContratoEvento.objects.filter(evento=evento)
        .select_related("creado_por", "propuesta_origen")
        .order_by("-version", "-id")
    )


def contratos_vigentes(evento):
    return contratos_evento(evento).filter(estado__in=CONTRATO_ESTADOS_VIGENTES)


def contrato_vigente(evento):
    """Single source of truth for the active/current contract of an event."""
    return contratos_vigentes(evento).first()


def contrato_es_vigente(contrato):
    if contrato is None or contrato.estado not in CONTRATO_ESTADOS_VIGENTES:
        return False
    vigente = contrato_vigente(contrato.evento)
    return bool(vigente and vigente.pk == contrato.pk)


def contrato_es_materializable(contrato):
    """
    D2 intentionally keeps materialization limited to the current K9
    CONTRATADO contract. Legacy FIRMADO can be read/reviewed/cancelled, but
    D3 will decide how legacy/current operation is reconciled.
    """
    return bool(
        contrato
        and contrato.estado == "CONTRATADO"
        and contrato_es_vigente(contrato)
    )
