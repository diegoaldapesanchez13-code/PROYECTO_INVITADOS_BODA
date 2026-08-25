from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('paquetes', '0005_alter_propuestaevento_estado'),
        ('proveedores', '0012_remove_legacy_commercial_k9'),
    ]

    operations = [
        migrations.DeleteModel(
            name='PaqueteEvento',
        ),
        migrations.DeleteModel(
            name='ServicioPaquete',
        ),
    ]
