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
    empresa = empresas_del_usuario(user).first()
    if empresa:
        return empresa

    from invitaciones.models import EventoBoda
    from proveedores.models import Proveedor

    evento_cliente = EventoBoda.objects.filter(
        clientes=user,
        empresa__isnull=False,
        empresa__activo=True,
    ).select_related('empresa').first()
    if evento_cliente:
        return evento_cliente.empresa

    proveedor = Proveedor.objects.filter(
        usuario=user,
        empresa__isnull=False,
        empresa__activo=True,
        activo=True,
    ).select_related('empresa').first()
    return proveedor.empresa if proveedor else None


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
