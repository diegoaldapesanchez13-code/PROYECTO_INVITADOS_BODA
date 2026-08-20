from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from core.services.auditoria import registrar_auditoria
from invitaciones.guest_domain import asegurar_roster_grupo
from invitaciones.models import Grupoinvitacion, Invitado

from .workspace_guests_capacity import validar_nuevos_lugares


def _sync_group_legacy(grupo):
    invitados = list(grupo.invitados.order_by("orden", "id"))
    total = len(invitados)
    yes_count = sum(1 for invitado in invitados if invitado.asistira is True)
    responded = sum(1 for invitado in invitados if invitado.asistira is not None)
    pending = total - responded

    grupo.cantidad_confirmada = yes_count
    grupo.confirmado = total > 0 and pending == 0
    grupo.fecha_confirmacion = timezone.now() if responded else None

    if not total or pending:
        grupo.asistira = None
    else:
        grupo.asistira = yes_count > 0

    grupo.cantidad_maxima = max(
        grupo.invitados.filter(es_acompanante_extra=False).count(),
        1,
    )
    grupo.save(update_fields=[
        "cantidad_confirmada",
        "confirmado",
        "fecha_confirmacion",
        "asistira",
        "cantidad_maxima",
    ])


@transaction.atomic
def crear_grupo(*, evento, cleaned_data, user=None, request=None):
    tipo = cleaned_data["tipo"]
    integrantes = cleaned_data.get("integrantes_lista") or []
    extras = int(cleaned_data.get("cantidad_extra_permitida") or 0)
    nominales = len(integrantes) if tipo == "FAMILIAR" else 1

    validar_nuevos_lugares(evento, nominales + extras)

    grupo = Grupoinvitacion.objects.create(
        evento=evento,
        nombre_grupo=cleaned_data["nombre_grupo"].strip(),
        tipo=tipo,
        cantidad_maxima=max(nominales, 1),
        permitir_acompanantes_extra=bool(
            cleaned_data.get("permitir_acompanantes_extra")
        ),
        cantidad_extra_permitida=extras,
        telefono_contacto=cleaned_data.get("telefono_contacto") or None,
        correo_contacto=cleaned_data.get("correo_contacto") or None,
    )

    if tipo == "FAMILIAR":
        for orden, nombre in enumerate(integrantes, 1):
            Invitado.objects.create(
                grupo=grupo,
                nombre=nombre,
                tipo_persona="ADULTO",
                orden=orden,
            )

    asegurar_roster_grupo(grupo)

    registrar_auditoria(
        usuario=user,
        empresa=evento.empresa,
        evento=evento,
        accion="CREAR_GRUPO_INVITACION_K9",
        modelo="Grupoinvitacion",
        objeto_id=grupo.id,
        descripcion=f"Se creó invitación: {grupo.nombre_grupo}.",
        valores_nuevos={
            "tipo": grupo.tipo,
            "lugares": grupo.total_lugares,
        },
        request=request,
    )
    return grupo


@transaction.atomic
def editar_grupo(grupo, *, cleaned_data, user=None, request=None):
    grupo = Grupoinvitacion.objects.select_for_update().get(pk=grupo.pk)
    nominales = grupo.invitados.filter(es_acompanante_extra=False).count()
    extras = (
        int(cleaned_data.get("cantidad_extra_permitida") or 0)
        if cleaned_data.get("permitir_acompanantes_extra")
        else 0
    )

    # Existing people who already said NO do not reserve capacity. For editing
    # the same group we exclude it and reserve its proposed roster again.
    validar_nuevos_lugares(
        grupo.evento,
        nominales + extras,
        excluir_grupo=grupo,
    )

    before = {
        "nombre": grupo.nombre_grupo,
        "extras": grupo.cantidad_extra_permitida,
    }

    grupo.nombre_grupo = cleaned_data["nombre_grupo"].strip()
    grupo.permitir_acompanantes_extra = bool(
        cleaned_data.get("permitir_acompanantes_extra")
    )
    grupo.cantidad_extra_permitida = extras
    grupo.telefono_contacto = cleaned_data.get("telefono_contacto") or None
    grupo.correo_contacto = cleaned_data.get("correo_contacto") or None
    grupo.save()

    asegurar_roster_grupo(grupo)
    _sync_group_legacy(grupo)

    registrar_auditoria(
        usuario=user,
        empresa=grupo.evento.empresa,
        evento=grupo.evento,
        accion="EDITAR_GRUPO_INVITACION_K9",
        modelo="Grupoinvitacion",
        objeto_id=grupo.id,
        descripcion=f"Se actualizó invitación: {grupo.nombre_grupo}.",
        valores_anteriores=before,
        valores_nuevos={
            "nombre": grupo.nombre_grupo,
            "extras": grupo.cantidad_extra_permitida,
        },
        request=request,
    )
    return grupo


@transaction.atomic
def agregar_persona(grupo, *, cleaned_data, user=None, request=None):
    if grupo.es_personal:
        raise ValidationError(
            "Una invitación personal usa su persona principal y acompañantes autorizados."
        )

    validar_nuevos_lugares(grupo.evento, 1)

    invitado = Invitado(
        grupo=grupo,
        orden=grupo.invitados.count() + 1,
    )
    for field, value in cleaned_data.items():
        setattr(invitado, field, value)
    invitado.full_clean()
    invitado.save()

    grupo.cantidad_maxima = max(
        grupo.invitados.filter(es_acompanante_extra=False).count(),
        1,
    )
    grupo.save(update_fields=["cantidad_maxima"])

    registrar_auditoria(
        usuario=user,
        empresa=grupo.evento.empresa,
        evento=grupo.evento,
        accion="AGREGAR_INVITADO_K9",
        modelo="Invitado",
        objeto_id=invitado.id,
        descripcion=f"Se agregó invitado: {invitado}.",
        request=request,
    )
    return invitado


@transaction.atomic
def guardar_persona(invitado, *, cleaned_data, user=None, request=None):
    invitado = Invitado.objects.select_for_update().get(pk=invitado.pk)
    before = {
        "nombre": str(invitado),
        "tipo_persona": invitado.tipo_persona,
        "menu": invitado.menu_asignado,
    }
    for field, value in cleaned_data.items():
        setattr(invitado, field, value)
    invitado.full_clean()
    invitado.save()

    registrar_auditoria(
        usuario=user,
        empresa=invitado.grupo.evento.empresa,
        evento=invitado.grupo.evento,
        accion="EDITAR_INVITADO_K9",
        modelo="Invitado",
        objeto_id=invitado.id,
        descripcion=f"Se actualizó invitado: {invitado}.",
        valores_anteriores=before,
        valores_nuevos={
            "nombre": str(invitado),
            "tipo_persona": invitado.tipo_persona,
            "menu": invitado.menu_asignado,
        },
        request=request,
    )
    return invitado


@transaction.atomic
def registrar_respuesta_manual(invitado, respuesta, *, user=None, request=None):
    invitado = Invitado.objects.select_for_update().select_related(
        "grupo", "grupo__evento"
    ).get(pk=invitado.pk)

    anterior = invitado.asistira
    if respuesta == "SI":
        invitado.asistira = True
        invitado.fecha_confirmacion = timezone.now()
    elif respuesta == "NO":
        invitado.asistira = False
        invitado.fecha_confirmacion = timezone.now()
    elif respuesta == "PENDIENTE":
        invitado.asistira = None
        invitado.fecha_confirmacion = None
    else:
        raise ValidationError("Respuesta inválida.")

    invitado.save(update_fields=["asistira", "fecha_confirmacion"])
    _sync_group_legacy(invitado.grupo)

    registrar_auditoria(
        usuario=user,
        empresa=invitado.grupo.evento.empresa,
        evento=invitado.grupo.evento,
        accion="AJUSTAR_RSVP_INVITADO_K9",
        modelo="Invitado",
        objeto_id=invitado.id,
        descripcion=f"Se ajustó RSVP manualmente: {invitado}.",
        valores_anteriores={"asistira": anterior},
        valores_nuevos={"asistira": invitado.asistira},
        request=request,
    )
    return invitado


def grupo_puede_eliminarse(grupo):
    if grupo.invitados.exclude(asistira__isnull=True).exists():
        return False, "Ya tiene respuestas RSVP."
    if grupo.invitados.filter(asignaciones_mesa__isnull=False).exists():
        return False, "Tiene personas asignadas a mesa."
    return True, ""


@transaction.atomic
def eliminar_grupo_error(grupo, *, user=None, request=None):
    permitido, motivo = grupo_puede_eliminarse(grupo)
    if not permitido:
        raise ValidationError(motivo)

    evento = grupo.evento
    grupo_id = grupo.id
    nombre = grupo.nombre_grupo

    registrar_auditoria(
        usuario=user,
        empresa=evento.empresa,
        evento=evento,
        accion="ELIMINAR_GRUPO_INVITACION_ERROR_K9",
        modelo="Grupoinvitacion",
        objeto_id=grupo_id,
        descripcion=f"Se eliminó invitación sin historial: {nombre}.",
        request=request,
    )
    grupo.delete()
    return grupo_id


@transaction.atomic
def eliminar_persona_error(invitado, *, user=None, request=None):
    if invitado.es_acompanante_extra:
        raise ValidationError("Los acompañantes se administran desde el grupo.")
    if invitado.grupo.es_personal:
        raise ValidationError(
            "No puedes eliminar la persona principal de una invitación personal."
        )
    if invitado.asistira is not None:
        raise ValidationError("La persona ya tiene una respuesta RSVP.")
    if invitado.asignaciones_mesa.exists():
        raise ValidationError("La persona ya tiene mesa.")

    grupo = invitado.grupo
    invitado_id = invitado.id
    nombre = str(invitado)

    registrar_auditoria(
        usuario=user,
        empresa=grupo.evento.empresa,
        evento=grupo.evento,
        accion="ELIMINAR_INVITADO_ERROR_K9",
        modelo="Invitado",
        objeto_id=invitado_id,
        descripcion=f"Se eliminó invitado sin historial: {nombre}.",
        request=request,
    )
    invitado.delete()

    grupo.cantidad_maxima = max(
        grupo.invitados.filter(es_acompanante_extra=False).count(),
        1,
    )
    grupo.save(update_fields=["cantidad_maxima"])
    return invitado_id
