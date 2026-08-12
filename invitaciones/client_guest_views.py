from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views.decorators.http import require_POST

from eventos.models import ParticipanteEvento
from .guest_domain import asegurar_roster_grupo
from .models import EventoBoda, Grupoinvitacion, Invitado


def _es_cliente(user, evento):
    return evento.clientes.filter(id=user.id).exists() or ParticipanteEvento.objects.filter(
        evento=evento,
        usuario=user,
        rol="CLIENTE",
        activo=True,
    ).exists()


def _evento_cliente(user, evento_id):
    evento = get_object_or_404(EventoBoda, pk=evento_id)
    if not _es_cliente(user, evento):
        raise PermissionDenied("No tienes acceso a los invitados de este evento.")
    return evento


def _redirect(evento, fragment="invitados"):
    return redirect(f"{reverse('portal_cliente')}?evento={evento.id}#{fragment}")


def _int(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _ocupacion(evento, excluir_grupo=None):
    qs = Invitado.objects.filter(grupo__evento=evento)
    if excluir_grupo:
        qs = qs.exclude(grupo=excluir_grupo)
    return qs.count()


def _validar_capacidad(evento, nueva_cantidad, *, excluir_grupo=None):
    capacidad = int(evento.capacidad_contratada or 0)
    if not capacidad:
        return
    actual = _ocupacion(evento, excluir_grupo=excluir_grupo)
    if actual + max(int(nueva_cantidad or 0), 0) > capacidad:
        raise ValidationError(
            f"La capacidad contratada es de {capacidad} lugares. "
            f"Disponibles: {max(capacidad - actual, 0)}."
        )


def _lineas_familia(texto):
    return [linea.strip() for linea in (texto or "").splitlines() if linea.strip()]


@login_required
@require_POST
@transaction.atomic
def crear_grupo_cliente(request, evento_id):
    evento = _evento_cliente(request.user, evento_id)
    nombre = (request.POST.get("nombre_grupo") or "").strip()
    tipo = request.POST.get("tipo_grupo") or "PERSONAL"
    if tipo not in dict(Grupoinvitacion.TIPO_INVITACION):
        tipo = "PERSONAL"
    if not nombre:
        messages.error(request, "Escribe el nombre de la invitación o familia.")
        return _redirect(evento)

    extras = max(_int(request.POST.get("cantidad_extra_permitida"), 0), 0)
    permitir_extras = request.POST.get("permitir_acompanantes_extra") == "on"
    if not permitir_extras:
        extras = 0

    integrantes = _lineas_familia(request.POST.get("integrantes"))
    if tipo == "FAMILIAR" and not integrantes:
        messages.error(request, "Agrega al menos una persona para una invitación familiar.")
        return _redirect(evento)
    nominales_estimados = len(integrantes) if tipo == "FAMILIAR" else 1
    try:
        _validar_capacidad(evento, nominales_estimados + extras)
    except ValidationError as exc:
        messages.error(request, " · ".join(exc.messages))
        return _redirect(evento)

    grupo = Grupoinvitacion.objects.create(
        evento=evento,
        nombre_grupo=nombre,
        tipo=tipo,
        cantidad_maxima=max(nominales_estimados, 1),
        permitir_acompanantes_extra=permitir_extras,
        cantidad_extra_permitida=extras,
        telefono_contacto=(request.POST.get("telefono_contacto") or "").strip() or None,
        correo_contacto=(request.POST.get("correo_contacto") or "").strip() or None,
    )
    if tipo == "FAMILIAR":
        for orden, nombre_persona in enumerate(integrantes, 1):
            Invitado.objects.create(
                grupo=grupo,
                nombre=nombre_persona,
                tipo_persona="ADULTO",
                orden=orden,
            )
    asegurar_roster_grupo(grupo)
    messages.success(request, "Invitación creada.")
    return _redirect(evento)


@login_required
@require_POST
@transaction.atomic
def editar_grupo_cliente(request, grupo_id):
    grupo = get_object_or_404(Grupoinvitacion.objects.select_related("evento"), pk=grupo_id)
    evento = _evento_cliente(request.user, grupo.evento_id)

    nombre = (request.POST.get("nombre_grupo") or "").strip()
    if nombre:
        grupo.nombre_grupo = nombre
    permitir_extras = request.POST.get("permitir_acompanantes_extra") == "on"
    extras = max(_int(request.POST.get("cantidad_extra_permitida"), 0), 0) if permitir_extras else 0

    nominales = grupo.invitados.filter(es_acompanante_extra=False).count()
    try:
        _validar_capacidad(
            evento,
            nominales + extras,
            excluir_grupo=grupo,
        )
    except ValidationError as exc:
        messages.error(request, " · ".join(exc.messages))
        return _redirect(evento)
    grupo.permitir_acompanantes_extra = permitir_extras
    grupo.cantidad_extra_permitida = extras
    grupo.telefono_contacto = (request.POST.get("telefono_contacto") or "").strip() or None
    grupo.correo_contacto = (request.POST.get("correo_contacto") or "").strip() or None
    savepoint = transaction.savepoint()
    try:
        grupo.save()
        asegurar_roster_grupo(grupo)
    except ValidationError as exc:
        transaction.savepoint_rollback(savepoint)
        messages.error(request, " · ".join(exc.messages))
        return _redirect(evento)
    transaction.savepoint_commit(savepoint)
    messages.success(request, "Invitación actualizada.")
    return _redirect(evento)


@login_required
@require_POST
@transaction.atomic
def eliminar_grupo_cliente(request, grupo_id):
    grupo = get_object_or_404(Grupoinvitacion.objects.select_related("evento"), pk=grupo_id)
    evento = _evento_cliente(request.user, grupo.evento_id)
    tiene_respuestas = grupo.invitados.exclude(asistira__isnull=True).exists()
    tiene_mesas = Invitado.objects.filter(
        grupo=grupo,
        asignaciones_mesa__isnull=False,
    ).exists()
    if tiene_respuestas or tiene_mesas:
        messages.error(
            request,
            "No puedes eliminar esta invitación porque ya tiene RSVP o personas asignadas a mesa.",
        )
        return _redirect(evento)
    grupo.delete()
    messages.success(request, "Invitación eliminada.")
    return _redirect(evento)


@login_required
@require_POST
@transaction.atomic
def agregar_invitado_cliente(request, grupo_id):
    grupo = get_object_or_404(Grupoinvitacion.objects.select_related("evento"), pk=grupo_id)
    evento = _evento_cliente(request.user, grupo.evento_id)
    if grupo.es_personal:
        messages.error(request, "Una invitación personal usa una persona principal y acompañantes autorizados.")
        return _redirect(evento)

    nombre = (request.POST.get("nombre") or "").strip()
    if not nombre:
        messages.error(request, "Escribe el nombre del invitado.")
        return _redirect(evento)
    try:
        _validar_capacidad(evento, 1)
    except ValidationError as exc:
        messages.error(request, " · ".join(exc.messages))
        return _redirect(evento)

    tipo = request.POST.get("tipo_persona") or "ADULTO"
    if tipo not in dict(Invitado.TIPO_PERSONA):
        tipo = "ADULTO"
    orden = grupo.invitados.count() + 1
    Invitado.objects.create(
        grupo=grupo,
        nombre=nombre,
        apellidos=(request.POST.get("apellidos") or "").strip() or None,
        telefono=(request.POST.get("telefono") or "").strip() or None,
        correo=(request.POST.get("correo") or "").strip() or None,
        tipo_persona=tipo,
        orden=orden,
    )
    grupo.cantidad_maxima = max(grupo.invitados.count(), 1)
    grupo.save(update_fields=["cantidad_maxima"])
    messages.success(request, "Invitado agregado.")
    return _redirect(evento)


@login_required
@require_POST
@transaction.atomic
def editar_invitado_cliente(request, invitado_id):
    invitado = get_object_or_404(
        Invitado.objects.select_related("grupo", "grupo__evento"),
        pk=invitado_id,
        es_acompanante_extra=False,
    )
    evento = _evento_cliente(request.user, invitado.grupo.evento_id)
    invitado.nombre = (request.POST.get("nombre") or "").strip() or invitado.nombre
    invitado.apellidos = (request.POST.get("apellidos") or "").strip() or None
    invitado.telefono = (request.POST.get("telefono") or "").strip() or None
    invitado.correo = (request.POST.get("correo") or "").strip() or None
    tipo = request.POST.get("tipo_persona") or invitado.tipo_persona
    if tipo in dict(Invitado.TIPO_PERSONA):
        invitado.tipo_persona = tipo
    invitado.save()
    messages.success(request, "Invitado actualizado.")
    return _redirect(evento)


@login_required
@require_POST
@transaction.atomic
def eliminar_invitado_cliente(request, invitado_id):
    invitado = get_object_or_404(
        Invitado.objects.select_related("grupo", "grupo__evento"),
        pk=invitado_id,
        es_acompanante_extra=False,
    )
    evento = _evento_cliente(request.user, invitado.grupo.evento_id)
    if invitado.grupo.es_personal:
        messages.error(request, "No puedes eliminar la persona principal de una invitación personal.")
        return _redirect(evento)
    if invitado.asistira is not None or invitado.asignaciones_mesa.exists():
        messages.error(request, "No puedes eliminar a una persona que ya respondió RSVP o tiene mesa.")
        return _redirect(evento)
    grupo = invitado.grupo
    invitado.delete()
    grupo.cantidad_maxima = max(grupo.invitados.filter(es_acompanante_extra=False).count(), 1)
    grupo.save(update_fields=["cantidad_maxima"])
    messages.success(request, "Invitado eliminado.")
    return _redirect(evento)
