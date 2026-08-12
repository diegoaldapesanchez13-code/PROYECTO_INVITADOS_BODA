from django.conf import settings
from django.db import models


class PerfilAcceso(models.Model):
    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="perfil_acceso",
    )
    telefono = models.CharField(
        max_length=32,
        blank=True,
        null=True,
    )
    telefono_normalizado = models.CharField(
        max_length=24,
        blank=True,
        null=True,
        unique=True,
    )
    telefono_verificado = models.BooleanField(
        default=False,
    )
    fecha_actualizacion = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        verbose_name = "Perfil de acceso"
        verbose_name_plural = "Perfiles de acceso"

    def __str__(self):
        return f"Acceso {self.usuario.username}"
