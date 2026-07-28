from django.contrib.auth import views as auth_views
from django.urls import path

from .views import LoginCentralView, redirigir_por_rol


urlpatterns = [
    path('login/', LoginCentralView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
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
