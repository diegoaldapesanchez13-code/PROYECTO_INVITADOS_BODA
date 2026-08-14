from django.shortcuts import redirect

from core.services.auditoria import registrar_auditoria
from core.services.permisos import empresa_principal_usuario, usuario_es_dirtec_operativo
from core.services.suscripciones import evaluar_suscripcion_empresa


class SaasSubscriptionMiddleware:
    PATHS_PUBLICOS = (
        '/admin/',
        '/static/',
        '/media/',
        '/invitacion/',
        '/suscripcion/estado/',
    )

    PATHS_OPERATIVOS = (
        '/dirtec/',
        '/empresa/',
        '/cliente/',
        '/proveedor/',
        '/catalogo/',
        '/colaboracion/',
        '/presupuesto/',
        '/dashboard/',
        '/portal/',
        '/api/',
        '/exportar-',
    )

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.saas_estado = None
        if self.debe_validar(request):
            empresa = empresa_principal_usuario(request.user)
            estado = evaluar_suscripcion_empresa(empresa)
            request.saas_estado = estado

            if not estado.puede_acceder:
                registrar_auditoria(
                    usuario=request.user,
                    empresa=estado.empresa,
                    accion='ACCESO_BLOQUEADO_SUSCRIPCION',
                    modelo='SuscripcionEmpresa',
                    objeto_id=getattr(estado.suscripcion, 'id', ''),
                    descripcion=estado.mensaje,
                    request=request,
                )
                return redirect('suscripcion_estado')

            if request.method not in ('GET', 'HEAD', 'OPTIONS', 'TRACE') and not estado.puede_escribir:
                registrar_auditoria(
                    usuario=request.user,
                    empresa=estado.empresa,
                    accion='ESCRITURA_BLOQUEADA_SUSCRIPCION',
                    modelo='SuscripcionEmpresa',
                    objeto_id=getattr(estado.suscripcion, 'id', ''),
                    descripcion=estado.mensaje,
                    request=request,
                )
                return redirect('suscripcion_estado')

        return self.get_response(request)

    def debe_validar(self, request):
        path = request.path_info or '/'
        if any(path.startswith(publico) for publico in self.PATHS_PUBLICOS):
            return False
        if not any(path.startswith(operativo) for operativo in self.PATHS_OPERATIVOS):
            return False
        user = getattr(request, 'user', None)
        if not getattr(user, 'is_authenticated', False):
            return False
        if usuario_es_dirtec_operativo(user):
            return False
        return True
