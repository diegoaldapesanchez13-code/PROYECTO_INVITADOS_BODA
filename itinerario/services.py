from django.core.exceptions import PermissionDenied

from eventos.models import ParticipanteEvento

from .models import ParticipanteActividad


def asegurar_participantes_cita(actividad, *, creador=None):
    """Crea la lista de confirmación de una cita sin duplicar participantes."""
    if actividad.tipo != 'CITA':
        return []

    creados = []
    for participante_evento in ParticipanteEvento.objects.filter(
        evento=actividad.evento,
        activo=True,
    ).select_related('usuario'):
        rol = participante_evento.rol
        if rol not in {'CLIENTE', 'PLANNER', 'COLABORADOR'}:
            rol = 'COLABORADOR'
        estado = 'CONFIRMADO' if creador and participante_evento.usuario_id == creador.id else 'PENDIENTE'
        participante, _ = ParticipanteActividad.objects.get_or_create(
            actividad=actividad,
            usuario=participante_evento.usuario,
            defaults={
                'rol': rol,
                'estado': estado,
                'requerido': True,
            },
        )
        creados.append(participante)

    if actividad.proveedor_id:
        participante, _ = ParticipanteActividad.objects.get_or_create(
            actividad=actividad,
            proveedor=actividad.proveedor,
            defaults={
                'rol': 'PROVEEDOR',
                'estado': 'PENDIENTE',
                'requerido': True,
            },
        )
        creados.append(participante)
    return creados


def participante_responde_usuario(participante, usuario):
    if participante.usuario_id == usuario.id:
        return True
    if participante.proveedor_id and participante.proveedor.usuario_id == usuario.id:
        return True
    return False


def registrar_confirmacion_propia(participante, usuario, estado, comentario=''):
    if not participante_responde_usuario(participante, usuario):
        raise PermissionDenied('Solo el participante puede responder esta confirmación.')
    if estado not in {'CONFIRMADO', 'NO_ASISTE', 'REPROGRAMAR'}:
        raise PermissionDenied('Respuesta de confirmación inválida.')
    participante.registrar_respuesta(estado, comentario)
    actividad = participante.actividad
    if actividad.confirmada_completa and actividad.estado != 'CONFIRMADA':
        actividad.estado = 'CONFIRMADA'
        actividad.save(update_fields=['estado'])
    elif not actividad.confirmada_completa and actividad.estado == 'CONFIRMADA':
        actividad.estado = 'PENDIENTE'
        actividad.save(update_fields=['estado'])
    return participante
