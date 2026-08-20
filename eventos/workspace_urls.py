from django.urls import path

from . import workspace_views, workspace_commercial_views, workspace_services_views, workspace_tasks_views, workspace_agenda_views, workspace_guests_views


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
    path("<int:evento_id>/configuracion/", workspace_views.evento_configuracion, name="k9_evento_configuracion"),
    path("<int:evento_id>/finalizar/", workspace_views.evento_finalizar, name="k9_evento_finalizar"),
    path("<int:evento_id>/cancelar/", workspace_views.evento_cancelar, name="k9_evento_cancelar"),
    path("<int:evento_id>/archivar/", workspace_views.evento_archivar, name="k9_evento_archivar"),
    path("<int:evento_id>/restaurar/", workspace_views.evento_restaurar, name="k9_evento_restaurar"),
    path("<int:evento_id>/eliminar-error/", workspace_views.evento_eliminar_error, name="k9_evento_eliminar_error"),
    path("<int:evento_id>/purgar/", workspace_views.evento_purgar, name="k9_evento_purgar"),
]

