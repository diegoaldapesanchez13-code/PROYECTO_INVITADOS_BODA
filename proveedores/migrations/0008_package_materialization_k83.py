# Generated for DIRTEC Event Studio K.8.3

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('paquetes', '0003_package_snapshot_materialization_k83'),
        ('proveedores', '0007_event_domain_foundation'),
    ]

    operations = [
        migrations.AddField(
            model_name='servicioevento',
            name='cantidad_paquete',
            field=models.PositiveIntegerField(default=1),
        ),
        migrations.AddField(
            model_name='servicioevento',
            name='paquete_evento',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='servicios_materializados', to='paquetes.paqueteevento'),
        ),
        migrations.AddField(
            model_name='servicioevento',
            name='paquete_nombre_snapshot',
            field=models.CharField(blank=True, max_length=160, null=True),
        ),
        migrations.AddField(
            model_name='servicioevento',
            name='paquete_servicio_snapshot',
            field=models.JSONField(blank=True, default=dict),
        ),
        migrations.AddField(
            model_name='servicioevento',
            name='servicio_paquete_origen',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='servicios_evento_materializados', to='paquetes.serviciopaquete'),
        ),
        migrations.AddIndex(
            model_name='servicioevento',
            index=models.Index(fields=['paquete_evento', 'origen'], name='prov_srv_pkg_orig_idx'),
        ),
        migrations.AddConstraint(
            model_name='servicioevento',
            constraint=models.UniqueConstraint(fields=('paquete_evento', 'servicio_paquete_origen'), name='prov_srv_pkg_item_unico'),
        ),
    ]
