from django.urls import path
from . import payment_views

urlpatterns = [
    path('cliente/eventos/<int:evento_id>/registrar/', payment_views.registrar_pago_cliente, name='pago_cliente_evento_registrar'),
    path('equipo/pagos/<int:pago_id>/revisar/', payment_views.revisar_pago_cliente, name='pago_cliente_evento_revisar'),
]
