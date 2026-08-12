import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('proveedores', '0009_financial_semantics_k831'),
        ('tareas', '0003_tareaevento_hora_inicio_hora_fin'),
    ]
    operations = [
        migrations.AddField(
            model_name='tareaevento',
            name='servicio_evento',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='tareas_operativas',
                to='proveedores.servicioevento',
                help_text='Servicio del evento al que pertenece esta tarea, cuando aplique.',
            ),
        ),
    ]
