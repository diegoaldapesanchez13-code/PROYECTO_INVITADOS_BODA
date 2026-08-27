from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("eventos", "0007_expediente_retencion_autorizacion_d63"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterField(
            model_name="expedientehistoricoevento",
            name="formato",
            field=models.CharField(
                choices=[
                    ("K9_D6_STRUCTURED_V1", "K9 D6 structured v1"),
                    ("K9_D6_FULL_V2", "K9 D6 full v2"),
                    ("K9_D6_PURGE_READY_V3", "K9 D6 purge-ready v3"),
                ],
                default="K9_D6_STRUCTURED_V1",
                max_length=40,
            ),
        ),
        migrations.AddField(
            model_name="expedientehistoricoevento",
            name="purga_ejecutada_en",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="expedientehistoricoevento",
            name="purga_ejecutada_por",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="expedientes_historicos_evento_purgados",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="expedientehistoricoevento",
            name="resultado_purga",
            field=models.JSONField(blank=True, default=dict),
        ),
    ]
