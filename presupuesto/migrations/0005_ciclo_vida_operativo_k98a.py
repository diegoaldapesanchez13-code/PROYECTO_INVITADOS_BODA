from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('presupuesto', '0004_pago_cliente_evento_k8741'),
    ]

    operations = [
        migrations.AddField(model_name='gastoevento', name='archivado_en', field=models.DateTimeField(blank=True, null=True)),
        migrations.AddField(model_name='gastoevento', name='archivado_por', field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='gastos_evento_archivados', to=settings.AUTH_USER_MODEL)),
        migrations.AddField(model_name='gastoevento', name='cancelado_en', field=models.DateTimeField(blank=True, null=True)),
        migrations.AddField(model_name='gastoevento', name='cancelado_por', field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='gastos_evento_cancelados', to=settings.AUTH_USER_MODEL)),
        migrations.AddField(model_name='gastoevento', name='motivo_cancelacion', field=models.TextField(blank=True, null=True)),
        migrations.AddField(model_name='pagoevento', name='anulado_en', field=models.DateTimeField(blank=True, null=True)),
        migrations.AddField(model_name='pagoevento', name='anulado_por', field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='pagos_evento_anulados', to=settings.AUTH_USER_MODEL)),
        migrations.AddField(model_name='pagoevento', name='estado', field=models.CharField(choices=[('ACTIVO', 'Activo'), ('ANULADO', 'Anulado')], default='ACTIVO', max_length=20)),
        migrations.AddField(model_name='pagoevento', name='motivo_anulacion', field=models.TextField(blank=True, null=True)),
    ]
