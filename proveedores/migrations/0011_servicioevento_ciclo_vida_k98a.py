from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('proveedores', '0010_servicioevento_contrato_origen_and_more'),
    ]

    operations = [
        migrations.AddField(model_name='servicioevento', name='archivado_en', field=models.DateTimeField(blank=True, null=True)),
        migrations.AddField(model_name='servicioevento', name='archivado_por', field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='servicios_evento_archivados', to=settings.AUTH_USER_MODEL)),
        migrations.AddField(model_name='servicioevento', name='cancelado_en', field=models.DateTimeField(blank=True, null=True)),
        migrations.AddField(model_name='servicioevento', name='cancelado_por', field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='servicios_evento_cancelados', to=settings.AUTH_USER_MODEL)),
        migrations.AddField(model_name='servicioevento', name='motivo_cancelacion', field=models.TextField(blank=True, null=True)),
    ]
