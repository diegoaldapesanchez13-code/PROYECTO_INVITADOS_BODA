from django.urls import path

from . import workspace_views


urlpatterns = [
    path("", workspace_views.evento_list, name="k9_evento_list"),
    path("nuevo/", workspace_views.evento_create, name="k9_evento_create"),
    path("<int:evento_id>/", workspace_views.evento_resumen, name="k9_evento_resumen"),
    path("<int:evento_id>/datos/", workspace_views.evento_datos, name="k9_evento_datos"),
]
