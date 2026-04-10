from django.urls import path
from . import views

urlpatterns = [
    path('', views.inicio, name='inicio'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('exportar-excel/', views.exportar_excel, name='exportar_excel'),
    path('dashboard/marcar-envio/<int:grupo_id>/', views.marcar_envio_invitacion, name='marcar_envio_invitacion'),
    path('dashboard/marcar-recordatorio/<int:grupo_id>/', views.marcar_recordatorio, name='marcar_recordatorio'),
    path('invitacion/<uuid:codigo>/', views.ver_invitacion, name='ver_invitacion'),
]

# Rutas de la aplicación invitaciones:
# - inicio: página principal.
# - dashboard: panel de control.
# - exportar-excel: descarga de confirmaciones en Excel.
# - marcar-envio: actualiza el estado de invitación preparada.
# - marcar-recordatorio: actualiza el estado de recordatorio preparado.
# - invitacion/<uuid>: visualiza la invitación individual del grupo.