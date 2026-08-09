from django.urls import path
from . import views
from .builder import views as builder_views
from .builder import public_views as builder_public_views

urlpatterns = [
    path('', views.inicio, name='inicio'),
    path('dirtec/dashboard/', views.dashboard_dirtec, name='dirtec_dashboard'),
    path('empresa/<slug:empresa_slug>/dashboard/', views.dashboard_empresa_slug, name='empresa_dashboard'),
    path('empresa/<slug:empresa_slug>/wedding-planner/dashboard/', views.dashboard_planner_slug, name='planner_dashboard_empresa'),
    path('empresa/<slug:empresa_slug>/planner/dashboard/', views.dashboard_planner_slug, name='planner_dashboard_empresa_alias'),
    path('cliente/dashboard/', views.portal_cliente, name='cliente_dashboard'),
    path('proveedor/dashboard/', views.portal_proveedor, name='proveedor_dashboard'),
    path('portal/cliente/', views.portal_cliente, name='portal_cliente'),
    path('portal/cliente/aprobaciones/<int:aprobacion_id>/responder/', views.responder_aprobacion_cliente, name='responder_aprobacion_cliente'),
    path('portal/proveedor/', views.portal_proveedor, name='portal_proveedor'),
    path('portal/proveedor/servicios/<int:servicio_id>/actualizar/', views.actualizar_servicio_proveedor, name='actualizar_servicio_proveedor'),
    path('portal/proveedor/documentos/subir/', views.subir_documento_proveedor, name='subir_documento_proveedor'),
    path('dashboard/profesional/', views.dashboard_profesional, name='dashboard_profesional'),
    path('dashboard/dirtec/', views.dashboard_dirtec, name='dashboard_dirtec'),
    path('dashboard/empresa/', views.dashboard_empresa, name='dashboard_empresa'),
    path('dashboard/planner/', views.dashboard_planner, name='dashboard_planner'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('dashboard/calendario/', views.calendario_operativo, name='calendario_operativo'),
    path('dashboard/mesas/', views.mesas_visual, name='mesas_visual'),
    path('dashboard/mesas/guardar-posiciones/', views.guardar_posiciones_mesas, name='guardar_posiciones_mesas'),
    path('dashboard/editor-invitacion/<int:evento_id>/', builder_views.editor, name='editor_invitacion_visual'),
    path('dashboard/editor-invitacion/<int:evento_id>/api/document/', builder_views.document_api, name='builder_document_api'),
    path('dashboard/editor-invitacion/<int:evento_id>/api/publish/', builder_views.publish_api, name='builder_publish_api'),
    path(
        'dashboard/editor-invitacion/<int:evento_id>/api/assets/',
        builder_views.assets_api,
        name='builder_assets_api',
    ),
    path(
        'dashboard/editor-invitacion/<int:evento_id>/api/assets/<int:asset_id>/',
        builder_views.asset_detail_api,
        name='builder_asset_detail_api',
    ),
    path('api/dashboard/metricas/', views.dashboard_metricas_json, name='dashboard_metricas_json'),
    path('api/calendario/eventos/', views.calendario_eventos_json, name='calendario_eventos_json'),
    path('exportar-excel/', views.exportar_excel, name='exportar_excel'),
    path('exportar-resumen/', views.exportar_resumen_evento, name='exportar_resumen_evento'),
    path('dashboard/marcar-envio/<int:grupo_id>/', views.marcar_envio_invitacion, name='marcar_envio_invitacion'),
    path('dashboard/marcar-recordatorio/<int:grupo_id>/', views.marcar_recordatorio, name='marcar_recordatorio'),
    path('invitacion/<uuid:codigo>/', builder_public_views.public_invitation, name='ver_invitacion'),
    path('invitacion/<uuid:codigo>/rsvp/', builder_public_views.public_rsvp_api, name='builder_public_rsvp_api'),
]

# Rutas de la aplicación invitaciones:
# - inicio: página principal.
# - dashboard: panel de control.
# - exportar-excel: descarga de confirmaciones en Excel.
# - marcar-envio: actualiza el estado de invitación preparada.
# - marcar-recordatorio: actualiza el estado de recordatorio preparado.
# - invitacion/<uuid>: visualiza la invitación individual del grupo.
