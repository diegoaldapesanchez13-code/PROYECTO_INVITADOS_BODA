from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import invitaciones.models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("invitaciones", "0032_guest_domain_v2"),
        ("proveedores", "0006_servicioevento_estado_proveedor_y_comentario"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="ExpedienteServicio",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("titulo", models.CharField(max_length=180)),
                ("descripcion", models.TextField(blank=True, null=True)),
                ("categoria", models.CharField(choices=[("DECORACION","Decoracion"),("MENU","Menu / banquete"),("MUSICA","Musica / entretenimiento"),("FOTOGRAFIA","Fotografia / video"),("MOBILIARIO","Mobiliario / montaje"),("TRANSPORTE","Transporte"),("INVITACION","Invitacion / papeleria"),("OTRO","Otro")], default="OTRO", max_length=30)),
                ("estado", models.CharField(choices=[("NUEVO","Nueva solicitud"),("EN_ANALISIS","En analisis"),("CONSULTA_PROVEEDOR","Consultando proveedor"),("COTIZACION_RECIBIDA","Cotizacion recibida"),("COTIZACION_ACEPTADA","Cotizacion aceptada por planner"),("PROPUESTA_CLIENTE","Propuesta enviada al cliente"),("CAMBIOS_CLIENTE","Cliente solicito cambios"),("APROBADO_CLIENTE","Aprobado por cliente"),("CONTRATADO","Contratado"),("CERRADO","Cerrado"),("CANCELADO","Cancelado")], default="NUEVO", max_length=30)),
                ("fecha_creacion", models.DateTimeField(auto_now_add=True)),
                ("fecha_actualizacion", models.DateTimeField(auto_now=True)),
                ("cliente_solicitante", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="solicitudes_servicio_cliente", to=settings.AUTH_USER_MODEL)),
                ("creado_por", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="expedientes_servicio_creados", to=settings.AUTH_USER_MODEL)),
                ("evento", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="expedientes_servicio", to="invitaciones.eventoboda")),
                ("proveedor", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="expedientes_colaboracion", to="proveedores.proveedor")),
                ("servicio_evento", models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="expediente_colaboracion", to="proveedores.servicioevento")),
            ],
            options={"verbose_name":"Expediente colaborativo de servicio","verbose_name_plural":"Expedientes colaborativos de servicio","ordering":["-fecha_actualizacion","-id"]},
        ),
        migrations.CreateModel(
            name="MensajeExpediente",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("canal", models.CharField(choices=[("CLIENTE_PLANNER","Cliente / Planner"),("PLANNER_PROVEEDOR","Planner / Proveedor")], max_length=30)),
                ("tipo", models.CharField(choices=[("MENSAJE","Mensaje"),("SISTEMA","Sistema")], default="MENSAJE", max_length=15)),
                ("mensaje", models.TextField(blank=True)),
                ("archivo", models.FileField(blank=True, null=True, upload_to="colaboracion/mensajes/", validators=[invitaciones.models.validar_documento])),
                ("fecha", models.DateTimeField(auto_now_add=True)),
                ("autor", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="mensajes_colaboracion", to=settings.AUTH_USER_MODEL)),
                ("expediente", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="mensajes", to="colaboracion.expedienteservicio")),
            ],
            options={"verbose_name":"Mensaje de expediente","verbose_name_plural":"Mensajes de expediente","ordering":["fecha","id"]},
        ),
        migrations.CreateModel(
            name="CotizacionProveedor",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("version", models.PositiveIntegerField()),
                ("costo_proveedor", models.DecimalField(decimal_places=2, max_digits=12)),
                ("descripcion", models.TextField(blank=True, null=True)),
                ("vigencia", models.DateField(blank=True, null=True)),
                ("archivo", models.FileField(blank=True, null=True, upload_to="colaboracion/cotizaciones/", validators=[invitaciones.models.validar_documento])),
                ("estado", models.CharField(choices=[("ENVIADA","Enviada"),("CAMBIOS_SOLICITADOS","Cambios solicitados"),("ACEPTADA","Aceptada por planner"),("RECHAZADA","Rechazada")], default="ENVIADA", max_length=25)),
                ("respuesta_planner", models.TextField(blank=True, null=True)),
                ("fecha_creacion", models.DateTimeField(auto_now_add=True)),
                ("fecha_actualizacion", models.DateTimeField(auto_now=True)),
                ("creado_por", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="cotizaciones_proveedor_creadas", to=settings.AUTH_USER_MODEL)),
                ("expediente", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="cotizaciones_proveedor", to="colaboracion.expedienteservicio")),
                ("proveedor", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="cotizaciones_colaboracion", to="proveedores.proveedor")),
            ],
            options={"ordering":["-version","-id"]},
        ),
        migrations.AddConstraint(
            model_name="cotizacionproveedor",
            constraint=models.UniqueConstraint(fields=("expediente","version"), name="colaboracion_cotizacion_version_unica"),
        ),
        migrations.CreateModel(
            name="PropuestaCliente",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("version", models.PositiveIntegerField()),
                ("modalidad", models.CharField(choices=[("ADICIONAL","Servicio adicional"),("INCLUIDO_PAQUETE","Incluido en paquete")], default="ADICIONAL", max_length=25)),
                ("descripcion", models.TextField(blank=True, null=True)),
                ("costo_base_snapshot", models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ("margen", models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ("precio_cliente", models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ("referencia_paquete", models.CharField(blank=True, max_length=180, null=True)),
                ("estado", models.CharField(choices=[("BORRADOR","Borrador"),("ENVIADA","Enviada al cliente"),("CAMBIOS_SOLICITADOS","Cambios solicitados"),("APROBADA","Aprobada"),("RECHAZADA","Rechazada"),("REEMPLAZADA","Reemplazada por nueva version")], default="BORRADOR", max_length=25)),
                ("comentario_cliente", models.TextField(blank=True, null=True)),
                ("fecha_envio", models.DateTimeField(blank=True, null=True)),
                ("fecha_respuesta", models.DateTimeField(blank=True, null=True)),
                ("fecha_creacion", models.DateTimeField(auto_now_add=True)),
                ("fecha_actualizacion", models.DateTimeField(auto_now=True)),
                ("cotizacion", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="propuestas_cliente", to="colaboracion.cotizacionproveedor")),
                ("enviado_por", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="propuestas_cliente_enviadas", to=settings.AUTH_USER_MODEL)),
                ("expediente", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="propuestas_cliente", to="colaboracion.expedienteservicio")),
                ("respondido_por", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="propuestas_cliente_respondidas", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering":["-version","-id"]},
        ),
        migrations.AddConstraint(
            model_name="propuestacliente",
            constraint=models.UniqueConstraint(fields=("expediente","version"), name="colaboracion_propuesta_version_unica"),
        ),
        migrations.CreateModel(
            name="PartidaPresupuestoCliente",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("concepto", models.CharField(max_length=180)),
                ("monto_cliente", models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ("incluido_en_paquete", models.BooleanField(default=False)),
                ("estado", models.CharField(choices=[("ACTIVA","Activa"),("CANCELADA","Cancelada")], default="ACTIVA", max_length=15)),
                ("fecha_creacion", models.DateTimeField(auto_now_add=True)),
                ("evento", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="partidas_presupuesto_cliente", to="invitaciones.eventoboda")),
                ("expediente", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="partidas_presupuesto_cliente", to="colaboracion.expedienteservicio")),
                ("propuesta", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="partida_presupuesto", to="colaboracion.propuestacliente")),
            ],
            options={"ordering":["fecha_creacion","id"]},
        ),
    ]
