from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("eventos", "0006_expediente_historico_integrity_d62"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="expedientehistoricoevento",
            name="respaldo_externo_confirmado_en",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="expedientehistoricoevento",
            name="respaldo_externo_confirmado_por",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="expedientes_historicos_evento_confirmados",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="expedientehistoricoevento",
            name="retencion_hasta",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="expedientehistoricoevento",
            name="purga_historica_autorizada_en",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="expedientehistoricoevento",
            name="purga_historica_autorizada_por",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="expedientes_historicos_evento_autorizados",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="expedientehistoricoevento",
            name="motivo_autorizacion_purga",
            field=models.TextField(blank=True, null=True),
        ),
    ]
