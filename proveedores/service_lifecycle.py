from django.core.exceptions import ValidationError


# D4 canonical service lifecycle.
#
# Canonical sources:
# - estado_comercial: commercial truth
# - estado_operativo: operational truth
# - estado_proveedor: external/provider signal
# - estado: legacy compatibility mirror only

OPERATIVE_TRANSITIONS = {
    "PENDIENTE": {"PENDIENTE", "EN_DEFINICION", "PROGRAMADO", "CANCELADO"},
    "EN_DEFINICION": {"EN_DEFINICION", "PENDIENTE", "PROGRAMADO", "INCIDENCIA", "CANCELADO"},
    "PROGRAMADO": {"PROGRAMADO", "EN_DEFINICION", "LISTO", "INCIDENCIA", "CANCELADO"},
    "LISTO": {"LISTO", "PROGRAMADO", "EN_EJECUCION", "INCIDENCIA", "CANCELADO"},
    "EN_EJECUCION": {"EN_EJECUCION", "COMPLETADO", "INCIDENCIA", "CANCELADO"},
    "INCIDENCIA": {
        "INCIDENCIA",
        "EN_DEFINICION",
        "PROGRAMADO",
        "LISTO",
        "EN_EJECUCION",
        "CANCELADO",
    },
    "COMPLETADO": {"COMPLETADO"},
    "CANCELADO": {"CANCELADO"},
}

LEGACY_FINANCIAL_MARKERS = {"ANTICIPO_PAGADO", "LIQUIDADO"}


def legacy_estado_canonico(servicio):
    """Derive legacy state without making it a fourth source of truth."""
    if servicio.estado_comercial == "CANCELADO" or servicio.estado_operativo == "CANCELADO":
        return "CANCELADO"
    if servicio.estado_operativo == "COMPLETADO":
        return "SERVICIO_COMPLETADO"
    mapping = {
        "CONTRATADO": "CONTRATADO",
        "APROBADO": "APROBADO",
        "PROPUESTO": "PENDIENTE_APROBACION",
        "COTIZANDO": "COTIZADO",
        "BORRADOR": "SOLICITADO",
    }
    return mapping.get(servicio.estado_comercial, "SOLICITADO")


def sincronizar_estado_legacy(servicio):
    """
    Keep historical finance-only legacy markers until a terminal lifecycle
    transition has to win. New K9 code must never use them as lifecycle truth.
    """
    derived = legacy_estado_canonico(servicio)
    if (
        servicio.estado in LEGACY_FINANCIAL_MARKERS
        and derived not in {"CANCELADO", "SERVICIO_COMPLETADO"}
    ):
        return servicio.estado
    servicio.estado = derived
    return derived


def validar_transicion_operativa(actual, nuevo):
    allowed = OPERATIVE_TRANSITIONS.get(actual)
    if allowed is None:
        raise ValidationError(f"Estado operativo actual no reconocido: {actual}.")
    if nuevo not in allowed:
        raise ValidationError(
            f"Transicion operativa no permitida: {actual} -> {nuevo}."
        )
    return nuevo


def aplicar_estado_operativo(servicio, nuevo):
    actual = servicio.estado_operativo or "PENDIENTE"
    validar_transicion_operativa(actual, nuevo)
    servicio.estado_operativo = nuevo
    if nuevo == "CANCELADO":
        servicio.estado_comercial = "CANCELADO"
    sincronizar_estado_legacy(servicio)
    return servicio


def aplicar_estado_comercial(servicio, nuevo):
    choices = {value for value, _label in servicio.ESTADOS_COMERCIALES}
    if nuevo not in choices:
        raise ValidationError(f"Estado comercial no reconocido: {nuevo}.")
    if servicio.estado_comercial == "CANCELADO" and nuevo != "CANCELADO":
        raise ValidationError("Un servicio comercialmente cancelado no se reactiva directamente.")
    servicio.estado_comercial = nuevo
    if nuevo == "CANCELADO":
        servicio.estado_operativo = "CANCELADO"
    sincronizar_estado_legacy(servicio)
    return servicio


def aplicar_estado_proveedor(servicio, nuevo, *, comentario=None, responded_at=None):
    choices = {value for value, _label in servicio.ESTADOS_PROVEEDOR}
    if nuevo not in choices:
        raise ValidationError(f"Estado de proveedor no reconocido: {nuevo}.")
    servicio.estado_proveedor = nuevo
    if comentario is not None:
        servicio.comentario_proveedor = comentario
    if responded_at is not None:
        servicio.fecha_respuesta_proveedor = responded_at
    # Provider signal intentionally does NOT mutate operational/commercial truth.
    return servicio


def servicio_cerrado(servicio):
    return servicio.estado_operativo in {"COMPLETADO", "CANCELADO"}


def servicio_consistente(servicio):
    """Focused invariant checker used by D4 tests/domain services."""
    errors = []
    if servicio.estado_operativo == "CANCELADO" and servicio.estado_comercial != "CANCELADO":
        errors.append("Un servicio operativamente cancelado debe estar comercialmente cancelado.")
    if servicio.estado_comercial == "CANCELADO" and servicio.estado_operativo != "CANCELADO":
        errors.append("Un servicio comercialmente cancelado debe estar operativamente cancelado.")
    if errors:
        raise ValidationError(errors)
    return True
