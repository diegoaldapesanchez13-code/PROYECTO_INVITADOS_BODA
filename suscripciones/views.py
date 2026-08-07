from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from core.services.permisos import empresa_principal_usuario
from core.services.suscripciones import evaluar_suscripcion_empresa


@login_required(login_url='/login/')
def estado_suscripcion(request):
    empresa = empresa_principal_usuario(request.user)
    estado = getattr(request, 'saas_estado', None) or evaluar_suscripcion_empresa(empresa)
    return render(
        request,
        'suscripciones/estado_suscripcion.html',
        {
            'empresa': estado.empresa,
            'estado': estado,
            'suscripcion': estado.suscripcion,
        },
    )
