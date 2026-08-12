from django.db import migrations


FIELD_NAMES = (
    "layout_mode",
    "coordinate_space",
    "parent_key",
    "constraints",
)


def add_missing_component_layout_columns(apps, schema_editor):
    ComponenteInvitacion = apps.get_model(
        "invitaciones",
        "ComponenteInvitacion",
    )

    table_name = ComponenteInvitacion._meta.db_table

    with schema_editor.connection.cursor() as cursor:
        existing_columns = {
            column.name
            for column in schema_editor.connection.introspection.get_table_description(
                cursor,
                table_name,
            )
        }

    for field_name in FIELD_NAMES:
        if field_name in existing_columns:
            continue

        field = ComponenteInvitacion._meta.get_field(field_name)
        schema_editor.add_field(ComponenteInvitacion, field)
        existing_columns.add(field_name)


class Migration(migrations.Migration):

    dependencies = [
        ("invitaciones", "0032_guest_domain_v2"),
    ]

    operations = [
        migrations.RunPython(
            add_missing_component_layout_columns,
            migrations.RunPython.noop,
        ),
    ]