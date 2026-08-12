from django.db import migrations, models
import django.db.models.deletion


def backfill_servicio_evento(apps, schema_editor):
    ServicioEvento = apps.get_model('proveedores', 'ServicioEvento')
    for servicio in ServicioEvento.objects.select_related('proveedor').all().iterator():
        updates = {
            'costo_proveedor': servicio.costo_total,
            'precio_cliente': servicio.costo_total,
            'origen': 'MANUAL',
            'modalidad': 'ADICIONAL',
        }
        if servicio.proveedor_id:
            updates['proveedor_nombre_snapshot'] = servicio.proveedor.nombre_comercial
        ServicioEvento.objects.filter(pk=servicio.pk).update(**updates)


class Migration(migrations.Migration):
    dependencies = [
        ('organizaciones', '0002_empresasuscriptora_colores_marca_and_more'),
        ('proveedores', '0006_servicioevento_estado_proveedor_y_comentario'),
    ]

    operations = [
        migrations.CreateModel(
            name='EtiquetaProveedor',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=80)),
                ('activa', models.BooleanField(default=True)),
                ('empresa', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='etiquetas_proveedor', to='organizaciones.empresasuscriptora')),
            ],
            options={'ordering': ['empresa', 'nombre']},
        ),
        migrations.CreateModel(
            name='ServicioCatalogoProveedor',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=160)),
                ('descripcion', models.TextField(blank=True, null=True)),
                ('categoria', models.CharField(blank=True, max_length=50, null=True)),
                ('costo_referencia', models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ('precio_referencia_cliente', models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ('activo', models.BooleanField(default=True)),
                ('fecha_creacion', models.DateTimeField(auto_now_add=True)),
                ('fecha_actualizacion', models.DateTimeField(auto_now=True)),
                ('empresa', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='servicios_catalogo_proveedor', to='organizaciones.empresasuscriptora')),
                ('proveedor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='servicios_catalogo', to='proveedores.proveedor')),
                ('etiquetas', models.ManyToManyField(blank=True, related_name='servicios_catalogo', to='proveedores.etiquetaproveedor')),
            ],
            options={'ordering': ['proveedor', 'nombre']},
        ),
        migrations.AddConstraint(
            model_name='etiquetaproveedor',
            constraint=models.UniqueConstraint(fields=('empresa', 'nombre'), name='proveedores_etiqueta_empresa_nombre_unico'),
        ),
        migrations.AddConstraint(
            model_name='serviciocatalogoproveedor',
            constraint=models.UniqueConstraint(fields=('proveedor', 'nombre'), name='proveedores_servicio_catalogo_proveedor_nombre_unico'),
        ),
        migrations.AddIndex(
            model_name='serviciocatalogoproveedor',
            index=models.Index(fields=['empresa', 'activo'], name='prov_cat_emp_act_idx'),
        ),
        migrations.AddIndex(
            model_name='serviciocatalogoproveedor',
            index=models.Index(fields=['proveedor', 'activo'], name='prov_cat_prov_act_idx'),
        ),
        migrations.AddField(model_name='servicioevento', name='ajuste_cliente', field=models.DecimalField(decimal_places=2, default=0, max_digits=12)),
        migrations.AddField(model_name='servicioevento', name='catalogo_descripcion_snapshot', field=models.TextField(blank=True, null=True)),
        migrations.AddField(model_name='servicioevento', name='catalogo_nombre_snapshot', field=models.CharField(blank=True, max_length=160, null=True)),
        migrations.AddField(model_name='servicioevento', name='categoria', field=models.CharField(blank=True, max_length=50, null=True)),
        migrations.AddField(model_name='servicioevento', name='costo_proveedor', field=models.DecimalField(decimal_places=2, default=0, max_digits=12)),
        migrations.AddField(model_name='servicioevento', name='estado_comercial', field=models.CharField(choices=[('BORRADOR', 'Borrador'), ('COTIZANDO', 'Cotizando'), ('PROPUESTO', 'Propuesto al cliente'), ('APROBADO', 'Aprobado'), ('CONTRATADO', 'Contratado'), ('CANCELADO', 'Cancelado')], default='BORRADOR', max_length=20)),
        migrations.AddField(model_name='servicioevento', name='estado_operativo', field=models.CharField(choices=[('PENDIENTE', 'Pendiente'), ('EN_DEFINICION', 'En definicion'), ('PROGRAMADO', 'Programado'), ('LISTO', 'Listo'), ('EN_EJECUCION', 'En ejecucion'), ('COMPLETADO', 'Completado'), ('INCIDENCIA', 'Incidencia'), ('CANCELADO', 'Cancelado')], default='PENDIENTE', max_length=20)),
        migrations.AddField(model_name='servicioevento', name='modalidad', field=models.CharField(choices=[('INCLUIDO', 'Incluido en paquete'), ('ADICIONAL', 'Servicio adicional'), ('UPGRADE', 'Upgrade / diferencia')], default='ADICIONAL', max_length=15)),
        migrations.AddField(model_name='servicioevento', name='notas_internas', field=models.TextField(blank=True, null=True)),
        migrations.AddField(model_name='servicioevento', name='origen', field=models.CharField(choices=[('MANUAL', 'Manual'), ('CATALOGO', 'Catalogo'), ('PAQUETE', 'Paquete')], default='MANUAL', max_length=15)),
        migrations.AddField(model_name='servicioevento', name='precio_cliente', field=models.DecimalField(decimal_places=2, default=0, max_digits=12)),
        migrations.AddField(model_name='servicioevento', name='proveedor_nombre_snapshot', field=models.CharField(blank=True, max_length=160, null=True)),
        migrations.AddField(model_name='servicioevento', name='servicio_catalogo', field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='instancias_evento', to='proveedores.serviciocatalogoproveedor')),
        migrations.AddIndex(model_name='servicioevento', index=models.Index(fields=['evento', 'estado_operativo'], name='prov_srv_evt_oper_idx')),
        migrations.AddIndex(model_name='servicioevento', index=models.Index(fields=['evento', 'estado_comercial'], name='prov_srv_evt_com_idx')),
        migrations.AddIndex(model_name='servicioevento', index=models.Index(fields=['evento', 'proveedor'], name='prov_srv_evt_prov_idx')),
        migrations.RunPython(backfill_servicio_evento, migrations.RunPython.noop),
    ]
