# Generated manually to consolidate RSVP data at group level.

from django.db import migrations, models


def migrar_respuestas_a_grupo(apps, schema_editor):
    GrupoInvitacion = apps.get_model('invitaciones', 'Grupoinvitacion')
    Invitado = apps.get_model('invitaciones', 'Invitado')

    for grupo in GrupoInvitacion.objects.all():
        invitados = list(Invitado.objects.filter(grupo_id=grupo.id))
        if not invitados:
            continue

        confirmados = [invitado for invitado in invitados if invitado.asistira is not None]
        asistentes = [invitado for invitado in invitados if invitado.asistira is True]
        comentarios = [
            invitado.comentario.strip()
            for invitado in invitados
            if invitado.comentario and invitado.comentario.strip()
        ]

        if asistentes:
            grupo.asistira = True
            grupo.cantidad_confirmada = min(len(asistentes), grupo.cantidad_maxima)
        elif confirmados:
            grupo.asistira = False
            grupo.cantidad_confirmada = 0
        else:
            grupo.asistira = None
            grupo.cantidad_confirmada = None

        grupo.confirmado = grupo.asistira is not None
        grupo.comentario = '\n'.join(comentarios) or None
        grupo.save(update_fields=[
            'asistira',
            'cantidad_confirmada',
            'confirmado',
            'comentario',
        ])


class Migration(migrations.Migration):

    dependencies = [
        ('invitaciones', '0005_grupoinvitacion_estado_envio_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='grupoinvitacion',
            name='asistira',
            field=models.BooleanField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='grupoinvitacion',
            name='cantidad_confirmada',
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='grupoinvitacion',
            name='comentario',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.RunPython(migrar_respuestas_a_grupo, migrations.RunPython.noop),
        migrations.DeleteModel(
            name='Invitado',
        ),
    ]
