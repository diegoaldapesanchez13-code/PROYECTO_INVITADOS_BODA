from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import invitaciones.models


class Migration(migrations.Migration):
    dependencies = [
        ("colaboracion", "0003_migrate_legacy_messages_k84"),
        ("proveedores", "0009_financial_semantics_k831"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="DecisionServicio",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("titulo", models.CharField(max_length=180)),
                ("descripcion", models.TextField(blank=True, null=True)),
                ("estado", models.CharField(choices=[("VIGENTE", "Vigente"), ("REEMPLAZADA", "Reemplazada"), ("CANCELADA", "Cancelada")], default="VIGENTE", max_length=20)),
                ("fecha_decision", models.DateTimeField(default=django.utils.timezone.now)),
                ("fecha_creacion", models.DateTimeField(auto_now_add=True)),
                ("mensaje_origen", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="decisiones_generadas", to="colaboracion.mensajeservicio")),
                ("registrado_por", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="decisiones_servicio_registradas", to=settings.AUTH_USER_MODEL)),
                ("servicio_evento", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="decisiones_workspace", to="proveedores.servicioevento")),
                ("tema", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="decisiones", to="colaboracion.temaservicio")),
            ],
            options={"ordering": ["-fecha_decision", "-id"]},
        ),
        migrations.CreateModel(
            name="CotizacionServicio",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("version", models.PositiveIntegerField()),
                ("costo_proveedor", models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ("descripcion", models.TextField(blank=True, null=True)),
                ("vigencia", models.DateField(blank=True, null=True)),
                ("archivo", models.FileField(blank=True, null=True, upload_to="colaboracion/workspace/cotizaciones/", validators=[invitaciones.models.validar_documento])),
                ("estado", models.CharField(choices=[("ENVIADA", "Enviada"), ("CAMBIOS_SOLICITADOS", "Cambios solicitados"), ("ACEPTADA", "Aceptada por planner"), ("RECHAZADA", "Rechazada"), ("REEMPLAZADA", "Reemplazada por nueva version")], default="ENVIADA", max_length=25)),
                ("respuesta_planner", models.TextField(blank=True, null=True)),
                ("fecha_creacion", models.DateTimeField(auto_now_add=True)),
                ("fecha_actualizacion", models.DateTimeField(auto_now=True)),
                ("creado_por", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="cotizaciones_servicio_workspace_creadas", to=settings.AUTH_USER_MODEL)),
                ("servicio_evento", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="cotizaciones_workspace", to="proveedores.servicioevento")),
            ],
            options={"ordering": ["-version", "-id"]},
        ),
        migrations.CreateModel(
            name="PropuestaServicioCliente",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("version", models.PositiveIntegerField()),
                ("modalidad", models.CharField(choices=[("INCLUIDO", "Incluido en paquete"), ("UPGRADE", "Upgrade / diferencia"), ("ADICIONAL", "Servicio adicional")], default="ADICIONAL", max_length=20)),
                ("descripcion", models.TextField(blank=True, null=True)),
                ("costo_proveedor_snapshot", models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ("valor_contratado_snapshot", models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ("cargo_adicional_cliente", models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ("estado", models.CharField(choices=[("BORRADOR", "Borrador"), ("ENVIADA", "Enviada al cliente"), ("CAMBIOS_SOLICITADOS", "Cambios solicitados"), ("APROBADA", "Aprobada"), ("RECHAZADA", "Rechazada"), ("REEMPLAZADA", "Reemplazada por nueva version")], default="BORRADOR", max_length=25)),
                ("comentario_cliente", models.TextField(blank=True, null=True)),
                ("fecha_envio", models.DateTimeField(blank=True, null=True)),
                ("fecha_respuesta", models.DateTimeField(blank=True, null=True)),
                ("fecha_creacion", models.DateTimeField(auto_now_add=True)),
                ("fecha_actualizacion", models.DateTimeField(auto_now=True)),
                ("cotizacion", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="propuestas_cliente", to="colaboracion.cotizacionservicio")),
                ("enviado_por", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="propuestas_servicio_workspace_enviadas", to=settings.AUTH_USER_MODEL)),
                ("respondido_por", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="propuestas_servicio_workspace_respondidas", to=settings.AUTH_USER_MODEL)),
                ("servicio_evento", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="propuestas_workspace", to="proveedores.servicioevento")),
            ],
            options={"ordering": ["-version", "-id"]},
        ),
        migrations.CreateModel(
            name="AprobacionServicio",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("titulo", models.CharField(max_length=180)),
                ("descripcion", models.TextField(blank=True, null=True)),
                ("estado", models.CharField(choices=[("PENDIENTE", "Pendiente"), ("APROBADA", "Aprobada"), ("CAMBIOS", "Solicita cambios"), ("RECHAZADA", "Rechazada")], default="PENDIENTE", max_length=20)),
                ("comentario_respuesta", models.TextField(blank=True, null=True)),
                ("fecha_solicitud", models.DateTimeField(default=django.utils.timezone.now)),
                ("fecha_respuesta", models.DateTimeField(blank=True, null=True)),
                ("decision", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="aprobaciones", to="colaboracion.decisionservicio")),
                ("propuesta", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="aprobaciones", to="colaboracion.propuestaserviciocliente")),
                ("respondido_por", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="aprobaciones_servicio_workspace_respondidas", to=settings.AUTH_USER_MODEL)),
                ("servicio_evento", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="aprobaciones_workspace", to="proveedores.servicioevento")),
                ("solicitado_por", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="aprobaciones_servicio_workspace_solicitadas", to=settings.AUTH_USER_MODEL)),
                ("tema", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="aprobaciones", to="colaboracion.temaservicio")),
            ],
            options={"ordering": ["estado", "-fecha_solicitud", "-id"]},
        ),
        migrations.AddConstraint(model_name="cotizacionservicio", constraint=models.UniqueConstraint(fields=("servicio_evento", "version"), name="colab_cot_srv_version_unica")),
        migrations.AddConstraint(model_name="propuestaserviciocliente", constraint=models.UniqueConstraint(fields=("servicio_evento", "version"), name="colab_prop_srv_version_unica")),
        migrations.AddIndex(model_name="decisionservicio", index=models.Index(fields=["servicio_evento", "estado"], name="colab_dec_srv_est_idx")),
        migrations.AddIndex(model_name="aprobacionservicio", index=models.Index(fields=["servicio_evento", "estado"], name="colab_apr_srv_est_idx")),
    ]
