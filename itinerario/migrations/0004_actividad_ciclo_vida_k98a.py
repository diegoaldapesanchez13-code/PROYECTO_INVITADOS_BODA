from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('itinerario', '0003_agenda_semantics_k8712'),
    ]

    operations = [
        migrations.AddField(model_name='actividaditinerario', name='archivado_en', field=models.DateTimeField(blank=True, null=True)),
        migrations.AddField(model_name='actividaditinerario', name='archivado_por', field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='actividades_itinerario_archivadas', to=settings.AUTH_USER_MODEL)),
        migrations.AddField(model_name='actividaditinerario', name='cancelado_en', field=models.DateTimeField(blank=True, null=True)),
        migrations.AddField(model_name='actividaditinerario', name='cancelado_por', field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='actividades_itinerario_canceladas', to=settings.AUTH_USER_MODEL)),
        migrations.AddField(model_name='actividaditinerario', name='motivo_cancelacion', field=models.TextField(blank=True, null=True)),
    ]
