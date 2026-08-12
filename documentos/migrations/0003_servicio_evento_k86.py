import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('proveedores', '0009_financial_semantics_k831'),
        ('documentos', '0002_alter_documentoevento_archivo_and_more'),
    ]
    operations = [
        migrations.AddField(
            model_name='documentoevento',
            name='servicio_evento',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='documentos_operativos',
                to='proveedores.servicioevento',
                help_text='Servicio del evento al que corresponde el documento, cuando aplique.',
            ),
        ),
    ]
