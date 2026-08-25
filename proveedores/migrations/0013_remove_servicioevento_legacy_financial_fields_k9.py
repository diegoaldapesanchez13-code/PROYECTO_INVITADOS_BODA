from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("proveedores", "0012_remove_legacy_commercial_k9"),
    ]

    operations = [
        migrations.RemoveField(model_name="servicioevento", name="costo_total"),
        migrations.RemoveField(model_name="servicioevento", name="precio_cliente"),
        migrations.RemoveField(model_name="servicioevento", name="ajuste_cliente"),
    ]
