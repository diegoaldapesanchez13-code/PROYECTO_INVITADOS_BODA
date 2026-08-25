from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('paquetes', '0005_alter_propuestaevento_estado'),
        ('proveedores', '0011_servicioevento_ciclo_vida_k98a'),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name='servicioevento',
            name='prov_srv_pkg_item_unico',
        ),
        migrations.RemoveIndex(
            model_name='servicioevento',
            name='prov_srv_pkg_orig_idx',
        ),
        migrations.RemoveField(
            model_name='servicioevento',
            name='servicio_catalogo',
        ),
        migrations.RemoveField(
            model_name='servicioevento',
            name='paquete_evento',
        ),
        migrations.RemoveField(
            model_name='servicioevento',
            name='servicio_paquete_origen',
        ),
        migrations.DeleteModel(
            name='ServicioCatalogoProveedor',
        ),
    ]
