from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("eventos", "0004_contratoevento_materializacion_version_and_more"),
        ("organizaciones", "0002_empresasuscriptora_colores_marca_and_more"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="ExpedienteHistoricoEvento",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("evento_id_snapshot", models.PositiveBigIntegerField()),
                ("evento_nombre_snapshot", models.CharField(max_length=200)),
                ("formato", models.CharField(choices=[("K9_D6_STRUCTURED_V1", "K9 D6 structured v1")], default="K9_D6_STRUCTURED_V1", max_length=40)),
                ("sha256", models.CharField(max_length=64)),
                ("tamano_bytes", models.PositiveBigIntegerField(default=0)),
                ("manifest", models.JSONField(blank=True, default=dict)),
                ("incluye_binarios", models.BooleanField(default=False)),
                ("completo_para_purga_historica", models.BooleanField(default=False)),
                ("generado_en", models.DateTimeField(auto_now_add=True)),
                ("empresa", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="expedientes_historicos_evento", to="organizaciones.empresasuscriptora")),
                ("evento", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="expedientes_historicos_generados", to="invitaciones.eventoboda")),
                ("generado_por", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="expedientes_historicos_evento_generados", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-generado_en", "-id"]},
        ),
        migrations.AddIndex(
            model_name="expedientehistoricoevento",
            index=models.Index(fields=["empresa", "generado_en"], name="evt_exp_emp_gen_idx"),
        ),
        migrations.AddIndex(
            model_name="expedientehistoricoevento",
            index=models.Index(fields=["evento_id_snapshot"], name="evt_exp_evt_snap_idx"),
        ),
    ]
