"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from core.services.permisos import usuario_es_dirtec_operativo


def dirtec_admin_has_permission(request):
    user = request.user
    return bool(
        user.is_active
        and user.is_staff
        and usuario_es_dirtec_operativo(user)
    )


admin.site.has_permission = dirtec_admin_has_permission

urlpatterns = [
    # Ruta para el panel administrativo de Django.
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
    path('suscripcion/', include('suscripciones.urls')),
    # Todas las demás rutas se delegan a la aplicación 'invitaciones'.
    path('', include('invitaciones.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
