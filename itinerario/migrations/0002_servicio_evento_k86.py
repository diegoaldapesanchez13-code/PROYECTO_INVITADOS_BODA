import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('proveedores', '0009_financial_semantics_k831'),
        ('itinerario', '0001_initial'),
    ]
    operations = [
        migrations.AddField(
            model_name='actividaditinerario',
            name='servicio_evento',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='actividades_agenda',
                to='proveedores.servicioevento',
                help_text='Servicio del evento relacionado con esta actividad, cuando aplique.',
            ),
        ),
    ]
