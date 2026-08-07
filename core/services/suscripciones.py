from dataclasses import dataclass

from django.conf import settings
from django.utils import timezone

from suscripciones.models import SuscripcionEmpresa


ESTADOS_ACCESO_COMPLETO = {'PRUEBA', 'ACTIVA', 'PROXIMA_A_VENCER'}
ESTADOS_BLOQUEO_TOTAL = {'SUSPENDIDA', 'CANCELADA'}


@dataclass
class EstadoSuscripcionAcceso:
    empresa: object
    suscripcion: object = None
    estado: str = 'SIN_SUSCRIPCION'
    puede_acceder: bool = True
    puede_escribir: bool = True
    requiere_aviso: bool = False
    mensaje: str = ''


def requiere_suscripcion_obligatoria():
    return getattr(settings, 'SAAS_REQUIRE_SUBSCRIPTION', False)


def evaluar_suscripcion_empresa(empresa, *, hoy=None):
    hoy = hoy or timezone.localdate()
    if not empresa:
        return EstadoSuscripcionAcceso(
            empresa=None,
            puede_acceder=not requiere_suscripcion_obligatoria(),
            puede_escribir=not requiere_suscripcion_obligatoria(),
            requiere_aviso=True,
            mensaje='No hay empresa asociada al usuario.',
        )

    if not empresa.activo:
        return EstadoSuscripcionAcceso(
            empresa=empresa,
            estado='EMPRESA_INACTIVA',
            puede_acceder=False,
            puede_escribir=False,
            requiere_aviso=True,
            mensaje='La empresa esta inactiva. Contacta a DIRTEC.',
        )

    try:
        suscripcion = empresa.suscripcion
    except SuscripcionEmpresa.DoesNotExist:
        return EstadoSuscripcionAcceso(
            empresa=empresa,
            estado='SIN_SUSCRIPCION',
            puede_acceder=not requiere_suscripcion_obligatoria(),
            puede_escribir=not requiere_suscripcion_obligatoria(),
            requiere_aviso=True,
            mensaje='La empresa aun no tiene una suscripcion registrada.',
        )

    if suscripcion.bloqueada_manualmente:
        return EstadoSuscripcionAcceso(
            empresa=empresa,
            suscripcion=suscripcion,
            estado='BLOQUEADA',
            puede_acceder=False,
            puede_escribir=False,
            requiere_aviso=True,
            mensaje=suscripcion.motivo_bloqueo or 'La suscripcion fue bloqueada manualmente por DIRTEC.',
        )

    if suscripcion.estado in ESTADOS_BLOQUEO_TOTAL:
        return EstadoSuscripcionAcceso(
            empresa=empresa,
            suscripcion=suscripcion,
            estado=suscripcion.estado,
            puede_acceder=False,
            puede_escribir=False,
            requiere_aviso=True,
            mensaje='La suscripcion no permite acceso operativo.',
        )

    if suscripcion.fecha_vencimiento < hoy:
        dentro_gracia = suscripcion.fecha_periodo_gracia and hoy <= suscripcion.fecha_periodo_gracia
        return EstadoSuscripcionAcceso(
            empresa=empresa,
            suscripcion=suscripcion,
            estado='VENCIDA_EN_GRACIA' if dentro_gracia else 'VENCIDA',
            puede_acceder=True,
            puede_escribir=bool(dentro_gracia),
            requiere_aviso=True,
            mensaje='La suscripcion esta vencida, pero aun se encuentra en periodo de gracia.' if dentro_gracia else 'La suscripcion esta vencida. Las operaciones de escritura quedan bloqueadas.',
        )

    dias_restantes = (suscripcion.fecha_vencimiento - hoy).days
    if suscripcion.estado == 'PROXIMA_A_VENCER' or dias_restantes <= 7:
        return EstadoSuscripcionAcceso(
            empresa=empresa,
            suscripcion=suscripcion,
            estado='PROXIMA_A_VENCER',
            puede_acceder=True,
            puede_escribir=True,
            requiere_aviso=True,
            mensaje=f'La suscripcion vence en {dias_restantes} dia(s).',
        )

    return EstadoSuscripcionAcceso(
        empresa=empresa,
        suscripcion=suscripcion,
        estado=suscripcion.estado,
        puede_acceder=suscripcion.estado in ESTADOS_ACCESO_COMPLETO,
        puede_escribir=suscripcion.estado in ESTADOS_ACCESO_COMPLETO,
        requiere_aviso=suscripcion.estado not in {'ACTIVA'},
        mensaje='Suscripcion activa.' if suscripcion.estado == 'ACTIVA' else f'Estado de suscripcion: {suscripcion.get_estado_display()}',
    )
