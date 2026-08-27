from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("eventos", "0005_expediente_historico_evento_d61"),
    ]

    operations = [
        migrations.AddField(
            model_name="expedientehistoricoevento",
            name="integridad_verificada",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="expedientehistoricoevento",
            name="binarios_encontrados",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="expedientehistoricoevento",
            name="binarios_faltantes",
            field=models.PositiveIntegerField(default=0),
        ),
    ]
