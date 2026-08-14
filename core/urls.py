from django.contrib.auth import views as auth_views
from django.urls import path

from .views import LoginCentralView, redirigir_por_rol
from . import secure_files


urlpatterns = [
    path('secure/documentos/<int:documento_id>/', secure_files.documento_evento, name='secure_documento_evento'),
    path('secure/pagos-cliente/<int:pago_id>/', secure_files.pago_cliente_comprobante, name='secure_pago_cliente_comprobante'),
    path('secure/pagos-operativos/<int:pago_id>/', secure_files.pago_operativo_comprobante, name='secure_pago_operativo_comprobante'),
    path('secure/cotizaciones/<int:cotizacion_id>/', secure_files.cotizacion_servicio, name='secure_cotizacion_servicio'),
    path('secure/adjuntos/<int:adjunto_id>/', secure_files.adjunto_workspace, name='secure_adjunto_workspace'),
    path('secure/tareas/<int:tarea_id>/evidencia/', secure_files.evidencia_tarea, name='secure_evidencia_tarea'),
    path('login/', LoginCentralView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login', redirect_field_name=None), name='logout'),
    path('redirigir/', redirigir_por_rol, name='redirigir_por_rol'),
    path(
        'password-reset/',
        auth_views.PasswordResetView.as_view(
            template_name='core/password_reset_form.html',
            email_template_name='core/password_reset_email.txt',
            subject_template_name='core/password_reset_subject.txt',
            success_url='/password-reset/enviado/',
        ),
        name='password_reset',
    ),
    path(
        'password-reset/enviado/',
        auth_views.PasswordResetDoneView.as_view(template_name='core/password_reset_done.html'),
        name='password_reset_done',
    ),
    path(
        'password-reset/<uidb64>/<token>/',
        auth_views.PasswordResetConfirmView.as_view(
            template_name='core/password_reset_confirm.html',
            success_url='/password-reset/completo/',
        ),
        name='password_reset_confirm',
    ),
    path(
        'password-reset/completo/',
        auth_views.PasswordResetCompleteView.as_view(template_name='core/password_reset_complete.html'),
        name='password_reset_complete',
    ),
]
