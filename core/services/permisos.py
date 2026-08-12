from organizaciones.models import EmpresaSuscriptora, MembresiaEmpresa


ROLES_DIRTEC_GRUPOS = {'Superadministrador', 'DIRTEC'}


def usuario_es_dirtec_operativo(user):
    if not getattr(user, 'is_authenticated', False):
        return False
    if user.is_superuser:
        return True
    return user.groups.filter(name__in=ROLES_DIRTEC_GRUPOS).exists()


def empresas_del_usuario(user):
    if not getattr(user, 'is_authenticated', False):
        return EmpresaSuscriptora.objects.none()
    if usuario_es_dirtec_operativo(user):
        return EmpresaSuscriptora.objects.filter(activo=True).order_by('nombre_comercial')
    return EmpresaSuscriptora.objects.filter(
        membresias__usuario=user,
        membresias__activo=True,
        activo=True,
    ).distinct().order_by('nombre_comercial')


def empresa_principal_usuario(user):
    if not getattr(user, 'is_authenticated', False):
        return None
    if usuario_es_dirtec_operativo(user):
        return empresas_del_usuario(user).first()

    from core.services.tenant_context import resolver_tenant_usuario
    return resolver_tenant_usuario(user).empresa


def roles_usuario_empresa(user, empresa):
    if not getattr(user, 'is_authenticated', False) or not empresa:
        return set()
    return set(
        MembresiaEmpresa.objects.filter(
            usuario=user,
            empresa=empresa,
            activo=True,
        ).values_list('rol', flat=True)
    )
