from urllib.parse import quote

from invitaciones.guest_analytics import resumen_invitados_evento
from invitaciones.models import Grupoinvitacion


def _base_url(request):
    return request.build_absolute_uri("/").rstrip("/")


def _share_message(grupo, link):
    saludo = (
        f"Hola Familia {grupo.nombre_grupo}"
        if grupo.es_familiar
        else f"Hola {grupo.nombre_grupo}"
    )
    return (
        f"{saludo}, te compartimos nuestra invitación digital.\n\n"
        f"Puedes verla y confirmar tu asistencia aquí:\n{link}"
    )


def construir_contexto_invitados_cliente_v3(evento, request):
    grupos = list(
        Grupoinvitacion.objects.filter(evento=evento)
        .prefetch_related("invitados__asignaciones_mesa")
        .order_by("tipo", "nombre_grupo", "id")
    )
    base = _base_url(request)
    grupos_ui = []
    for grupo in grupos:
        link = f"{base}/invitacion/{grupo.codigo}/"
        mensaje = _share_message(grupo, link)
        telefono = (
            (grupo.telefono_contacto or "")
            .replace(" ", "")
            .replace("+", "")
            .replace("-", "")
            .replace("(", "")
            .replace(")", "")
        )
        whatsapp = (
            f"https://wa.me/{telefono}?text={quote(mensaje)}"
            if telefono
            else f"https://wa.me/?text={quote(mensaje)}"
        )
        nominales = list(
            grupo.invitados.filter(es_acompanante_extra=False).order_by("orden", "id")
        )
        extras = list(
            grupo.invitados.filter(es_acompanante_extra=True).order_by("orden", "id")
        )
        grupos_ui.append({
            "objeto": grupo,
            "nominales": nominales,
            "extras": extras,
            "link": link,
            "whatsapp": whatsapp,
            "total": grupo.total_lugares,
            "confirmados": grupo.lugares_asistiran,
            "no_asisten": grupo.lugares_no_asistiran,
            "pendientes": grupo.lugares_pendientes,
        })

    metricas = resumen_invitados_evento(evento)
    capacidad = int(evento.capacidad_contratada or 0)
    total = int(metricas["total_personas"] or 0)
    disponibles = max(capacidad - total, 0) if capacidad else None

    return {
        "cliente_grupos_v3": grupos_ui,
        "cliente_grupos_total_v3": len(grupos_ui),
        "cliente_invitados_metricas_v3": metricas,
        "cliente_capacidad_v3": capacidad,
        "cliente_lugares_disponibles_v3": disponibles,
        "cliente_capacidad_limitada_v3": bool(capacidad),
        "cliente_tipos_invitacion_v3": Grupoinvitacion.TIPO_INVITACION,
    }
