from django.urls import path

from . import operational_lifecycle_views, views


urlpatterns = [
    path(
        '<slug:empresa_slug>/propuestas/<int:propuesta_id>/contrato/generar/',
        views.contrato_generar_desde_propuesta,
        name='eventos_contrato_generar',
    ),
    path(
        '<slug:empresa_slug>/contratos/<int:contrato_id>/',
        views.contrato_detail,
        name='eventos_contrato_detail',
    ),
    path(
        '<slug:empresa_slug>/contratos/<int:contrato_id>/materializar/',
        views.contrato_materializar_servicios,
        name='eventos_contrato_materializar',
    ),

    # K9.8B — acciones de ciclo de vida operativo. Todas son POST, tenant-aware
    # y conservan historial; no exponen hard-delete.
    path('<slug:empresa_slug>/operacion/servicios/<int:servicio_id>/cancelar/', operational_lifecycle_views.servicio_cancelar, name='eventos_servicio_cancelar'),
    path('<slug:empresa_slug>/operacion/servicios/<int:servicio_id>/archivar/', operational_lifecycle_views.servicio_archivar, name='eventos_servicio_archivar'),
    path('<slug:empresa_slug>/operacion/servicios/<int:servicio_id>/desarchivar/', operational_lifecycle_views.servicio_desarchivar, name='eventos_servicio_desarchivar'),
    path('<slug:empresa_slug>/operacion/tareas/<int:tarea_id>/cancelar/', operational_lifecycle_views.tarea_cancelar, name='eventos_tarea_cancelar'),
    path('<slug:empresa_slug>/operacion/tareas/<int:tarea_id>/archivar/', operational_lifecycle_views.tarea_archivar, name='eventos_tarea_archivar'),
    path('<slug:empresa_slug>/operacion/tareas/<int:tarea_id>/desarchivar/', operational_lifecycle_views.tarea_desarchivar, name='eventos_tarea_desarchivar'),
    path('<slug:empresa_slug>/operacion/actividades/<int:actividad_id>/cancelar/', operational_lifecycle_views.actividad_cancelar, name='eventos_actividad_cancelar'),
    path('<slug:empresa_slug>/operacion/actividades/<int:actividad_id>/archivar/', operational_lifecycle_views.actividad_archivar, name='eventos_actividad_archivar'),
    path('<slug:empresa_slug>/operacion/actividades/<int:actividad_id>/desarchivar/', operational_lifecycle_views.actividad_desarchivar, name='eventos_actividad_desarchivar'),
    path('<slug:empresa_slug>/operacion/documentos/<int:documento_id>/archivar/', operational_lifecycle_views.documento_archivar, name='eventos_documento_archivar'),
    path('<slug:empresa_slug>/operacion/documentos/<int:documento_id>/desarchivar/', operational_lifecycle_views.documento_desarchivar, name='eventos_documento_desarchivar'),
    path('<slug:empresa_slug>/operacion/gastos/<int:gasto_id>/cancelar/', operational_lifecycle_views.gasto_cancelar, name='eventos_gasto_cancelar'),
    path('<slug:empresa_slug>/operacion/gastos/<int:gasto_id>/archivar/', operational_lifecycle_views.gasto_archivar, name='eventos_gasto_archivar'),
    path('<slug:empresa_slug>/operacion/gastos/<int:gasto_id>/desarchivar/', operational_lifecycle_views.gasto_desarchivar, name='eventos_gasto_desarchivar'),
    path('<slug:empresa_slug>/operacion/pagos/<int:pago_id>/anular/', operational_lifecycle_views.pago_anular, name='eventos_pago_anular'),
]
