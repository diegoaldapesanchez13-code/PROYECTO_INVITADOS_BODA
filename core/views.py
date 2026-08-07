from django.contrib.auth.views import LoginView
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect

from core.services.auditoria import registrar_auditoria
from core.services.permisos import empresa_principal_usuario, roles_usuario_empresa, usuario_es_dirtec_operativo
from core.services.suscripciones import evaluar_suscripcion_empresa


class LoginCentralView(LoginView):
    template_name = 'core/login.html'
    redirect_authenticated_user = True

    def form_valid(self, form):
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

    roles = roles_usuario_empresa(request.user, empresa)
    if empresa and roles.intersection({'ADMIN_EMPRESA', 'VENTAS'}):
        return redirect(f'/empresa/{empresa.slug}/dashboard/')
    if empresa and 'WEDDING_PLANNER' in roles:
        return redirect(f'/empresa/{empresa.slug}/wedding-planner/dashboard/')
    if request.user.eventos_cliente.exists():
        return redirect('/cliente/dashboard/')
    if hasattr(request.user, 'perfil_proveedor'):
        return redirect('/proveedor/dashboard/')
    return redirect('/dashboard/')
