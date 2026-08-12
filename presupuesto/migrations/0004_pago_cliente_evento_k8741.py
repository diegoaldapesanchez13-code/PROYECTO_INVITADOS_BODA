from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import invitaciones.models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('presupuesto', '0003_servicio_evento_k86'),
        ('proveedores', '0009_financial_semantics_k831'),
    ]

    operations = [
        migrations.CreateModel(
            name='PagoClienteEvento',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('concepto', models.CharField(blank=True, max_length=160, null=True)),
                ('monto', models.DecimalField(decimal_places=2, max_digits=12)),
                ('fecha_pago', models.DateField(default=django.utils.timezone.localdate)),
                ('metodo_pago', models.CharField(choices=[('EFECTIVO', 'Efectivo'), ('TRANSFERENCIA', 'Transferencia'), ('TARJETA', 'Tarjeta'), ('CHEQUE', 'Cheque'), ('DEPOSITO', 'Deposito'), ('OTRO', 'Otro')], default='TRANSFERENCIA', max_length=20)),
                ('referencia', models.CharField(blank=True, max_length=120, null=True)),
                ('comprobante', models.FileField(upload_to='presupuesto/pagos_cliente_evento/', validators=[invitaciones.models.validar_documento])),
                ('comentario_cliente', models.TextField(blank=True, null=True)),
                ('estado', models.CharField(choices=[('PENDIENTE', 'Pendiente de revisión'), ('RECIBIDO', 'Recibido por empresa / planner'), ('OBSERVADO', 'Observado / requiere revisión'), ('CANCELADO', 'Cancelado')], default='PENDIENTE', max_length=20)),
                ('comentario_equipo', models.TextField(blank=True, null=True)),
                ('fecha_revision', models.DateTimeField(blank=True, null=True)),
                ('fecha_creacion', models.DateTimeField(auto_now_add=True)),
                ('fecha_actualizacion', models.DateTimeField(auto_now=True)),
                ('evento', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='pagos_cliente_reportados', to='invitaciones.eventoboda')),
                ('registrado_por', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='pagos_cliente_evento_registrados', to=settings.AUTH_USER_MODEL)),
                ('revisado_por', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='pagos_cliente_evento_revisados', to=settings.AUTH_USER_MODEL)),
                ('servicio_evento', models.ForeignKey(blank=True, help_text='Concepto opcional del pago; el receptor sigue siendo la empresa/planner.', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='pagos_cliente_evento', to='proveedores.servicioevento')),
            ],
            options={
                'verbose_name': 'Pago reportado por cliente',
                'verbose_name_plural': 'Pagos reportados por clientes',
                'ordering': ['-fecha_pago', '-id'],
            },
        ),
        migrations.AddIndex(
            model_name='pagoclienteevento',
            index=models.Index(fields=['evento', 'estado'], name='pres_pago_cli_evt_est_idx'),
        ),
        migrations.AddIndex(
            model_name='pagoclienteevento',
            index=models.Index(fields=['registrado_por', 'estado'], name='pres_pago_cli_usr2_est_idx'),
        ),
    ]
