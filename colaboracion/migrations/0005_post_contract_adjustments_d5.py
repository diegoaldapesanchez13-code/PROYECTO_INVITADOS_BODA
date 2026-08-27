from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ("colaboracion", "0004_decisions_quotes_approvals_k85"),
        ("eventos", "0004_contratoevento_materializacion_version_and_more"),
        ("proveedores", "0009_financial_semantics_k831"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterField(
            model_name="propuestaserviciocliente",
            name="modalidad",
            field=models.CharField(
                choices=[
                    ("INCLUIDO", "Incluido en paquete"),
                    ("UPGRADE", "Upgrade / diferencia"),
                    ("ADICIONAL", "Servicio adicional"),
                    ("CORTESIA", "Cortesia"),
                ],
                default="ADICIONAL",
                max_length=20,
            ),
        ),
        migrations.CreateModel(
            name="AjusteContractualServicio",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("tipo", models.CharField(choices=[("UPGRADE", "Upgrade / diferencia"), ("ADICIONAL", "Servicio adicional"), ("CORTESIA", "Cortesia")], max_length=20)),
                ("descripcion_snapshot", models.TextField(blank=True, null=True)),
                ("monto_cliente", models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ("valor_informativo", models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ("moneda", models.CharField(default="MXN", max_length=3)),
                ("estado", models.CharField(choices=[("VIGENTE", "Vigente"), ("ANULADO", "Anulado")], default="VIGENTE", max_length=15)),
                ("aprobado_en", models.DateTimeField(default=django.utils.timezone.now)),
                ("anulado_en", models.DateTimeField(blank=True, null=True)),
                ("motivo_anulacion", models.TextField(blank=True, null=True)),
                ("fecha_creacion", models.DateTimeField(auto_now_add=True)),
                ("fecha_actualizacion", models.DateTimeField(auto_now=True)),
                ("aprobado_por", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="ajustes_contractuales_aprobados", to=settings.AUTH_USER_MODEL)),
                ("anulado_por", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="ajustes_contractuales_anulados", to=settings.AUTH_USER_MODEL)),
                ("contrato_base", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="ajustes_contractuales", to="eventos.contratoevento")),
                ("evento", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="ajustes_contractuales_servicio", to="invitaciones.eventoboda")),
                ("propuesta_origen", models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, related_name="ajuste_contractual", to="colaboracion.propuestaserviciocliente")),
                ("servicio_evento", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="ajustes_contractuales", to="proveedores.servicioevento")),
            ],
            options={"ordering": ["evento", "aprobado_en", "id"]},
        ),
        migrations.AddIndex(
            model_name="ajustecontractualservicio",
            index=models.Index(fields=["evento", "estado"], name="colab_ajuste_evt_est_idx"),
        ),
        migrations.AddIndex(
            model_name="ajustecontractualservicio",
            index=models.Index(fields=["contrato_base", "estado"], name="colab_ajuste_ctr_est_idx"),
        ),
    ]
