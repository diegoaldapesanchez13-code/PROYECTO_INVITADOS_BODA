import logging

from django.contrib import messages
from django.shortcuts import redirect


logger = logging.getLogger(__name__)


def block_replaced_legacy_post(
    request,
    *,
    endpoint,
    replacement,
    redirect_to,
    empresa=None,
    evento=None,
):
    url_name = getattr(getattr(request, "resolver_match", None), "url_name", None)
    user_id = getattr(getattr(request, "user", None), "id", None)
    empresa_id = getattr(empresa, "id", None)
    evento_id = getattr(evento, "id", None)
    logger.info(
        "Blocked replaced legacy POST endpoint=%s url_name=%s method=%s user=%s empresa=%s evento=%s replacement=%s",
        endpoint,
        url_name,
        request.method,
        user_id,
        empresa_id,
        evento_id,
        replacement,
    )
    messages.warning(
        request,
        "Esta accion legacy fue reemplazada. Usa el workspace K9 para continuar.",
    )
    return redirect(redirect_to)
