from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from proveedores.models import ServicioEvento
from documentos.models import DocumentoEvento
from itinerario.models import ActividadItinerario
from presupuesto.models import CategoriaGasto, GastoEvento, PagoEvento
from tareas.models import TareaEvento
from core.services.auditoria import registrar_auditoria

from .models import (AdjuntoMensajeServicio, ReferenciaServicio, TemaServicio, MensajeServicio, ConversacionServicio, DecisionServicio, CotizacionServicio, PropuestaServicioCliente, AprobacionServicio)
from .services import (
    canales_visibles_workspace,
    crear_tema_workspace,
    es_operador_servicio_workspace,
    es_cliente_servicio_workspace,
    es_proveedor_servicio_workspace,
    puede_escribir_canal_workspace,
    puede_ver_workspace,
    promover_adjunto_a_referencia,
    registrar_mensaje_workspace,
    eliminar_adjunto_workspace,
    eliminar_referencia_workspace,
    eliminar_mensaje_workspace,
    limpiar_historial_canal_workspace,
    archivar_tema_workspace,
)


def _servicio_queryset():
    return ServicioEvento.objects.select_related(
        "evento",
        "evento__empresa",
        "proveedor",
    )


def _workspace_url(servicio_id, canal=None):
    url = reverse("colaboracion_workspace_servicio", args=[servicio_id])
    return f"{url}?canal={canal}" if canal else url


@login_required
def servicio_workspace(request, servicio_id):
    servicio = get_object_or_404(_servicio_queryset(), id=servicio_id)
    if not puede_ver_workspace(request.user, servicio):
        raise PermissionDenied("No tienes acceso al workspace de este servicio.")

    canales = canales_visibles_workspace(request.user, servicio)
    canal_solicitado = request.GET.get("canal")
    prioridad = ["CLIENTE_PLANNER", "PLANNER_PROVEEDOR", "INTERNO"]
    canal_activo = (
        canal_solicitado
        if canal_solicitado in canales
        else next((item for item in prioridad if item in canales), None)
    )

    conversaciones = {
        conv.canal: conv
        for conv in servicio.conversaciones_workspace.prefetch_related(
            "mensajes__autor",
            "mensajes__tema",
            "mensajes__adjuntos",
        )
        if conv.canal in canales
    }
    conversacion = conversaciones.get(canal_activo)
    mensajes_qs = conversacion.mensajes.all() if conversacion else []
    total_mensajes_canal = conversacion.mensajes.count() if conversacion else 0

    temas = servicio.temas_workspace.filter(activo=True)
    referencias_qs = servicio.referencias_workspace.select_related(
        "tema",
        "adjunto_origen",
        "mensaje_origen",
        "mensaje_origen__conversacion",
    )
    if not es_operador_servicio_workspace(request.user, servicio):
        referencias_qs = referencias_qs.filter(
            mensaje_origen__conversacion__canal__in=canales
        )
    referencias = referencias_qs[:30]

    es_operador = es_operador_servicio_workspace(request.user, servicio)
    es_cliente = es_cliente_servicio_workspace(request.user, servicio)
    es_proveedor = es_proveedor_servicio_workspace(request.user, servicio)

    tareas_operativas = servicio.tareas_operativas.select_related("responsable").all() if es_operador else servicio.tareas_operativas.filter(responsable=request.user)
    actividades_agenda = servicio.actividades_agenda.select_related("responsable", "proveedor").prefetch_related("participantes__usuario", "participantes__proveedor").all()
    if es_proveedor and servicio.proveedor_id:
        actividades_agenda = actividades_agenda.filter(proveedor=servicio.proveedor)
    documentos_operativos = servicio.documentos_operativos.select_related("proveedor", "cargado_por").all()
    if es_cliente:
        documentos_operativos = documentos_operativos.filter(visible_cliente=True)
    elif es_proveedor:
        documentos_operativos = documentos_operativos.filter(
            Q(visible_proveedor=True) | Q(cargado_por=request.user)
        )
    gastos_operativos = servicio.gastos_operativos.select_related("categoria", "proveedor").prefetch_related("pagos") if es_operador else GastoEvento.objects.none()

    # K.8.6 también permite enlazar registros legacy que ya pertenecen al mismo evento.
    tareas_sin_servicio = TareaEvento.objects.filter(evento=servicio.evento, servicio_evento__isnull=True).order_by("fecha_limite", "titulo")[:50] if es_operador else []
    actividades_sin_servicio = ActividadItinerario.objects.filter(evento=servicio.evento, servicio_evento__isnull=True).order_by("fecha", "hora_inicio")[:50] if es_operador else []
    documentos_sin_servicio = DocumentoEvento.objects.filter(evento=servicio.evento, servicio_evento__isnull=True).order_by("-fecha_carga")[:50] if es_operador else []
    gastos_sin_servicio = GastoEvento.objects.filter(evento=servicio.evento, servicio_evento__isnull=True).order_by("fecha_limite", "concepto")[:50] if es_operador else []

    return render(
        request,
        "colaboracion/workspace_servicio.html",
        {
            "servicio": servicio,
            "canales": canales,
            "canal_activo": canal_activo,
            "mensajes_workspace": mensajes_qs,
            "total_mensajes_canal": total_mensajes_canal,
            "temas_workspace": temas,
            "referencias_workspace": referencias,
            "es_operador_workspace": es_operador,
            "es_cliente_workspace": es_cliente,
            "es_proveedor_workspace": es_proveedor,
            "canales_labels": dict(servicio.conversaciones_workspace.model.CANALES),
            "decisiones_workspace": servicio.decisiones_workspace.select_related("tema", "registrado_por")[:20],
            "cotizaciones_workspace": (
                servicio.cotizaciones_workspace.select_related("creado_por")[:20]
                if (es_operador or es_proveedor)
                else []
            ),
            "propuestas_workspace": servicio.propuestas_workspace.select_related("cotizacion", "enviado_por", "respondido_por")[:20],
            "aprobaciones_workspace": servicio.aprobaciones_workspace.select_related("tema", "solicitado_por", "respondido_por")[:20],
            "tareas_operativas": tareas_operativas[:30],
            "actividades_agenda": actividades_agenda[:30],
            "documentos_operativos": documentos_operativos[:30],
            "gastos_operativos": gastos_operativos[:30],
            "categorias_gasto": CategoriaGasto.objects.filter(activo=True).order_by("nombre") if es_operador else [],
            "tipos_documento_k86": DocumentoEvento.TIPOS,
            "prioridades_tarea_k86": TareaEvento.PRIORIDADES,
            "categorias_tarea_k86": TareaEvento.CATEGORIAS,
            "tipos_actividad_k8712": ActividadItinerario.TIPOS,
            "categorias_actividad_k86": ActividadItinerario.CATEGORIAS,
            "prioridades_actividad_k86": ActividadItinerario.PRIORIDADES,
            "metodos_pago_k86": PagoEvento.METODOS,
            "tareas_sin_servicio": tareas_sin_servicio,
            "actividades_sin_servicio": actividades_sin_servicio,
            "documentos_sin_servicio": documentos_sin_servicio,
            "gastos_sin_servicio": gastos_sin_servicio,
        },
    )


@login_required
@require_POST
@transaction.atomic
def crear_tema(request, servicio_id):
    servicio = get_object_or_404(_servicio_queryset(), id=servicio_id)
    if not es_operador_servicio_workspace(request.user, servicio):
        raise PermissionDenied("Solo el equipo operativo puede crear temas.")
    try:
        crear_tema_workspace(
            servicio,
            request.POST.get("nombre"),
            descripcion=request.POST.get("descripcion", ""),
            user=request.user,
        )
        messages.success(request, "Tema creado.")
    except (ValueError, Exception) as exc:
        # IntegrityError por nombre repetido se presenta de forma legible.
        messages.error(request, f"No se pudo crear el tema: {exc}")
    return redirect(_workspace_url(servicio.id, request.POST.get("canal")))


@login_required
@require_POST
@transaction.atomic
def enviar_mensaje_workspace(request, servicio_id):
    servicio = get_object_or_404(_servicio_queryset(), id=servicio_id)
    canal = request.POST.get("canal", "")
    if not puede_escribir_canal_workspace(request.user, servicio, canal):
        raise PermissionDenied("No puedes escribir en este canal.")

    tema = None
    tema_id = request.POST.get("tema_id")
    if tema_id:
        tema = get_object_or_404(TemaServicio, id=tema_id, servicio_evento=servicio, activo=True)

    archivos = request.FILES.getlist("archivos")
    try:
        registrar_mensaje_workspace(
            servicio,
            canal,
            user=request.user,
            texto=request.POST.get("texto", ""),
            tema=tema,
            archivos=archivos,
        )
        messages.success(request, "Mensaje enviado.")
    except ValueError as exc:
        messages.error(request, str(exc))
    return redirect(_workspace_url(servicio.id, canal))


@login_required
@require_POST
@transaction.atomic
def guardar_referencia(request, adjunto_id):
    adjunto = get_object_or_404(
        AdjuntoMensajeServicio.objects.select_related(
            "mensaje__conversacion__servicio_evento__evento",
            "mensaje__conversacion__servicio_evento__evento__empresa",
        ),
        id=adjunto_id,
    )
    servicio = adjunto.mensaje.conversacion.servicio_evento
    if not es_operador_servicio_workspace(request.user, servicio):
        raise PermissionDenied("Solo el equipo operativo puede registrar referencias.")

    tipo = request.POST.get("tipo", "REFERENCIA")
    if tipo not in dict(ReferenciaServicio.TIPOS):
        tipo = "REFERENCIA"
    promover_adjunto_a_referencia(
        adjunto,
        user=request.user,
        titulo=request.POST.get("titulo") or None,
        tipo=tipo,
    )
    messages.success(request, "Adjunto guardado como referencia del servicio.")
    return redirect(_workspace_url(servicio.id, adjunto.mensaje.conversacion.canal))


@login_required
@require_POST
@transaction.atomic
def eliminar_adjunto(request, adjunto_id):
    adjunto = get_object_or_404(
        AdjuntoMensajeServicio.objects.select_related(
            "mensaje__autor",
            "mensaje__conversacion__servicio_evento__evento",
            "mensaje__conversacion__servicio_evento__evento__empresa",
            "mensaje__conversacion__servicio_evento__proveedor",
        ),
        id=adjunto_id,
    )
    servicio = adjunto.mensaje.conversacion.servicio_evento
    canal = adjunto.mensaje.conversacion.canal

    try:
        eliminar_adjunto_workspace(adjunto, user=request.user)
        messages.success(request, "Archivo eliminado.")
    except PermissionDenied:
        raise
    except ValueError as exc:
        messages.error(request, str(exc))

    return redirect(_workspace_url(servicio.id, canal))

@login_required
@require_POST
@transaction.atomic
def eliminar_mensaje(request, mensaje_id):
    mensaje = get_object_or_404(
        MensajeServicio.objects.select_related(
            "conversacion__servicio_evento__evento",
            "conversacion__servicio_evento__evento__empresa",
            "conversacion__servicio_evento__proveedor",
        ).prefetch_related("adjuntos"),
        pk=mensaje_id,
    )
    servicio = mensaje.conversacion.servicio_evento
    canal = mensaje.conversacion.canal
    try:
        mensaje_id_original = mensaje.id
        eliminar_mensaje_workspace(mensaje, user=request.user)
        registrar_auditoria(
            usuario=request.user,
            empresa=servicio.evento.empresa,
            evento=servicio.evento,
            accion='ELIMINAR_MENSAJE_COLABORACION',
            modelo='MensajeServicio',
            objeto_id=mensaje_id_original,
            descripcion=f'Eliminó un mensaje del canal {canal} del servicio {servicio.id}.',
            request=request,
        )
        messages.success(request, "Mensaje eliminado del historial.")
    except PermissionDenied:
        raise
    except ValueError as exc:
        messages.error(request, str(exc))
    return redirect(_workspace_url(servicio.id, canal))


@login_required
@require_POST
@transaction.atomic
def limpiar_historial_canal(request, servicio_id):
    servicio = get_object_or_404(_servicio_queryset(), id=servicio_id)
    canal = request.POST.get("canal") or ""
    if canal not in dict(ConversacionServicio.CANALES):
        raise PermissionDenied("Canal inválido.")
    conversacion = get_object_or_404(
        ConversacionServicio,
        servicio_evento=servicio,
        canal=canal,
    )
    total = limpiar_historial_canal_workspace(conversacion, user=request.user)
    registrar_auditoria(
        usuario=request.user,
        empresa=servicio.evento.empresa,
        evento=servicio.evento,
        accion='LIMPIAR_HISTORIAL_COLABORACION',
        modelo='ConversacionServicio',
        objeto_id=conversacion.id,
        descripcion=f'Vació {total} mensaje(s) del canal {canal} del servicio {servicio.id}.',
        valores_anteriores={'total_mensajes': total, 'canal': canal},
        request=request,
    )
    messages.success(
        request,
        f"Historial limpiado: {total} mensaje(s) eliminados. "
        "Las decisiones, cotizaciones y aprobaciones estructuradas se conservaron.",
    )
    return redirect(_workspace_url(servicio.id, canal))


@login_required
@require_POST
@transaction.atomic
def eliminar_referencia(request, referencia_id):
    referencia = get_object_or_404(
        ReferenciaServicio.objects.select_related(
            "servicio_evento__evento",
            "servicio_evento__evento__empresa",
            "servicio_evento__proveedor",
            "mensaje_origen__conversacion",
        ),
        pk=referencia_id,
    )
    servicio = referencia.servicio_evento
    canal = (
        referencia.mensaje_origen.conversacion.canal
        if referencia.mensaje_origen_id
        else request.POST.get("canal")
    )
    referencia_id_original = referencia.id
    eliminar_referencia_workspace(referencia, user=request.user)
    registrar_auditoria(
        usuario=request.user,
        empresa=servicio.evento.empresa,
        evento=servicio.evento,
        accion='ELIMINAR_REFERENCIA_COLABORACION',
        modelo='ReferenciaServicio',
        objeto_id=referencia_id_original,
        descripcion=f'Eliminó una referencia del servicio {servicio.id}.',
        request=request,
    )
    messages.success(request, "Referencia eliminada.")
    return redirect(_workspace_url(servicio.id, canal))


@login_required
@require_POST
@transaction.atomic
def archivar_tema(request, tema_id):
    tema = get_object_or_404(
        TemaServicio.objects.select_related(
            "servicio_evento__evento",
            "servicio_evento__evento__empresa",
            "servicio_evento__proveedor",
        ),
        pk=tema_id,
    )
    servicio = tema.servicio_evento
    archivar_tema_workspace(tema, user=request.user)
    registrar_auditoria(
        usuario=request.user,
        empresa=servicio.evento.empresa,
        evento=servicio.evento,
        accion='ARCHIVAR_TEMA_COLABORACION',
        modelo='TemaServicio',
        objeto_id=tema.id,
        descripcion=f'Archivó el tema {tema.nombre} del servicio {servicio.id}.',
        request=request,
    )
    messages.success(request, "Tema archivado.")
    return redirect(_workspace_url(servicio.id, request.POST.get("canal")))

