from django.urls import path

from . import workspace_views, workspace_commercial_views, workspace_services_views, workspace_tasks_views, workspace_agenda_views, workspace_guests_views, workspace_guests_io_views, workspace_documents_views, workspace_finance_views


urlpatterns = [
    path("", workspace_views.evento_list, name="k9_evento_list"),
    path("nuevo/", workspace_views.evento_create, name="k9_evento_create"),
    path("<int:evento_id>/", workspace_views.evento_resumen, name="k9_evento_resumen"),
    path("<int:evento_id>/datos/", workspace_views.evento_datos, name="k9_evento_datos"),
    path("<int:evento_id>/comercial/", workspace_commercial_views.evento_comercial, name="k9_evento_comercial"),
    path("<int:evento_id>/servicios/", workspace_services_views.evento_servicios, name="k9_evento_servicios"),
    path("<int:evento_id>/tareas/", workspace_tasks_views.evento_tareas, name="k9_evento_tareas"),
    path("<int:evento_id>/agenda/", workspace_agenda_views.evento_agenda, name="k9_evento_agenda"),
    path("<int:evento_id>/invitados/", workspace_guests_views.evento_invitados, name="k9_evento_invitados"),
    path("<int:evento_id>/invitados/plantilla.xlsx", workspace_guests_io_views.invitados_plantilla, name="k9_evento_invitados_plantilla"),
    path("<int:evento_id>/invitados/exportar.xlsx", workspace_guests_io_views.invitados_exportar, name="k9_evento_invitados_exportar"),
    path("<int:evento_id>/invitados/importar/", workspace_guests_io_views.invitados_importar, name="k9_evento_invitados_importar"),
    path("<int:evento_id>/documentos/", workspace_documents_views.evento_documentos, name="k9_evento_documentos"),
    path("<int:evento_id>/documentos/<int:documento_id>/archivar/", workspace_documents_views.documento_archivar, name="k9_documento_archivar"),
    path("<int:evento_id>/documentos/<int:documento_id>/restaurar/", workspace_documents_views.documento_restaurar, name="k9_documento_restaurar"),
    path("<int:evento_id>/documentos/<int:documento_id>/reemplazar/", workspace_documents_views.documento_reemplazar, name="k9_documento_reemplazar"),
    path("<int:evento_id>/documentos/<int:documento_id>/eliminar/", workspace_documents_views.documento_eliminar, name="k9_documento_eliminar"),
    path("<int:evento_id>/finanzas/", workspace_finance_views.evento_finanzas, name="k9_evento_finanzas"),
    path("<int:evento_id>/finanzas/gastos/crear/", workspace_finance_views.gasto_crear, name="k9_finanzas_gasto_crear"),
    path("<int:evento_id>/finanzas/gastos/<int:gasto_id>/editar/", workspace_finance_views.gasto_editar, name="k9_finanzas_gasto_editar"),
    path("<int:evento_id>/finanzas/gastos/<int:gasto_id>/pagar/", workspace_finance_views.pago_registrar, name="k9_finanzas_pago_registrar"),
    path("<int:evento_id>/finanzas/pagos/<int:pago_id>/anular/", workspace_finance_views.pago_anular, name="k9_finanzas_pago_anular"),
    path("<int:evento_id>/finanzas/gastos/<int:gasto_id>/cancelar/", workspace_finance_views.gasto_cancelar, name="k9_finanzas_gasto_cancelar"),
    path("<int:evento_id>/finanzas/gastos/<int:gasto_id>/archivar/", workspace_finance_views.gasto_archivar, name="k9_finanzas_gasto_archivar"),
    path("<int:evento_id>/finanzas/gastos/<int:gasto_id>/restaurar/", workspace_finance_views.gasto_restaurar, name="k9_finanzas_gasto_restaurar"),
    path("<int:evento_id>/finanzas/pagos-cliente/<int:pago_id>/revisar/", workspace_finance_views.pago_cliente_revisar, name="k9_finanzas_pago_cliente_revisar"),
    path("<int:evento_id>/configuracion/", workspace_views.evento_configuracion, name="k9_evento_configuracion"),
    path("<int:evento_id>/finalizar/", workspace_views.evento_finalizar, name="k9_evento_finalizar"),
    path("<int:evento_id>/cancelar/", workspace_views.evento_cancelar, name="k9_evento_cancelar"),
    path("<int:evento_id>/archivar/", workspace_views.evento_archivar, name="k9_evento_archivar"),
    path("<int:evento_id>/restaurar/", workspace_views.evento_restaurar, name="k9_evento_restaurar"),
    path("<int:evento_id>/eliminar-error/", workspace_views.evento_eliminar_error, name="k9_evento_eliminar_error"),
    path("<int:evento_id>/purgar/", workspace_views.evento_purgar, name="k9_evento_purgar"),
]

