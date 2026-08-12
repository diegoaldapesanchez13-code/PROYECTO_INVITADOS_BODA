import django.db.models.deletion
from django.db import migrations, models


def migrate_group_assignments(apps, schema_editor):
    AsignacionMesa = apps.get_model('mesas', 'AsignacionMesa')
    Invitado = apps.get_model('invitaciones', 'Invitado')

    for asignacion in AsignacionMesa.objects.all().order_by('id').iterator():
        # Explicit individual assignment always wins if historical data contains
        # both foreign keys.
        if asignacion.invitado_id:
            continue

        grupo_id = asignacion.grupo_invitacion_id
        if not grupo_id:
            # Invalid historical orphan: there is no person that can be seated.
            asignacion.delete()
            continue

        titular = (
            Invitado.objects
            .filter(
                grupo_id=grupo_id,
                es_acompanante_extra=False,
            )
            .order_by('orden', 'id')
            .first()
        )

        if titular is None:
            Grupo = apps.get_model('invitaciones', 'Grupoinvitacion')
            grupo = Grupo.objects.filter(pk=grupo_id).first()
            if grupo is None:
                asignacion.delete()
                continue

            titular = Invitado.objects.create(
                grupo_id=grupo_id,
                nombre=grupo.nombre_grupo,
                tipo_persona='ADULTO',
                es_acompanante_extra=False,
                orden=0,
            )

        existing = (
            AsignacionMesa.objects
            .filter(invitado_id=titular.id)
            .exclude(pk=asignacion.pk)
            .order_by('id')
            .first()
        )

        if existing is not None:
            # An explicit per-person seat is more precise than the old group
            # assignment. Preserve it and remove the duplicate legacy record.
            if not existing.numero_asiento and asignacion.numero_asiento:
                existing.numero_asiento = asignacion.numero_asiento
            if not existing.notas and asignacion.notas:
                existing.notas = asignacion.notas
            existing.save(
                update_fields=['numero_asiento', 'notas']
            )
            asignacion.delete()
            continue

        asignacion.invitado_id = titular.id
        asignacion.save(update_fields=['invitado'])


class Migration(migrations.Migration):
    dependencies = [
        ('invitaciones', '0032_guest_domain_v2'),
        ('mesas', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(
            migrate_group_assignments,
            migrations.RunPython.noop,
        ),
        migrations.RemoveField(
            model_name='asignacionmesa',
            name='grupo_invitacion',
        ),
        migrations.AlterField(
            model_name='asignacionmesa',
            name='invitado',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='asignaciones_mesa',
                to='invitaciones.invitado',
            ),
        ),
        migrations.AddConstraint(
            model_name='asignacionmesa',
            constraint=models.UniqueConstraint(
                fields=('invitado',),
                name='mesas_un_invitado_una_mesa',
            ),
        ),
    ]
