from .models import ContratoEvento, ParticipanteEvento


def participantes_activos(evento, rol=None):
    qs = ParticipanteEvento.objects.filter(evento=evento, activo=True).select_related('usuario')
    if rol:
        qs = qs.filter(rol=rol)
    return qs


def contratos_evento(evento):
    return ContratoEvento.objects.filter(evento=evento).select_related('creado_por')


def contrato_vigente(evento):
    return contratos_evento(evento).filter(estado='FIRMADO').order_by('-version', '-id').first()
