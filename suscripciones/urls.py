from django.urls import path

from . import views


urlpatterns = [
    path('estado/', views.estado_suscripcion, name='suscripcion_estado'),
]
