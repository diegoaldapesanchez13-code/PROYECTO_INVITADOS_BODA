from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("paquetes", "0006_remove_legacy_package_models_k9"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="propuestaevento",
            name="aceptado_en",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="propuestaevento",
            name="aceptado_por",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="propuestas_k9_aceptadas",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="propuestaevento",
            name="snapshot_aceptacion",
            field=models.JSONField(blank=True, default=dict),
        ),
        migrations.AddField(
            model_name="propuestaevento",
            name="snapshot_aceptacion_version",
            field=models.PositiveIntegerField(default=0),
        ),
    ]
