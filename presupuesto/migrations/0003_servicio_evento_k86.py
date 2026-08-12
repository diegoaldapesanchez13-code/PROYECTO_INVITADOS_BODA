import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('proveedores', '0009_financial_semantics_k831'),
        ('presupuesto', '0002_alter_pagoevento_comprobante'),
    ]
    operations = [
        migrations.AddField(
            model_name='gastoevento',
            name='servicio_evento',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='gastos_operativos',
                to='proveedores.servicioevento',
                help_text='Servicio del evento que origina este gasto, cuando aplique.',
            ),
        ),
    ]
