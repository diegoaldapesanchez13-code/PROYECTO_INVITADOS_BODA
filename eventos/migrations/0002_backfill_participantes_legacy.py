from django.db import migrations


def backfill_participantes(apps, schema_editor):
    EventoBoda = apps.get_model('invitaciones', 'EventoBoda')
    ParticipanteEvento = apps.get_model('eventos', 'ParticipanteEvento')

    for evento in EventoBoda.objects.all().iterator():
        if evento.wedding_planner_id:
            ParticipanteEvento.objects.get_or_create(
                evento_id=evento.id,
                usuario_id=evento.wedding_planner_id,
                rol='PLANNER',
                defaults={
                    'activo': True,
                    'puede_ver_finanzas': True,
                    'puede_aprobar': True,
                    'puede_gestionar_invitados': True,
                    'puede_gestionar_servicios': True,
                },
            )
        for usuario_id in evento.clientes.values_list('id', flat=True):
            ParticipanteEvento.objects.get_or_create(
                evento_id=evento.id,
                usuario_id=usuario_id,
                rol='CLIENTE',
                defaults={
                    'activo': True,
                    'puede_aprobar': True,
                    'puede_gestionar_invitados': True,
                },
            )


class Migration(migrations.Migration):
    dependencies = [
        ('eventos', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(backfill_participantes, migrations.RunPython.noop),
    ]
