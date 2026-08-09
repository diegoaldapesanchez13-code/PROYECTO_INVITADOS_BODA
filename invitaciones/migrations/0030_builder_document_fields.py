from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("invitaciones", "0029_sync_component_layout_state"),
    ]

    operations = [
        migrations.AddField(
            model_name="disenoinvitacion",
            name="documento_builder_borrador",
            field=models.JSONField(blank=True, default=dict),
        ),
        migrations.AddField(
            model_name="disenoinvitacion",
            name="documento_builder_publicado",
            field=models.JSONField(blank=True, default=dict),
        ),
        migrations.AddField(
            model_name="disenoinvitacion",
            name="builder_revision",
            field=models.PositiveIntegerField(default=0),
        ),
    ]
