from django.contrib.auth.views import LoginView
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.shortcuts import redirect

from core.services.auditoria import registrar_auditoria
from core.services.permisos import empresa_principal_usuario, roles_usuario_empresa, usuario_es_dirtec_operativo
from core.services.suscripciones import evaluar_suscripcion_empresa


LOGIN_FAILURE_LIMIT = 10
LOGIN_FAILURE_WINDOW_SECONDS = 15 * 60


def _login_throttle_key(request):
    identifier = (request.POST.get('username') or '').strip().lower()
    ip = request.META.get('HTTP_X_FORWARDED_FOR', '').split(',')[0].strip() or request.META.get('REMOTE_ADDR', '')
    safe_identifier = ''.join(ch for ch in identifier if ch.isalnum() or ch in '._-')[:80]
    safe_ip = ''.join(ch for ch in ip if ch.isalnum() or ch in '.:-')[:64]
    return f'login-fail:{safe_ip}:{safe_identifier}'


def _login_failure_count(request):
    return int(cache.get(_login_throttle_key(request), 0) or 0)


class LoginCentralView(LoginView):
    template_name = 'core/login.html'
    redirect_authenticated_user = True

    def post(self, request, *args, **kwargs):
        if _login_failure_count(request) >= LOGIN_FAILURE_LIMIT:
            registrar_auditoria(
                usuario=None,
                empresa=None,
                accion='LOGIN_BLOQUEADO_TEMPORAL',
                modelo='auth.User',
                descripcion='Intento de login bloqueado temporalmente por demasiados fallos.',
                request=request,
            )
            messages.error(
                request,
                'Demasiados intentos fallidos. Espera unos minutos antes de volver a intentar.',
            )
            return self.get(request, *args, **kwargs)
        return super().post(request, *args, **kwargs)

    def form_invalid(self, form):
        key = _login_throttle_key(self.request)
        current = int(cache.get(key, 0) or 0) + 1
        cache.set(key, current, timeout=LOGIN_FAILURE_WINDOW_SECONDS)
        registrar_auditoria(
            usuario=None,
            empresa=None,
            accion='LOGIN_FALLIDO',
            modelo='auth.User',
            descripcion=f'Intento de login fallido ({current}/{LOGIN_FAILURE_LIMIT}).',
            request=self.request,
        )
        return super().form_invalid(form)

    def form_valid(self, form):
        cache.delete(_login_throttle_key(self.request))
        response = super().form_valid(form)
        registrar_auditoria(
            usuario=self.request.user,
            empresa=empresa_principal_usuario(self.request.user),
            accion='LOGIN_EXITOSO',
            modelo='auth.User',
            objeto_id=self.request.user.id,
            descripcion='Inicio de sesion desde login central.',
            request=self.request,
        )
        return response


@login_required(login_url='/login/')
def redirigir_por_rol(request):
    if usuario_es_dirtec_operativo(request.user):
        return redirect('/dirtec/dashboard/')

    empresa = empresa_principal_usuario(request.user)
    estado_saas = evaluar_suscripcion_empresa(empresa)
    if not estado_saas.puede_acceder:
        return redirect('suscripcion_estado')

    roles = roles_usuario_empresa(
        request.user,
        empresa,
    )

    # External portal identities never enter the company backoffice.
    if 'CLIENTE' in roles:
        return redirect('/cliente/dashboard/')

    if (
        'PROVEEDOR' in roles
        or hasattr(
            request.user,
            'perfil_proveedor',
        )
    ):
        return redirect('/proveedor/dashboard/')

    if (
        empresa
        and roles.intersection(
            {'ADMIN_EMPRESA', 'VENTAS'}
        )
    ):
        return redirect(
            f'/empresa/{empresa.slug}/dashboard/'
        )

    if (
        empresa
        and 'WEDDING_PLANNER' in roles
    ):
        return redirect(
            f'/empresa/{empresa.slug}/wedding-planner/dashboard/'
        )

    # Relationship fallbacks for older accounts not yet migrated to memberships.
    if request.user.eventos_cliente.exists():
        return redirect('/cliente/dashboard/')

    return redirect('/dashboard/')
