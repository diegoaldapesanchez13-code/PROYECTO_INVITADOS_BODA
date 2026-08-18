from django.urls import path

from . import views


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
]
