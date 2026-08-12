from datetime import time

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
from django.db.models import Q


def clasificar_y_migrar(apps, schema_editor):
    Actividad = apps.get_model('itinerario', 'ActividadItinerario')
    Participante = apps.get_model('itinerario', 'ParticipanteActividad')
    Tarea = apps.get_model('tareas', 'TareaEvento')
    ParticipanteEvento = apps.get_model('eventos', 'ParticipanteEvento')

    hitos = {'CEREMONIA', 'RECEPCION', 'CENA', 'BRINDIS', 'BAILE', 'PASTEL'}
    for actividad in Actividad.objects.all():
        if actividad.categoria in hitos and not actividad.servicio_evento_id:
            actividad.tipo = 'HITO'
        elif actividad.servicio_evento_id and actividad.proveedor_id:
            actividad.tipo = 'CITA'
        else:
            actividad.tipo = 'ACTIVIDAD'
        actividad.save(update_fields=['tipo'])

    # Las tareas antiguas con rango horario representaban una cita de forma ambigua.
    # Se materializan como CITA y se limpian sus horas para que Tarea vuelva a tener
    # una sola semántica: trabajo pendiente con fecha límite.
    for tarea in Tarea.objects.filter(Q(hora_inicio__isnull=False) | Q(hora_fin__isnull=False)):
        fecha = tarea.fecha_inicio or tarea.fecha_limite
        if not fecha:
            tarea.hora_inicio = None
            tarea.hora_fin = None
            tarea.save(update_fields=['hora_inicio', 'hora_fin'])
            continue
        inicio = tarea.hora_inicio or tarea.hora_fin or time(9, 0)
        fin = tarea.hora_fin if tarea.hora_fin and tarea.hora_fin > inicio else None
        actividad, _ = Actividad.objects.get_or_create(
            evento_id=tarea.evento_id,
            servicio_evento_id=tarea.servicio_evento_id,
            titulo=tarea.titulo,
            fecha=fecha,
            hora_inicio=inicio,
            defaults={
                'tipo': 'CITA',
                'descripcion': tarea.descripcion,
                'hora_fin': fin,
                'responsable_id': tarea.responsable_id,
                'prioridad': tarea.prioridad,
                'estado': 'CONFIRMADA' if tarea.estado == 'COMPLETADA' else 'PENDIENTE',
                'categoria': 'PROVEEDORES' if tarea.servicio_evento_id else 'OTRO',
                'notas': tarea.notas,
            },
        )
        if actividad.tipo != 'CITA':
            actividad.tipo = 'CITA'
            actividad.save(update_fields=['tipo'])
        tarea.hora_inicio = None
        tarea.hora_fin = None
        tarea.save(update_fields=['hora_inicio', 'hora_fin'])

    # Participantes por defecto de las citas existentes.
    for actividad in Actividad.objects.filter(tipo='CITA'):
        for pe in ParticipanteEvento.objects.filter(evento_id=actividad.evento_id, activo=True):
            rol = pe.rol if pe.rol in {'CLIENTE', 'PLANNER', 'COLABORADOR'} else 'COLABORADOR'
            Participante.objects.get_or_create(
                actividad_id=actividad.id,
                usuario_id=pe.usuario_id,
                defaults={
                    'rol': rol,
                    'estado': 'PENDIENTE',
                    'requerido': True,
                },
            )
        if actividad.proveedor_id:
            Participante.objects.get_or_create(
                actividad_id=actividad.id,
                proveedor_id=actividad.proveedor_id,
                defaults={
                    'rol': 'PROVEEDOR',
                    'estado': 'PENDIENTE',
                    'requerido': True,
                },
            )


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('itinerario', '0002_servicio_evento_k86'),
        ('tareas', '0004_servicio_evento_k86'),
        ('eventos', '0002_backfill_participantes_legacy'),
        ('proveedores', '0009_financial_semantics_k831'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='actividaditinerario',
            options={'ordering': ['evento', 'fecha', 'hora_inicio', 'orden'], 'verbose_name': 'Actividad de agenda', 'verbose_name_plural': 'Actividades de agenda'},
        ),
        migrations.AddField(
            model_name='actividaditinerario',
            name='tipo',
            field=models.CharField(choices=[('CITA', 'Cita'), ('ACTIVIDAD', 'Actividad operativa'), ('HITO', 'Hito del evento')], default='ACTIVIDAD', max_length=15),
        ),
        migrations.CreateModel(
            name='ParticipanteActividad',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('rol', models.CharField(choices=[('CLIENTE', 'Cliente'), ('PLANNER', 'Planner'), ('COLABORADOR', 'Colaborador'), ('PROVEEDOR', 'Proveedor'), ('OTRO', 'Otro')], max_length=20)),
                ('nombre_snapshot', models.CharField(blank=True, max_length=180, null=True)),
                ('requerido', models.BooleanField(default=True)),
                ('estado', models.CharField(choices=[('PENDIENTE', 'Pendiente de confirmar'), ('CONFIRMADO', 'Confirmado'), ('NO_ASISTE', 'No asistirá'), ('REPROGRAMAR', 'Solicita reprogramar'), ('NO_REQUIERE', 'No requiere confirmación')], default='PENDIENTE', max_length=20)),
                ('comentario', models.TextField(blank=True, null=True)),
                ('respondido_en', models.DateTimeField(blank=True, null=True)),
                ('fecha_creacion', models.DateTimeField(auto_now_add=True)),
                ('actividad', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='participantes', to='itinerario.actividaditinerario')),
                ('proveedor', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='participaciones_agenda', to='proveedores.proveedor')),
                ('usuario', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='participaciones_agenda', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Participante de agenda',
                'verbose_name_plural': 'Participantes de agenda',
                'ordering': ['actividad', 'rol', 'id'],
            },
        ),
        migrations.AddConstraint(
            model_name='participanteactividad',
            constraint=models.UniqueConstraint(condition=Q(usuario__isnull=False), fields=('actividad', 'usuario'), name='itin_part_act_usuario_unico'),
        ),
        migrations.AddConstraint(
            model_name='participanteactividad',
            constraint=models.UniqueConstraint(condition=Q(proveedor__isnull=False), fields=('actividad', 'proveedor'), name='itin_part_act_prov_unico'),
        ),
        migrations.AddIndex(
            model_name='participanteactividad',
            index=models.Index(fields=['actividad', 'estado'], name='itin_part_act_est_idx'),
        ),
        migrations.AddIndex(
            model_name='participanteactividad',
            index=models.Index(fields=['usuario', 'estado'], name='itin_part_usr_est_idx'),
        ),
        migrations.AddIndex(
            model_name='participanteactividad',
            index=models.Index(fields=['proveedor', 'estado'], name='itin_part_prov_est_idx'),
        ),
        migrations.RunPython(clasificar_y_migrar, noop_reverse),
    ]
