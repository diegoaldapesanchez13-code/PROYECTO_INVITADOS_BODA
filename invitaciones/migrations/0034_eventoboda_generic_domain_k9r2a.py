from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('invitaciones', '0033_repair_component_layout_columns'),
    ]

    operations = [
        migrations.AlterField(
            model_name='eventoboda',
            name='estado',
            field=models.CharField(
                choices=[
                    ('BORRADOR', 'Borrador'),
                    ('ACTIVO', 'Activo'),
                    ('PLANEACION', 'Planeacion'),
                    ('PREPARACION', 'En preparacion'),
                    ('CONFIRMADO', 'Confirmado'),
                    ('EN_CURSO', 'En curso'),
                    ('FINALIZADO', 'Finalizado'),
                    ('CANCELADO', 'Cancelado'),
                    ('ARCHIVADO', 'Archivado'),
                ],
                default='BORRADOR',
                max_length=20,
            ),
        ),
        migrations.AlterField(
            model_name='eventoboda',
            name='tipo_evento',
            field=models.CharField(
                choices=[
                    ('BODA', 'Boda'),
                    ('XV', 'XV anos'),
                    ('BABY_SHOWER', 'Baby shower'),
                    ('BAUTIZO', 'Bautizo'),
                    ('CUMPLEANOS', 'Cumpleanos'),
                    ('ANIVERSARIO', 'Aniversario'),
                    ('CORPORATIVO', 'Corporativo'),
                    ('OTRO', 'Otro'),
                ],
                default='OTRO',
                max_length=20,
            ),
        ),
        migrations.AlterField(
            model_name='eventoboda',
            name='novio',
            field=models.CharField(blank=True, default='', max_length=100),
        ),
        migrations.AlterField(
            model_name='eventoboda',
            name='novia',
            field=models.CharField(blank=True, default='', max_length=100),
        ),
        migrations.AlterField(
            model_name='eventoboda',
            name='frase_portada',
            field=models.CharField(blank=True, default='', max_length=255),
        ),
        migrations.AlterField(
            model_name='eventoboda',
            name='mensaje_general',
            field=models.TextField(blank=True, default=''),
        ),
        migrations.AlterField(
            model_name='eventoboda',
            name='fecha_misa',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='eventoboda',
            name='lugar_misa',
            field=models.CharField(blank=True, default='', max_length=200),
        ),
        migrations.AlterField(
            model_name='eventoboda',
            name='fecha_fiesta',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='eventoboda',
            name='lugar_fiesta',
            field=models.CharField(blank=True, default='', max_length=200),
        ),
        migrations.AddField(
            model_name='eventoboda',
            name='fecha_inicio',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='eventoboda',
            name='fecha_fin',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='eventoboda',
            name='cancelado_en',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='eventoboda',
            name='cancelado_por',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='eventos_cancelados_k9',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name='eventoboda',
            name='motivo_cancelacion',
            field=models.TextField(blank=True, default=''),
        ),
        migrations.AddField(
            model_name='eventoboda',
            name='archivado_en',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='eventoboda',
            name='archivado_por',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='eventos_archivados_k9',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name='eventoboda',
            name='estado_previo_archivado',
            field=models.CharField(blank=True, default='', max_length=20),
        ),
    ]
