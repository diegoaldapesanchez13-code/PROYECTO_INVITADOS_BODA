def obtener_ip_request(request):
    forwarded = request.META.get('HTTP_X_FORWARDED_FOR') if request else None
    if forwarded:
        return forwarded.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR') if request else None


def registrar_auditoria(
    *,
    usuario=None,
    empresa=None,
    evento=None,
    accion,
    modelo='',
    objeto_id='',
    descripcion='',
    valores_anteriores=None,
    valores_nuevos=None,
    request=None,
):
    from auditoria.models import RegistroAuditoria

    return RegistroAuditoria.objects.create(
        usuario=usuario if getattr(usuario, 'is_authenticated', False) else None,
        empresa=empresa,
        evento=evento,
        accion=accion,
        modelo=modelo,
        objeto_id=str(objeto_id or ''),
        descripcion=descripcion,
        valores_anteriores=valores_anteriores or {},
        valores_nuevos=valores_nuevos or {},
        direccion_ip=obtener_ip_request(request),
        user_agent=request.META.get('HTTP_USER_AGENT', '') if request else '',
    )
