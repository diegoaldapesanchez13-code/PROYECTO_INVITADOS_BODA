from django.core.exceptions import ValidationError
from django.db import models


class Mesa(models.Model):
    TIPOS = [
        ('REDONDA', 'Redonda'),
        ('RECTANGULAR', 'Rectangular'),
        ('PRINCIPAL', 'Mesa principal'),
        ('PROTAGONISTAS', 'Mesa de protagonistas'),
        ('PROVEEDORES', 'Mesa de proveedores'),
        ('OTRA', 'Otra'),
    ]

    evento = models.ForeignKey(
        'invitaciones.EventoBoda',
        on_delete=models.CASCADE,
        related_name='mesas_evento',
    )
    nombre = models.CharField(max_length=100)
    numero = models.PositiveIntegerField(blank=True, null=True)
    tipo = models.CharField(max_length=20, choices=TIPOS, default='REDONDA')
    capacidad = models.PositiveIntegerField(default=10)
    zona = models.CharField(max_length=100, blank=True, null=True)
    posicion_x = models.PositiveIntegerField(default=0)
    posicion_y = models.PositiveIntegerField(default=0)
    ancho = models.PositiveIntegerField(default=140)
    alto = models.PositiveIntegerField(default=140)
    rotacion = models.PositiveIntegerField(default=0)
    mesero = models.ForeignKey(
        'proveedores.PersonalEvento',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='mesas_como_mesero',
    )
    notas = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['evento', 'numero', 'nombre']
        unique_together = ('evento', 'nombre')
        verbose_name = 'Mesa'
        verbose_name_plural = 'Mesas'

    def __str__(self):
        return self.nombre

    @property
    def lugares_ocupados(self):
        return self.asignaciones.count()

    @property
    def lugares_disponibles(self):
        disponibles = self.capacidad - self.lugares_ocupados
        return disponibles if disponibles > 0 else 0

    @property
    def excedida(self):
        return self.lugares_ocupados > self.capacidad


class AsignacionMesa(models.Model):
    mesa = models.ForeignKey(
        Mesa,
        on_delete=models.CASCADE,
        related_name='asignaciones',
    )
    invitado = models.ForeignKey(
        'invitaciones.Invitado',
        on_delete=models.CASCADE,
        related_name='asignaciones_mesa',
    )
    numero_asiento = models.PositiveIntegerField(blank=True, null=True)
    notas = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['mesa', 'numero_asiento', 'id']
        verbose_name = 'Asignacion de mesa'
        verbose_name_plural = 'Asignaciones de mesa'
        constraints = [
            models.UniqueConstraint(
                fields=['invitado'],
                name='mesas_un_invitado_una_mesa',
            ),
        ]

    def __str__(self):
        return f'{self.invitado} en {self.mesa}'

    def clean(self):
        if not self.invitado_id:
            raise ValidationError('Selecciona una persona.')

        if (
            self.invitado_id
            and self.mesa_id
            and self.invitado.grupo.evento_id != self.mesa.evento_id
        ):
            raise ValidationError('La persona pertenece a otro evento.')

        asignaciones = (
            self.mesa.asignaciones.exclude(pk=self.pk)
            if self.mesa_id
            else AsignacionMesa.objects.none()
        )
        if self.mesa_id and asignaciones.count() >= self.mesa.capacidad:
            raise ValidationError('La mesa ya alcanzo su capacidad.')

        if (
            self.invitado_id
            and AsignacionMesa.objects
            .exclude(pk=self.pk)
            .filter(invitado_id=self.invitado_id)
            .exists()
        ):
            raise ValidationError('Esta persona ya tiene mesa asignada.')

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
