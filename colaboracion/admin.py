from django.contrib import admin

from .models import (
    CotizacionProveedor,
    ExpedienteServicio,
    MensajeExpediente,
    PartidaPresupuestoCliente,
    PropuestaCliente,
)


admin.site.register(ExpedienteServicio)
admin.site.register(MensajeExpediente)
admin.site.register(CotizacionProveedor)
admin.site.register(PropuestaCliente)
admin.site.register(PartidaPresupuestoCliente)
