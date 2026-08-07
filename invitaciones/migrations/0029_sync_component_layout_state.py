from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('invitaciones', '0028_componenteinvitacion'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.AddField(
                    model_name='componenteinvitacion',
                    name='layout_mode',
                    field=models.CharField(
                        choices=[
                            ('FLOW', 'Flujo'),
                            ('ABSOLUTE', 'Absoluto'),
                            ('LAYER', 'Capa permanente'),
                        ],
                        default='ABSOLUTE',
                        max_length=20,
                    ),
                ),
                migrations.AddField(
                    model_name='componenteinvitacion',
                    name='coordinate_space',
                    field=models.CharField(
                        choices=[
                            ('PAGE', 'Pagina'),
                            ('SECTION', 'Seccion'),
                            ('CONTAINER', 'Contenedor'),
                            ('COMPONENT', 'Componente'),
                        ],
                        default='SECTION',
                        max_length=20,
                    ),
                ),
                migrations.AddField(
                    model_name='componenteinvitacion',
                    name='parent_key',
                    field=models.CharField(
                        blank=True,
                        default='',
                        max_length=120,
                    ),
                ),
                migrations.AddField(
                    model_name='componenteinvitacion',
                    name='constraints',
                    field=models.JSONField(
                        blank=True,
                        default=dict,
                    ),
                ),
            ],
        ),
    ]