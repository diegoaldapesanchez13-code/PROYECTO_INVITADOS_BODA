# Generated manually for DIRTEC Event Studio K.8.2.
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import invitaciones.models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('invitaciones', '0032_guest_domain_v2'),
    ]

    operations = [
        migrations.CreateModel(
            name='ParticipanteEvento',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('rol', models.CharField(choices=[('CLIENTE', 'Cliente'), ('PLANNER', 'Wedding planner'), ('COLABORADOR', 'Colaborador')], max_length=20)),
                ('activo', models.BooleanField(default=True)),
                ('es_contacto_principal', models.BooleanField(default=False)),
                ('puede_ver_finanzas', models.BooleanField(default=False)),
                ('puede_aprobar', models.BooleanField(default=False)),
                ('puede_gestionar_invitados', models.BooleanField(default=False)),
                ('puede_gestionar_servicios', models.BooleanField(default=False)),
                ('notas', models.TextField(blank=True, null=True)),
                ('fecha_creacion', models.DateTimeField(auto_now_add=True)),
                ('fecha_actualizacion', models.DateTimeField(auto_now=True)),
                ('evento', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='participantes_evento', to='invitaciones.eventoboda')),
                ('usuario', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='participaciones_evento', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Participante del evento',
                'verbose_name_plural': 'Participantes del evento',
                'ordering': ['evento', 'rol', 'usuario__username'],
            },
        ),
        migrations.CreateModel(
            name='ContratoEvento',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('numero_contrato', models.CharField(blank=True, max_length=80, null=True)),
                ('version', models.PositiveIntegerField(default=1)),
                ('estado', models.CharField(choices=[('BORRADOR', 'Borrador'), ('EN_REVISION', 'En revision'), ('FIRMADO', 'Firmado'), ('CANCELADO', 'Cancelado'), ('REEMPLAZADO', 'Reemplazado')], default='BORRADOR', max_length=20)),
                ('monto_base', models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ('moneda', models.CharField(default='MXN', max_length=3)),
                ('fecha_emision', models.DateField(blank=True, null=True)),
                ('fecha_firma', models.DateField(blank=True, null=True)),
                ('archivo', models.FileField(blank=True, null=True, upload_to='eventos/contratos/', validators=[invitaciones.models.validar_documento])),
                ('snapshot_comercial', models.JSONField(blank=True, default=dict)),
                ('notas', models.TextField(blank=True, null=True)),
                ('fecha_creacion', models.DateTimeField(auto_now_add=True)),
                ('fecha_actualizacion', models.DateTimeField(auto_now=True)),
                ('creado_por', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='contratos_evento_creados', to=settings.AUTH_USER_MODEL)),
                ('evento', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='contratos_evento', to='invitaciones.eventoboda')),
            ],
            options={
                'verbose_name': 'Contrato del evento',
                'verbose_name_plural': 'Contratos del evento',
                'ordering': ['evento', '-version', '-id'],
            },
        ),
        migrations.AddConstraint(
            model_name='participanteevento',
            constraint=models.UniqueConstraint(fields=('evento', 'usuario', 'rol'), name='eventos_participante_evento_usuario_rol_unico'),
        ),
        migrations.AddIndex(
            model_name='participanteevento',
            index=models.Index(fields=['evento', 'rol', 'activo'], name='evt_part_evt_rol_act_idx'),
        ),
        migrations.AddIndex(
            model_name='participanteevento',
            index=models.Index(fields=['usuario', 'activo'], name='evt_part_usr_act_idx'),
        ),
        migrations.AddConstraint(
            model_name='contratoevento',
            constraint=models.UniqueConstraint(fields=('evento', 'version'), name='eventos_contrato_evento_version_unica'),
        ),
        migrations.AddIndex(
            model_name='contratoevento',
            index=models.Index(fields=['evento', 'estado'], name='evt_contrato_evt_est_idx'),
        ),
    ]
