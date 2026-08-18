from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('documentos', '0004_visible_proveedor_k875'),
    ]

    operations = [
        migrations.AddField(model_name='documentoevento', name='archivado_en', field=models.DateTimeField(blank=True, null=True)),
        migrations.AddField(model_name='documentoevento', name='archivado_por', field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='documentos_evento_archivados', to=settings.AUTH_USER_MODEL)),
        migrations.AddField(model_name='documentoevento', name='motivo_archivo', field=models.TextField(blank=True, null=True)),
    ]
