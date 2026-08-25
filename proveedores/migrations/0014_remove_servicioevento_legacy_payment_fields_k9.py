from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("proveedores", "0013_remove_servicioevento_legacy_financial_fields_k9"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="servicioevento",
            name="anticipo",
        ),
        migrations.RemoveField(
            model_name="servicioevento",
            name="fecha_limite_pago",
        ),
        migrations.RemoveField(
            model_name="servicioevento",
            name="comprobante_pago",
        ),
    ]
