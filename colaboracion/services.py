from decimal import Decimal

from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import Max, Sum

from core.services.authorization import (
    Actions,
    usuario_puede_evento,
    usuario_tiene_permiso,
)
from eventos.selectors import contrato_vigente
from notificaciones.models import Notificacion
from proveedores.models import Proveedor

from .models import (
    CotizacionProveedor,
    ExpedienteServicio,
    MensajeExpediente,
    PartidaPresupuestoCliente,
    PropuestaCliente,
)


def planner_puede_expediente(user, expediente):
    return usuario_puede_evento(
        user,
        expediente.evento,
        Actions.EVENT_OPERATIONS,
    )


def cliente_puede_evento(user, evento):
    """Client relationship used by both portal and collaboration writes.

    Keeping this check in one place prevents a POST endpoint from using a
    narrower/different event query than the screen that rendered the form.
    """
    return bool(
        getattr(user, "is_authenticated", False)
        and evento
        and usuario_puede_evento(
            user,
            evento,
            Actions.EVENT_VIEW,
        )
        and evento.clientes.filter(
            id=user.id
        ).exists()
    )


def cliente_puede_expediente(user, expediente):
    return cliente_puede_evento(
        user,
        expediente.evento,
    )


def proveedor_puede_expediente(user, expediente):
    return bool(
        getattr(user, "is_authenticated", False)
        and expediente.proveedor_id
        and expediente.proveedor
        and expediente.proveedor.usuario_id == user.id
        and expediente.proveedor.activo
        and usuario_tiene_permiso(
            user,
            Actions.PROVIDER_PORTAL,
            empresa=expediente.evento.empresa,
        )
    )


def crear_notificacion_colaboracion(
    usuario,
    expediente,
    titulo,
    mensaje,
    *,
    tipo="INFO",
    enlace=None,
):
    if not usuario or not usuario.pk:
        return None
    return Notificacion.objects.create(
        usuario=usuario,
        evento=expediente.evento,
        titulo=titulo[:140],
        mensaje=mensaje,
        tipo=tipo,
        enlace=enlace,
    )


def clientes_destino_expediente(expediente):
    if expediente.cliente_solicitante_id:
        return [expediente.cliente_solicitante]
    return list(
        expediente.evento.clientes.all()
    )


def notificar_planner(expediente, titulo, mensaje):
    return crear_notificacion_colaboracion(
        expediente.evento.wedding_planner,
        expediente,
        titulo,
        mensaje,
        enlace="/dashboard/planner/#colaboracion",
    )


def notificar_proveedor(expediente, titulo, mensaje):
    usuario = (
        expediente.proveedor.usuario
        if expediente.proveedor
        and expediente.proveedor.usuario_id
        else None
    )
    return crear_notificacion_colaboracion(
        usuario,
        expediente,
        titulo,
        mensaje,
        tipo="PROVEEDOR",
        enlace=(
            f"/proveedor/dashboard/?evento="
            f"{expediente.evento_id}#colaboracion"
        ),
    )


def notificar_clientes(expediente, titulo, mensaje):
    notificaciones = []
    for usuario in clientes_destino_expediente(
        expediente
    ):
        notificaciones.append(
            crear_notificacion_colaboracion(
                usuario,
                expediente,
                titulo,
                mensaje,
                tipo="APROBACION",
                enlace=(
                    f"/cliente/dashboard/?evento="
                    f"{expediente.evento_id}#colaboracion"
                ),
            )
        )
    return notificaciones


def registrar_mensaje_sistema(
    expediente,
    canal,
    mensaje,
    *,
    autor=None,
):
    return MensajeExpediente.objects.create(
        expediente=expediente,
        canal=canal,
        autor=autor,
        tipo="SISTEMA",
        mensaje=mensaje,
    )


def siguiente_version(model, expediente):
    actual = (
        model.objects
        .filter(expediente=expediente)
        .aggregate(max_version=Max("version"))
        .get("max_version")
        or 0
    )
    return actual + 1


def preparar_expedientes_cliente(evento, user):
    expedientes = list(
        ExpedienteServicio.objects
        .filter(evento=evento)
        .select_related("proveedor", "servicio_evento")
    )
    for expediente in expedientes:
        expediente.mensajes_cliente_ui = list(
            expediente.mensajes.filter(
                canal="CLIENTE_PLANNER"
            ).select_related("autor")
        )
        expediente.propuestas_cliente_ui = list(
            expediente.propuestas_cliente
            .exclude(estado="BORRADOR")
            .order_by("-version")
        )
        expediente.propuesta_actual_ui = (
            expediente.propuestas_cliente_ui[0]
            if expediente.propuestas_cliente_ui
            else None
        )
    return expedientes


def preparar_expedientes_planner(eventos):
    expedientes = list(
        ExpedienteServicio.objects
        .filter(evento__in=eventos)
        .select_related(
            "evento",
            "proveedor",
            "servicio_evento",
            "cliente_solicitante",
        )
    )
    for expediente in expedientes:
        expediente.mensajes_cliente_ui = list(
            expediente.mensajes.filter(
                canal="CLIENTE_PLANNER"
            ).select_related("autor")
        )
        expediente.mensajes_proveedor_ui = list(
            expediente.mensajes.filter(
                canal="PLANNER_PROVEEDOR"
            ).select_related("autor")
        )
        expediente.cotizaciones_ui = list(
            expediente.cotizaciones_proveedor
            .select_related("proveedor")
            .order_by("-version")
        )
        expediente.propuestas_ui = list(
            expediente.propuestas_cliente
            .select_related("cotizacion")
            .order_by("-version")
        )
        expediente.cotizacion_aceptada_ui = next(
            (
                item
                for item in expediente.cotizaciones_ui
                if item.estado == "ACEPTADA"
            ),
            None,
        )
        expediente.propuesta_aprobada_ui = next(
            (
                item
                for item in expediente.propuestas_ui
                if item.estado == "APROBADA"
            ),
            None,
        )
    return expedientes


def preparar_expedientes_proveedor(evento, proveedor):
    expedientes = list(
        ExpedienteServicio.objects
        .filter(
            evento=evento,
            proveedor=proveedor,
        )
        .select_related(
            "evento",
            "servicio_evento",
        )
    )
    for expediente in expedientes:
        expediente.mensajes_proveedor_ui = list(
            expediente.mensajes.filter(
                canal="PLANNER_PROVEEDOR"
            ).select_related("autor")
        )
        expediente.cotizaciones_ui = list(
            expediente.cotizaciones_proveedor
            .filter(proveedor=proveedor)
            .order_by("-version")
        )
    return expedientes


def presupuesto_cliente(evento):
    qs = PartidaPresupuestoCliente.objects.filter(
        evento=evento,
        estado="ACTIVA",
    )
    return {
        "partidas": qs,
        "total_adicionales": (
            qs.filter(
                incluido_en_paquete=False
            ).aggregate(total=Sum("monto_cliente"))["total"]
            or Decimal("0")
        ),
        "incluidos": qs.filter(
            incluido_en_paquete=True
        ).count(),
    }


def proveedores_para_expediente(expediente):
    return Proveedor.objects.filter(
        empresa=expediente.evento.empresa,
        activo=True,
        visible_para_wedding_planners=True,
    ).order_by("nombre_comercial")


# K.8.4 ---------------------------------------------------------------------
from eventos.models import ParticipanteEvento
from .models import (
    ConversacionServicio,
    TemaServicio,
    MensajeServicio,
    AdjuntoMensajeServicio,
    ReferenciaServicio,
)


def es_cliente_servicio_workspace(user, servicio):
    if not getattr(user, "is_authenticated", False):
        return False
    return ParticipanteEvento.objects.filter(
        evento=servicio.evento,
        usuario=user,
        rol="CLIENTE",
        activo=True,
    ).exists() or servicio.evento.clientes.filter(id=user.id).exists()


def es_proveedor_servicio_workspace(user, servicio):
    return bool(
        getattr(user, "is_authenticated", False)
        and servicio.proveedor_id
        and servicio.proveedor
        and servicio.proveedor.activo
        and servicio.proveedor.usuario_id == user.id
        and usuario_tiene_permiso(
            user,
            Actions.PROVIDER_PORTAL,
            empresa=servicio.evento.empresa,
        )
    )


def es_operador_servicio_workspace(user, servicio):
    return usuario_puede_evento(user, servicio.evento, Actions.EVENT_OPERATIONS)


def canales_visibles_workspace(user, servicio):
    if es_operador_servicio_workspace(user, servicio):
        return {"CLIENTE_PLANNER", "PLANNER_PROVEEDOR", "INTERNO"}
    if es_cliente_servicio_workspace(user, servicio):
        return {"CLIENTE_PLANNER"}
    if es_proveedor_servicio_workspace(user, servicio):
        return {"PLANNER_PROVEEDOR"}
    return set()


def puede_ver_workspace(user, servicio):
    return bool(canales_visibles_workspace(user, servicio))


def puede_escribir_canal_workspace(user, servicio, canal):
    return canal in canales_visibles_workspace(user, servicio)


def obtener_o_crear_conversacion(servicio, canal, *, user=None):
    if canal not in dict(ConversacionServicio.CANALES):
        raise ValueError("Canal de conversacion no valido.")
    conversacion, _ = ConversacionServicio.objects.get_or_create(
        servicio_evento=servicio,
        canal=canal,
        defaults={"creada_por": user},
    )
    return conversacion


def crear_tema_workspace(servicio, nombre, *, descripcion="", user=None):
    nombre = (nombre or "").strip()
    if not nombre:
        raise ValueError("El nombre del tema es obligatorio.")
    return TemaServicio.objects.create(
        servicio_evento=servicio,
        nombre=nombre[:120],
        descripcion=(descripcion or "").strip() or None,
        creado_por=user,
    )


def registrar_mensaje_workspace(
    servicio,
    canal,
    *,
    user,
    texto="",
    tema=None,
    archivos=None,
):
    texto = (texto or "").strip()
    archivos = list(archivos or [])
    if not texto and not archivos:
        raise ValueError("El mensaje necesita texto o al menos un archivo.")
    if tema and tema.servicio_evento_id != servicio.id:
        raise ValueError("El tema no pertenece al servicio.")

    conversacion = obtener_o_crear_conversacion(servicio, canal, user=user)
    mensaje = MensajeServicio.objects.create(
        conversacion=conversacion,
        tema=tema,
        autor=user,
        texto=texto,
    )
    for archivo in archivos:
        AdjuntoMensajeServicio.objects.create(
            mensaje=mensaje,
            archivo=archivo,
            nombre_original=getattr(archivo, "name", "")[:255],
            tipo_mime=getattr(archivo, "content_type", "")[:120],
            tamano_bytes=getattr(archivo, "size", 0) or 0,
        )
    return mensaje


def promover_adjunto_a_referencia(adjunto, *, user, titulo=None, tipo="REFERENCIA"):
    mensaje = adjunto.mensaje
    servicio = mensaje.conversacion.servicio_evento
    if tipo not in dict(ReferenciaServicio.TIPOS):
        raise ValueError("Tipo de referencia no valido.")
    return ReferenciaServicio.objects.create(
        servicio_evento=servicio,
        tema=mensaje.tema,
        mensaje_origen=mensaje,
        adjunto_origen=adjunto,
        tipo=tipo,
        titulo=(titulo or adjunto.nombre_original or "Referencia")[:180],
        creado_por=user,
    )


def eliminar_adjunto_workspace(adjunto, *, user):
    """Elimina un adjunto del workspace sin permitir borrados cruzados.

    El autor puede corregir su propio envio y el equipo operativo puede retirar
    adjuntos del servicio. Un archivo promovido a referencia se protege para no
    destruir silenciosamente evidencia ya clasificada.
    """
    mensaje = adjunto.mensaje
    servicio = mensaje.conversacion.servicio_evento

    es_operador = es_operador_servicio_workspace(user, servicio)
    es_autor = bool(mensaje.autor_id and mensaje.autor_id == getattr(user, "id", None))
    canal_visible = mensaje.conversacion.canal in canales_visibles_workspace(user, servicio)
    if not es_operador and not (es_autor and canal_visible):
        raise PermissionDenied("No puedes eliminar este archivo.")

    if adjunto.referencias_generadas.exists():
        raise ValueError(
            "Este archivo ya fue guardado como referencia. Retira primero la referencia antes de eliminarlo."
        )

    archivo = adjunto.archivo
    adjunto.delete()
    if archivo:
        transaction.on_commit(lambda archivo=archivo: archivo.delete(save=False))

    if not mensaje.texto.strip() and not mensaje.adjuntos.exists():
        mensaje.delete()
    return True


def _eliminar_archivos_adjuntos(adjuntos):
    """Programa el borrado físico solo después de confirmar la transacción."""
    archivos = [adjunto.archivo for adjunto in adjuntos if adjunto.archivo]

    def borrar():
        for archivo in archivos:
            try:
                archivo.delete(save=False)
            except Exception:
                # El storage puede haber perdido el blob previamente; la BD ya quedó coherente.
                pass

    transaction.on_commit(borrar)


def eliminar_referencia_workspace(referencia, *, user):
    servicio = referencia.servicio_evento
    if not es_operador_servicio_workspace(user, servicio):
        raise PermissionDenied("Solo el equipo operativo puede eliminar referencias.")
    referencia.delete()
    return True


def eliminar_mensaje_workspace(mensaje, *, user):
    """Elimina un mensaje individual únicamente desde el equipo operativo.

    Si un adjunto está promovido a referencia se exige retirar primero la
    referencia para evitar destruir un archivo que sigue clasificado.
    """
    servicio = mensaje.conversacion.servicio_evento
    if not es_operador_servicio_workspace(user, servicio):
        raise PermissionDenied("Solo el equipo operativo puede eliminar mensajes.")

    adjuntos = list(mensaje.adjuntos.all())
    if (
        mensaje.referencias_generadas.exists()
        or ReferenciaServicio.objects.filter(adjunto_origen__in=adjuntos).exists()
    ):
        raise ValueError(
            "Este mensaje contiene archivos guardados como referencia. "
            "Elimina primero esas referencias."
        )

    mensaje.delete()
    _eliminar_archivos_adjuntos(adjuntos)
    return True


def limpiar_historial_canal_workspace(conversacion, *, user):
    """Vacía mensajes y referencias originadas en el canal actual.

    No elimina decisiones, cotizaciones, propuestas ni aprobaciones; sus
    referencias al mensaje usan SET_NULL y por tanto sobreviven como registros
    estructurados.
    """
    servicio = conversacion.servicio_evento
    if not es_operador_servicio_workspace(user, servicio):
        raise PermissionDenied("Solo el equipo operativo puede limpiar el historial.")

    mensajes = list(
        conversacion.mensajes.prefetch_related("adjuntos", "referencias_generadas").all()
    )
    mensaje_ids = [mensaje.id for mensaje in mensajes]
    adjuntos = [
        adjunto
        for mensaje in mensajes
        for adjunto in mensaje.adjuntos.all()
    ]

    # Las referencias promovidas desde este canal forman parte de la limpieza
    # explícita del historial del canal.
    ReferenciaServicio.objects.filter(
        servicio_evento=servicio,
        mensaje_origen_id__in=mensaje_ids,
    ).delete()

    total = len(mensajes)
    conversacion.mensajes.all().delete()
    _eliminar_archivos_adjuntos(adjuntos)
    return total


def archivar_tema_workspace(tema, *, user):
    servicio = tema.servicio_evento
    if not es_operador_servicio_workspace(user, servicio):
        raise PermissionDenied("Solo el equipo operativo puede archivar temas.")
    tema.activo = False
    tema.save(update_fields=["activo", "fecha_actualizacion"])
    return True

# K.8.5 ---------------------------------------------------------------------
from django.utils import timezone
from .models import AjusteContractualServicio, DecisionServicio, CotizacionServicio, PropuestaServicioCliente, AprobacionServicio


def _siguiente_version_servicio(model, servicio):
    actual = model.objects.filter(servicio_evento=servicio).aggregate(max_version=Max("version")).get("max_version") or 0
    return actual + 1


def registrar_decision_servicio(servicio, *, user, titulo, descripcion="", tema=None, mensaje_origen=None):
    if not es_operador_servicio_workspace(user, servicio):
        raise PermissionDenied("Solo el equipo operativo puede registrar decisiones.")
    titulo = (titulo or "").strip()
    if not titulo:
        raise ValueError("El titulo de la decision es obligatorio.")
    if tema and tema.servicio_evento_id != servicio.id:
        raise ValueError("El tema no pertenece al servicio.")
    if mensaje_origen and mensaje_origen.conversacion.servicio_evento_id != servicio.id:
        raise ValueError("El mensaje no pertenece al servicio.")
    return DecisionServicio.objects.create(
        servicio_evento=servicio, tema=tema, mensaje_origen=mensaje_origen,
        titulo=titulo[:180], descripcion=(descripcion or "").strip() or None,
        registrado_por=user,
    )


def crear_cotizacion_servicio(servicio, *, user, costo_proveedor, descripcion="", vigencia=None, archivo=None):
    if not (es_operador_servicio_workspace(user, servicio) or es_proveedor_servicio_workspace(user, servicio)):
        raise PermissionDenied("No puedes registrar cotizaciones para este servicio.")
    costo = Decimal(str(costo_proveedor or "0"))
    if costo < 0:
        raise ValueError("El costo no puede ser negativo.")
    CotizacionServicio.objects.filter(servicio_evento=servicio, estado="ENVIADA").update(estado="REEMPLAZADA")
    return CotizacionServicio.objects.create(
        servicio_evento=servicio,
        version=_siguiente_version_servicio(CotizacionServicio, servicio),
        costo_proveedor=costo,
        descripcion=(descripcion or "").strip() or None,
        vigencia=vigencia or None,
        archivo=archivo,
        creado_por=user,
    )


def decidir_cotizacion_servicio(cotizacion, *, user, estado, comentario=""):
    servicio = cotizacion.servicio_evento
    if not es_operador_servicio_workspace(user, servicio):
        raise PermissionDenied("Solo el equipo operativo puede decidir una cotizacion.")
    if estado not in {"ACEPTADA", "CAMBIOS_SOLICITADOS", "RECHAZADA"}:
        raise ValueError("Decision de cotizacion no valida.")
    cotizacion.estado = estado
    cotizacion.respuesta_planner = (comentario or "").strip() or None
    cotizacion.save(update_fields=["estado", "respuesta_planner", "fecha_actualizacion"])
    if estado == "ACEPTADA":
        servicio.costo_proveedor = cotizacion.costo_proveedor
        servicio.save(update_fields=["costo_proveedor"])
    return cotizacion


def crear_propuesta_servicio(servicio, *, user, descripcion="", modalidad=None, cargo_adicional_cliente=None, cotizacion=None, enviar=True):
    if not es_operador_servicio_workspace(user, servicio):
        raise PermissionDenied("Solo el equipo operativo puede crear propuestas.")
    modalidad = modalidad or servicio.modalidad or "ADICIONAL"
    if modalidad not in dict(PropuestaServicioCliente.MODALIDADES):
        raise ValueError("Modalidad de propuesta no valida.")
    cargo = Decimal(str(cargo_adicional_cliente if cargo_adicional_cliente not in (None, "") else servicio.cargo_adicional_cliente or 0))
    if cargo < 0:
        raise ValueError("El cargo adicional no puede ser negativo.")
    if modalidad in {"INCLUIDO", "CORTESIA"} and cargo != 0:
        raise ValueError("Un servicio incluido o una cortesia no puede generar cargo adicional al cliente.")
    PropuestaServicioCliente.objects.filter(servicio_evento=servicio, estado__in=["BORRADOR", "ENVIADA", "CAMBIOS_SOLICITADOS"]).update(estado="REEMPLAZADA")
    propuesta = PropuestaServicioCliente.objects.create(
        servicio_evento=servicio,
        cotizacion=cotizacion,
        version=_siguiente_version_servicio(PropuestaServicioCliente, servicio),
        modalidad=modalidad,
        descripcion=(descripcion or "").strip() or None,
        costo_proveedor_snapshot=servicio.costo_proveedor or 0,
        valor_contratado_snapshot=servicio.valor_contratado or 0,
        cargo_adicional_cliente=cargo,
        estado="ENVIADA" if enviar else "BORRADOR",
        enviado_por=user,
        fecha_envio=timezone.now() if enviar else None,
    )
    return propuesta


@transaction.atomic
def responder_propuesta_servicio(propuesta, *, user, estado, comentario=""):
    propuesta = (
        PropuestaServicioCliente.objects.select_for_update()
        .select_related("servicio_evento", "servicio_evento__evento")
        .get(pk=propuesta.pk)
    )
    servicio = propuesta.servicio_evento
    if not es_cliente_servicio_workspace(user, servicio):
        raise PermissionDenied("Solo un cliente del evento puede responder esta propuesta.")
    if propuesta.estado != "ENVIADA":
        raise ValueError("Esta propuesta ya no esta pendiente de respuesta.")
    if estado not in {"APROBADA", "CAMBIOS_SOLICITADOS", "RECHAZADA"}:
        raise ValueError("Respuesta de propuesta no valida.")

    if estado == "APROBADA":
        cargo = Decimal(str(propuesta.cargo_adicional_cliente or 0))
        if propuesta.modalidad in {"INCLUIDO", "CORTESIA"} and cargo != 0:
            raise ValueError("Un servicio incluido o una cortesia debe aprobarse con cargo cero.")

        contrato = contrato_vigente(servicio.evento)
        requiere_ajuste = propuesta.modalidad in {"UPGRADE", "ADICIONAL", "CORTESIA"}
        if requiere_ajuste and contrato is None:
            raise ValueError(
                "No existe un contrato vigente. Los cambios post-contrato deben aprobarse contra un contrato base."
            )
        if requiere_ajuste:
            AjusteContractualServicio.objects.create(
                evento=servicio.evento,
                contrato_base=contrato,
                servicio_evento=servicio,
                propuesta_origen=propuesta,
                tipo=propuesta.modalidad,
                descripcion_snapshot=(propuesta.descripcion or "").strip() or None,
                monto_cliente=cargo,
                valor_informativo=propuesta.valor_contratado_snapshot or 0,
                moneda=contrato.moneda or "MXN",
                aprobado_por=user,
                aprobado_en=timezone.now(),
            )

    propuesta.estado = estado
    propuesta.respondido_por = user
    propuesta.comentario_cliente = (comentario or "").strip() or None
    propuesta.fecha_respuesta = timezone.now()
    propuesta.save(update_fields=[
        "estado", "respondido_por", "comentario_cliente",
        "fecha_respuesta", "fecha_actualizacion",
    ])

    if estado == "APROBADA":
        servicio.modalidad = propuesta.modalidad
        total_ajustes = (
            AjusteContractualServicio.objects.filter(
                servicio_evento=servicio, estado="VIGENTE"
            ).aggregate(total=Sum("monto_cliente"))["total"] or Decimal("0")
        )
        servicio.cargo_adicional_cliente = total_ajustes
        servicio.save(update_fields=["modalidad", "cargo_adicional_cliente"])

    return propuesta


def solicitar_aprobacion_servicio(servicio, *, user, titulo, descripcion="", tema=None, decision=None, propuesta=None):
    if not es_operador_servicio_workspace(user, servicio):
        raise PermissionDenied("Solo el equipo operativo puede solicitar aprobaciones.")
    titulo = (titulo or "").strip()
    if not titulo:
        raise ValueError("El titulo de la aprobacion es obligatorio.")
    for objeto in (tema, decision, propuesta):
        if objeto is not None and getattr(objeto, "servicio_evento_id", servicio.id) != servicio.id:
            raise ValueError("El elemento relacionado no pertenece al servicio.")
    return AprobacionServicio.objects.create(
        servicio_evento=servicio, tema=tema, decision=decision, propuesta=propuesta,
        titulo=titulo[:180], descripcion=(descripcion or "").strip() or None,
        solicitado_por=user,
    )


def responder_aprobacion_servicio(aprobacion, *, user, estado, comentario=""):
    servicio = aprobacion.servicio_evento
    if not es_cliente_servicio_workspace(user, servicio):
        raise PermissionDenied("Solo un cliente del evento puede responder esta aprobacion.")
    if aprobacion.estado != "PENDIENTE":
        raise ValueError("Esta aprobacion ya fue respondida.")
    if estado not in {"APROBADA", "CAMBIOS", "RECHAZADA"}:
        raise ValueError("Respuesta de aprobacion no valida.")
    aprobacion.estado = estado
    aprobacion.respondido_por = user
    aprobacion.comentario_respuesta = (comentario or "").strip() or None
    aprobacion.fecha_respuesta = timezone.now()
    aprobacion.save(update_fields=["estado", "respondido_por", "comentario_respuesta", "fecha_respuesta"])
    return aprobacion
