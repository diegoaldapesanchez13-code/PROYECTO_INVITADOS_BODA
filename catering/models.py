from django.db import models


class CategoriaAlimento(models.Model):
    nombre = models.CharField(max_length=100, unique=True)

    class Meta:
        ordering = ['nombre']
        verbose_name = 'Categoria de alimento'
        verbose_name_plural = 'Categorias de alimentos'

    def __str__(self):
        return self.nombre


class Alimento(models.Model):
    categoria = models.ForeignKey(
        CategoriaAlimento,
        on_delete=models.PROTECT,
        related_name='alimentos',
    )
    nombre = models.CharField(max_length=120)
    descripcion = models.TextField(blank=True, null=True)
    vegetariano = models.BooleanField(default=False)
    vegano = models.BooleanField(default=False)
    sin_gluten = models.BooleanField(default=False)
    contiene_alergenos = models.BooleanField(default=False)
    activo = models.BooleanField(default=True)

    class Meta:
        ordering = ['categoria__nombre', 'nombre']
        verbose_name = 'Alimento'
        verbose_name_plural = 'Alimentos'

    def __str__(self):
        return self.nombre


class PaqueteBuffet(models.Model):
    proveedor = models.ForeignKey(
        'proveedores.Proveedor',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='paquetes_buffet',
    )
    nombre = models.CharField(max_length=140)
    descripcion = models.TextField(blank=True, null=True)
    personas_incluidas = models.PositiveIntegerField(default=0)
    precio_base = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    precio_por_persona_extra = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    precio_por_nino = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    activo = models.BooleanField(default=True)

    class Meta:
        ordering = ['nombre']
        verbose_name = 'Paquete de buffet'
        verbose_name_plural = 'Paquetes de buffet'

    def __str__(self):
        return self.nombre


class PaqueteBuffetAlimento(models.Model):
    paquete = models.ForeignKey(
        PaqueteBuffet,
        on_delete=models.CASCADE,
        related_name='alimentos_incluidos',
    )
    alimento = models.ForeignKey(
        Alimento,
        on_delete=models.PROTECT,
        related_name='paquetes_buffet',
    )
    cantidad_incluida = models.CharField(max_length=120, blank=True, null=True)

    class Meta:
        unique_together = ('paquete', 'alimento')
        ordering = ['paquete', 'alimento__categoria__nombre', 'alimento__nombre']
        verbose_name = 'Alimento incluido en buffet'
        verbose_name_plural = 'Alimentos incluidos en buffet'

    def __str__(self):
        return f'{self.alimento} - {self.paquete}'


class CateringEvento(models.Model):
    evento = models.ForeignKey(
        'invitaciones.EventoBoda',
        on_delete=models.CASCADE,
        related_name='catering_evento',
    )
    proveedor = models.ForeignKey(
        'proveedores.Proveedor',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='catering_eventos',
    )
    paquete_buffet = models.ForeignKey(
        PaqueteBuffet,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='eventos',
    )
    alimentos_seleccionados = models.ManyToManyField(
        Alimento,
        blank=True,
        related_name='eventos_catering',
    )
    cantidad_adultos = models.PositiveIntegerField(default=0)
    cantidad_ninos = models.PositiveIntegerField(default=0)
    cantidad_proveedores = models.PositiveIntegerField(default=0)
    precio_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    fecha_degustacion = models.DateField(blank=True, null=True)
    hora_servicio = models.TimeField(blank=True, null=True)
    horario_montaje = models.TimeField(blank=True, null=True)
    duracion_servicio = models.CharField(max_length=80, blank=True, null=True)
    observaciones = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['evento', 'hora_servicio']
        verbose_name = 'Catering del evento'
        verbose_name_plural = 'Catering de eventos'

    def __str__(self):
        return f'Catering - {self.evento}'

    @property
    def total_personas(self):
        return self.cantidad_adultos + self.cantidad_ninos + self.cantidad_proveedores

# Create your models here.
