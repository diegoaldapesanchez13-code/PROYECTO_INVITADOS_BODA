from django.db import migrations


ROLES_BASE = [
    'Superadministrador',
    'Wedding planner',
    'Cliente',
    'Proveedor',
]


def crear_roles(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    for nombre in ROLES_BASE:
        Group.objects.get_or_create(name=nombre)


def eliminar_roles(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    Group.objects.filter(name__in=ROLES_BASE).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('invitaciones', '0018_eventoboda_clientes_eventoboda_descripcion_and_more'),
    ]

    operations = [
        migrations.RunPython(crear_roles, eliminar_roles),
    ]
