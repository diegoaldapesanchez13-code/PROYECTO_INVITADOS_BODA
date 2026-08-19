from urllib.parse import parse_qs, urlsplit

from django.contrib.auth.views import LoginView
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.shortcuts import redirect
from django.urls import Resolver404, resolve
from django.utils.http import url_has_allowed_host_and_scheme

from core.services.auditoria import registrar_auditoria
from core.services.authorization import Actions, usuario_puede_evento
from core.services.permisos import empresa_principal_usuario, roles_usuario_empresa, usuario_es_dirtec_operativo
from core.services.suscripciones import evaluar_suscripcion_empresa
from organizaciones.models import EmpresaSuscriptora


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


def _usuario_es_cliente(user):
    empresa = empresa_principal_usuario(user)
    return (
        'CLIENTE' in roles_usuario_empresa(user, empresa)
        or user.eventos_cliente.exists()
    )


def _usuario_es_proveedor(user):
    empresa = empresa_principal_usuario(user)
    return (
        'PROVEEDOR' in roles_usuario_empresa(user, empresa)
        or hasattr(user, 'perfil_proveedor')
    )


def _usuario_puede_dashboard_empresa(user, empresa_slug, roles_permitidos):
    empresa = EmpresaSuscriptora.objects.filter(slug=empresa_slug).first()
    if not empresa:
        return False
    return bool(roles_usuario_empresa(user, empresa).intersection(roles_permitidos))


def _next_query_autorizada(user, split_url):
    if not split_url.query:
        return True
    query = parse_qs(split_url.query)
    if set(query) != {'evento'} or len(query['evento']) != 1:
        return False
    try:
        evento_id = int(query['evento'][0])
    except (TypeError, ValueError):
        return False
    from invitaciones.models import EventoBoda

    evento = EventoBoda.objects.filter(id=evento_id).select_related('empresa').first()
    return usuario_puede_evento(user, evento, Actions.EVENT_VIEW)


def _next_autorizado_para_usuario(user, redirect_to, request):
    if not redirect_to or not url_has_allowed_host_and_scheme(
        redirect_to,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return False

    split_url = urlsplit(redirect_to)
    if not _next_query_autorizada(user, split_url):
        return False
    path = split_url.path
    try:
        match = resolve(path)
    except Resolver404:
        return False

    url_name = match.url_name
    if url_name == 'redirigir_por_rol':
        return True
    if url_name in {'dirtec_dashboard', 'dashboard_dirtec'}:
        return usuario_es_dirtec_operativo(user)
    if url_name in {'cliente_dashboard', 'portal_cliente'}:
        return _usuario_es_cliente(user)
    if url_name in {'proveedor_dashboard', 'portal_proveedor'}:
        return _usuario_es_proveedor(user)
    if url_name in {'empresa_dashboard', 'dashboard_empresa'}:
        empresa_slug = match.kwargs.get('empresa_slug')
        if not empresa_slug:
            empresa = empresa_principal_usuario(user)
            return bool(
                empresa
                and roles_usuario_empresa(user, empresa).intersection({'ADMIN_EMPRESA', 'VENTAS'})
            )
        return _usuario_puede_dashboard_empresa(user, empresa_slug, {'ADMIN_EMPRESA', 'VENTAS'})
    if url_name in {'planner_dashboard_empresa', 'planner_dashboard_empresa_alias', 'dashboard_planner'}:
        empresa_slug = match.kwargs.get('empresa_slug')
        if not empresa_slug:
            empresa = empresa_principal_usuario(user)
            return bool(empresa and 'WEDDING_PLANNER' in roles_usuario_empresa(user, empresa))
        return _usuario_puede_dashboard_empresa(user, empresa_slug, {'WEDDING_PLANNER'})
    return False


class LoginCentralView(LoginView):
    template_name = 'core/login.html'
    redirect_authenticated_user = True

    def get_redirect_url(self):
        redirect_to = super().get_redirect_url()
        user = getattr(self, '_usuario_login_exitoso', None) or self.request.user
        if _next_autorizado_para_usuario(user, redirect_to, self.request):
            return redirect_to
        return ''

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
        self._usuario_login_exitoso = form.get_user()
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
            f'/empresa/{empresa.slug}/planner/dashboard/'
        )

    # Relationship fallbacks for older accounts not yet migrated to memberships.
    if request.user.eventos_cliente.exists():
        return redirect('/cliente/dashboard/')

    return redirect('/dashboard/')
