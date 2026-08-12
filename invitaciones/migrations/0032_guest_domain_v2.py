from django.db import migrations, models


def forwards(apps, schema_editor):
    Grupo = apps.get_model('invitaciones', 'Grupoinvitacion')
    Invitado = apps.get_model('invitaciones', 'Invitado')

    for grupo in Grupo.objects.all().iterator():
        extras_autorizados = max(int(grupo.cantidad_extra_permitida or 0), 0)
        if extras_autorizados:
            grupo.permitir_acompanantes_extra = True
            grupo.save(update_fields=['permitir_acompanantes_extra'])

        existentes = list(Invitado.objects.filter(grupo_id=grupo.id).order_by('orden', 'id'))

        if grupo.tipo == 'PERSONAL':
            # Historical PERSONAL stored the principal person on the group itself.
            principal = Invitado.objects.create(
                grupo_id=grupo.id,
                nombre=grupo.nombre_grupo,
                tipo_persona='ADULTO',
                es_acompanante_extra=False,
                asistira=grupo.asistira,
                fecha_confirmacion=grupo.fecha_confirmacion,
                orden=0,
            )

            # Existing rows on PERSONAL historically represented named extras.
            for index, invitado in enumerate(existentes, 1):
                invitado.es_acompanante_extra = True
                invitado.orden = index
                invitado.save(update_fields=['es_acompanante_extra', 'orden'])

            extras = list(
                Invitado.objects.filter(
                    grupo_id=grupo.id,
                    es_acompanante_extra=True,
                ).order_by('orden', 'id')
            )

            while len(extras) < extras_autorizados:
                index = len(extras) + 1
                extras.append(
                    Invitado.objects.create(
                        grupo_id=grupo.id,
                        nombre=f'Acompañante {index}',
                        tipo_persona='ADULTO',
                        es_acompanante_extra=True,
                        orden=index,
                    )
                )

            if grupo.confirmado:
                total_confirmados = max(int(grupo.cantidad_confirmada or 0), 0)
                extras_confirmados = max(total_confirmados - (1 if grupo.asistira else 0), 0)
                adultos_confirmados = max(int(grupo.acompanantes_adultos or 0), 0)
                ninos_confirmados = max(int(grupo.acompanantes_ninos or 0), 0)

                for index, extra in enumerate(extras):
                    extra.asistira = bool(grupo.asistira and index < extras_confirmados)
                    if index < ninos_confirmados:
                        extra.tipo_persona = 'NINO'
                    elif index < ninos_confirmados + adultos_confirmados:
                        extra.tipo_persona = 'ADULTO'
                    extra.fecha_confirmacion = grupo.fecha_confirmacion
                    extra.save(update_fields=['asistira', 'tipo_persona', 'fecha_confirmacion'])

        else:
            # Existing FAMILY rows are named people and stay nominal.
            Invitado.objects.filter(grupo_id=grupo.id).update(es_acompanante_extra=False)
            extras_actuales = 0
            while extras_actuales < extras_autorizados:
                extras_actuales += 1
                Invitado.objects.create(
                    grupo_id=grupo.id,
                    nombre=f'Acompañante {extras_actuales}',
                    tipo_persona='ADULTO',
                    es_acompanante_extra=True,
                    orden=1000 + extras_actuales,
                )


def backwards(apps, schema_editor):
    Invitado = apps.get_model('invitaciones', 'Invitado')
    # Only delete anonymous placeholders introduced by this migration. Named
    # records and attendance history are intentionally preserved.
    Invitado.objects.filter(
        es_acompanante_extra=True,
        nombre__startswith='Acompañante ',
    ).delete()


class Migration(migrations.Migration):
    dependencies = [
        ('invitaciones', '0031_alter_assetinvitacion_tipo'),
    ]

    operations = [
        migrations.AddField(
            model_name='grupoinvitacion',
            name='permitir_acompanantes_extra',
            field=models.BooleanField(
                default=False,
                help_text='Solo el organizador habilita acompañantes adicionales sin nombre conocido.',
            ),
        ),
        migrations.AddField(
            model_name='invitado',
            name='es_acompanante_extra',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='invitado',
            name='menu_asignado',
            field=models.CharField(
                choices=[
                    ('SEGUN_TIPO', 'Según tipo de persona'),
                    ('ADULTO', 'Menú adulto'),
                    ('INFANTIL', 'Menú infantil'),
                ],
                default='SEGUN_TIPO',
                help_text='Decisión interna del organizador. El invitado no modifica este valor.',
                max_length=12,
            ),
        ),
        migrations.RunPython(forwards, backwards),
    ]
