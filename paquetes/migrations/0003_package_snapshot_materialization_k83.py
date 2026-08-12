# Generated for DIRTEC Event Studio K.8.3

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('paquetes', '0002_paqueteboda_empresa'),
    ]

    operations = [
        migrations.AddField(
            model_name='paqueteevento',
            name='materializacion_version',
            field=models.PositiveIntegerField(default=1),
        ),
        migrations.AddField(
            model_name='paqueteevento',
            name='materializado_en',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='paqueteevento',
            name='snapshot_generado_en',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='paqueteevento',
            name='snapshot_paquete',
            field=models.JSONField(blank=True, default=dict),
        ),
    ]
