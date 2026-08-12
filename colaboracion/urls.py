from django.urls import path

from . import views, workspace_views, k85_views, k86_views


urlpatterns = [
    path("servicios/<int:servicio_id>/workspace/operacion/tareas/crear/", k86_views.crear_tarea, name="colaboracion_k86_tarea_crear"),
    path("servicios/<int:servicio_id>/workspace/operacion/agenda/crear/", k86_views.crear_actividad, name="colaboracion_k86_actividad_crear"),
    path("servicios/<int:servicio_id>/workspace/operacion/agenda/participantes/<int:participante_id>/responder/", k86_views.responder_confirmacion_cita, name="colaboracion_k8712_cita_responder"),
    path("agenda/participantes/<int:participante_id>/responder/", k86_views.responder_confirmacion_cita_evento, name="colaboracion_k8712_cita_evento_responder"),
    path("servicios/<int:servicio_id>/workspace/operacion/documentos/crear/", k86_views.crear_documento, name="colaboracion_k86_documento_crear"),
    path("servicios/<int:servicio_id>/workspace/operacion/gastos/crear/", k86_views.crear_gasto, name="colaboracion_k86_gasto_crear"),
    path("servicios/<int:servicio_id>/workspace/operacion/pagos/crear/", k86_views.crear_pago, name="colaboracion_k86_pago_crear"),
    path("servicios/<int:servicio_id>/workspace/operacion/vincular/", k86_views.vincular_existente, name="colaboracion_k86_vincular"),
    path("servicios/<int:servicio_id>/workspace/operacion/desvincular/", k86_views.desvincular, name="colaboracion_k86_desvincular"),
    path("servicios/<int:servicio_id>/workspace/decisiones/crear/", k85_views.registrar_decision, name="colaboracion_k85_decision_crear"),
    path("servicios/<int:servicio_id>/workspace/cotizaciones/crear/", k85_views.crear_cotizacion, name="colaboracion_k85_cotizacion_crear"),
    path("workspace/cotizaciones/<int:cotizacion_id>/decidir/", k85_views.decidir_cotizacion, name="colaboracion_k85_cotizacion_decidir"),
    path("servicios/<int:servicio_id>/workspace/propuestas/crear/", k85_views.crear_propuesta, name="colaboracion_k85_propuesta_crear"),
    path("workspace/propuestas/<int:propuesta_id>/responder/", k85_views.responder_propuesta, name="colaboracion_k85_propuesta_responder"),
    path("servicios/<int:servicio_id>/workspace/aprobaciones/crear/", k85_views.solicitar_aprobacion, name="colaboracion_k85_aprobacion_crear"),
    path("workspace/aprobaciones/<int:aprobacion_id>/responder/", k85_views.responder_aprobacion, name="colaboracion_k85_aprobacion_responder"),

    path(
        "servicios/<int:servicio_id>/workspace/",
        workspace_views.servicio_workspace,
        name="colaboracion_workspace_servicio",
    ),
    path(
        "servicios/<int:servicio_id>/workspace/temas/crear/",
        workspace_views.crear_tema,
        name="colaboracion_workspace_crear_tema",
    ),
    path(
        "servicios/<int:servicio_id>/workspace/mensajes/enviar/",
        workspace_views.enviar_mensaje_workspace,
        name="colaboracion_workspace_enviar_mensaje",
    ),
    path(
        "workspace/adjuntos/<int:adjunto_id>/referencia/",
        workspace_views.guardar_referencia,
        name="colaboracion_workspace_guardar_referencia",
    ),
    path(
        "workspace/adjuntos/<int:adjunto_id>/eliminar/",
        workspace_views.eliminar_adjunto,
        name="colaboracion_workspace_eliminar_adjunto",
    ),
    path(
        "workspace/mensajes/<int:mensaje_id>/eliminar/",
        workspace_views.eliminar_mensaje,
        name="colaboracion_workspace_eliminar_mensaje",
    ),
    path(
        "servicios/<int:servicio_id>/workspace/historial/limpiar/",
        workspace_views.limpiar_historial_canal,
        name="colaboracion_workspace_limpiar_historial",
    ),
    path(
        "workspace/referencias/<int:referencia_id>/eliminar/",
        workspace_views.eliminar_referencia,
        name="colaboracion_workspace_eliminar_referencia",
    ),
    path(
        "workspace/temas/<int:tema_id>/archivar/",
        workspace_views.archivar_tema,
        name="colaboracion_workspace_archivar_tema",
    ),
]
