from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('documentos', '0003_servicio_evento_k86'),
    ]

    operations = [
        migrations.AddField(
            model_name='documentoevento',
            name='visible_proveedor',
            field=models.BooleanField(default=False),
        ),
    ]
