from django.urls import path

from . import views


urlpatterns = [
    path('<slug:empresa_slug>/paquetes/', views.paquete_list, name='paquetes_paquete_list'),
    path('<slug:empresa_slug>/paquetes/nuevo/', views.paquete_create, name='paquetes_paquete_create'),
    path('<slug:empresa_slug>/paquetes/<int:paquete_id>/', views.paquete_detail, name='paquetes_paquete_detail'),
    path('<slug:empresa_slug>/paquetes/<int:paquete_id>/editar/', views.paquete_update, name='paquetes_paquete_update'),
    path('<slug:empresa_slug>/paquetes/<int:paquete_id>/servicios/agregar/', views.paquete_servicio_create, name='paquetes_servicio_create'),
    path(
        '<slug:empresa_slug>/paquetes/<int:paquete_id>/servicios/<int:servicio_id>/eliminar/',
        views.paquete_servicio_delete,
        name='paquetes_servicio_delete',
    ),
    path('<slug:empresa_slug>/paquetes/<int:paquete_id>/media/agregar/', views.paquete_media_create, name='paquetes_media_create'),
    path('<slug:empresa_slug>/paquetes/<int:paquete_id>/portada/', views.paquete_portada, name='paquetes_paquete_portada'),
    path('<slug:empresa_slug>/paquetes/<int:paquete_id>/pdf/', views.paquete_pdf, name='paquetes_paquete_pdf'),
    path('<slug:empresa_slug>/paquetes/<int:paquete_id>/media/<int:media_id>/', views.paquete_media_download, name='paquetes_media_download'),
    path('<slug:empresa_slug>/eventos/<int:evento_id>/propuesta/', views.propuesta_editor, name='paquetes_propuesta_nueva'),
    path('<slug:empresa_slug>/eventos/<int:evento_id>/propuesta/<int:propuesta_id>/', views.propuesta_editor, name='paquetes_propuesta_editor'),
    path(
        '<slug:empresa_slug>/eventos/<int:evento_id>/propuesta/<int:propuesta_id>/lineas/<int:linea_id>/estado/',
        views.propuesta_linea_toggle,
        name='paquetes_propuesta_linea_toggle',
    ),
    path(
        '<slug:empresa_slug>/eventos/<int:evento_id>/propuesta/<int:propuesta_id>/lineas/<int:linea_id>/eliminar/',
        views.propuesta_linea_delete,
        name='paquetes_propuesta_linea_delete',
    ),
]
