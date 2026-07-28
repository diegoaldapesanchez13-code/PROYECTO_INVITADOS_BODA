from invitaciones.models import EventoBoda
from organizaciones.models import MembresiaEmpresa


class LimitePlanExcedido(Exception):
    pass


def obtener_plan_empresa(empresa):
    try:
        return empresa.suscripcion.plan
    except AttributeError:
        return None


def conteo_usuarios_empresa(empresa):
    return MembresiaEmpresa.objects.filter(empresa=empresa, activo=True).values('usuario_id').distinct().count()


def conteo_planners_empresa(empresa):
    return MembresiaEmpresa.objects.filter(empresa=empresa, rol='WEDDING_PLANNER', activo=True).count()


def conteo_clientes_empresa(empresa):
    return MembresiaEmpresa.objects.filter(empresa=empresa, rol='CLIENTE', activo=True).count()


def conteo_eventos_activos_empresa(empresa):
    return EventoBoda.objects.filter(empresa=empresa, activo=True).count()


def validar_limite_usuarios(empresa, incremento=1):
    plan = obtener_plan_empresa(empresa)
    if plan and conteo_usuarios_empresa(empresa) + incremento > plan.limite_usuarios:
        raise LimitePlanExcedido('Se alcanzo el limite de usuarios del plan contratado.')


def validar_limite_planners(empresa, incremento=1):
    plan = obtener_plan_empresa(empresa)
    if plan and conteo_planners_empresa(empresa) + incremento > plan.limite_wedding_planners:
        raise LimitePlanExcedido('Se alcanzo el limite de wedding planners del plan contratado.')


def validar_limite_eventos_activos(empresa, incremento=1):
    plan = obtener_plan_empresa(empresa)
    if plan and conteo_eventos_activos_empresa(empresa) + incremento > plan.limite_eventos_activos:
        raise LimitePlanExcedido('Se alcanzo el limite de eventos activos del plan contratado.')


def validar_limite_clientes(empresa, incremento=1):
    plan = obtener_plan_empresa(empresa)
    if plan and conteo_clientes_empresa(empresa) + incremento > plan.limite_clientes:
        raise LimitePlanExcedido('Se alcanzo el limite de clientes del plan contratado.')


def resumen_uso_plan(empresa):
    plan = obtener_plan_empresa(empresa)
    return {
        'plan': plan,
        'usuarios': conteo_usuarios_empresa(empresa),
        'planners': conteo_planners_empresa(empresa),
        'clientes': conteo_clientes_empresa(empresa),
        'eventos_activos': conteo_eventos_activos_empresa(empresa),
        'limite_usuarios': plan.limite_usuarios if plan else None,
        'limite_planners': plan.limite_wedding_planners if plan else None,
        'limite_clientes': plan.limite_clientes if plan else None,
        'limite_eventos_activos': plan.limite_eventos_activos if plan else None,
    }
