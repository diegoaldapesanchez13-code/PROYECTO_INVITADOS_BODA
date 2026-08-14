from django.urls import path

from . import views


urlpatterns = [
    path('<slug:empresa_slug>/servicios/', views.servicio_list, name='catalogo_servicio_list'),
    path('<slug:empresa_slug>/servicios/nuevo/', views.servicio_create, name='catalogo_servicio_create'),
    path('<slug:empresa_slug>/servicios/<int:servicio_id>/', views.servicio_detail, name='catalogo_servicio_detail'),
    path('<slug:empresa_slug>/servicios/<int:servicio_id>/editar/', views.servicio_update, name='catalogo_servicio_update'),
    path('<slug:empresa_slug>/servicios/<int:servicio_id>/estado/', views.servicio_toggle, name='catalogo_servicio_toggle'),
    path('<slug:empresa_slug>/servicios/<int:servicio_id>/archivos/agregar/', views.archivo_create, name='catalogo_archivo_create'),
    path('<slug:empresa_slug>/servicios/<int:servicio_id>/imagen/', views.servicio_imagen, name='catalogo_servicio_imagen'),
    path('<slug:empresa_slug>/servicios/<int:servicio_id>/archivos/<int:archivo_id>/', views.archivo_download, name='catalogo_archivo_download'),
]
