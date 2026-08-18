from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render

from core.services.tenant_context import validar_slug_tenant
from invitaciones.models import EventoBoda

from .services import resumen_financiero_interno


@login_required
def finanzas_evento(request, empresa_slug, evento_id):
    context = validar_slug_tenant(request, empresa_slug)
    empresa = context.empresa
    evento = get_object_or_404(EventoBoda, pk=evento_id, empresa=empresa)
    resumen = resumen_financiero_interno(evento, user=request.user)
    return render(
        request,
        'presupuesto/finanzas_evento.html',
        {
            'empresa': empresa,
            'evento': evento,
            'resumen': resumen,
        },
    )
