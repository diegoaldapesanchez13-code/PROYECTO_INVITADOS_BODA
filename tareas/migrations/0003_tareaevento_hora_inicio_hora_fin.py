from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("tareas", "0002_alter_tareaevento_evidencia"),
    ]

    operations = [
        migrations.AddField(
            model_name="tareaevento",
            name="hora_inicio",
            field=models.TimeField(
                blank=True,
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="tareaevento",
            name="hora_fin",
            field=models.TimeField(
                blank=True,
                null=True,
            ),
        ),
    ]
