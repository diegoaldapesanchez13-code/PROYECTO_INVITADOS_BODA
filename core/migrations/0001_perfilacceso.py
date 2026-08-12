from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(
            settings.AUTH_USER_MODEL
        ),
    ]

    operations = [
        migrations.CreateModel(
            name="PerfilAcceso",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "telefono",
                    models.CharField(
                        blank=True,
                        max_length=32,
                        null=True,
                    ),
                ),
                (
                    "telefono_normalizado",
                    models.CharField(
                        blank=True,
                        max_length=24,
                        null=True,
                        unique=True,
                    ),
                ),
                (
                    "telefono_verificado",
                    models.BooleanField(
                        default=False
                    ),
                ),
                (
                    "fecha_actualizacion",
                    models.DateTimeField(
                        auto_now=True
                    ),
                ),
                (
                    "usuario",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="perfil_acceso",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "Perfil de acceso",
                "verbose_name_plural": "Perfiles de acceso",
            },
        ),
    ]
