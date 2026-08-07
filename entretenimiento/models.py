from django.db import models


class EntretenimientoEvento(models.Model):
    TIPOS = [
        ('DJ', 'DJ'),
        ('BANDA', 'Banda'),
        ('MARIACHI', 'Mariachi'),
        ('GRUPO', 'Grupo musical'),
        ('SOLISTA', 'Solista'),
        ('MUSICA_AMBIENTAL', 'Musica ambiental'),
        ('ANIMACION', 'Animacion'),
        ('OTRO', 'Otro'),
    ]
    ESTADOS = [
        ('PROPUESTO', 'Propuesto'),
        ('COTIZADO', 'Cotizado'),
        ('APROBADO', 'Aprobado'),
        ('CONTRATADO', 'Contratado'),
        ('ANTICIPO_PAGADO', 'Anticipo pagado'),
        ('LIQUIDADO', 'Liquidado'),
        ('CANCELADO', 'Cancelado'),
        ('COMPLETADO', 'Completado'),
    ]

    evento = models.ForeignKey(
        'invitaciones.EventoBoda',
        on_delete=models.CASCADE,
        related_name='entretenimiento_evento',
    )
    tipo = models.CharField(max_length=30, choices=TIPOS, default='DJ')
    proveedor = models.ForeignKey(
        'proveedores.Proveedor',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='entretenimientos',
    )
    nombre_artista = models.CharField(max_length=140)
    hora_inicio = models.TimeField(blank=True, null=True)
    hora_fin = models.TimeField(blank=True, null=True)
    duracion = models.CharField(max_length=80, blank=True, null=True)
    costo = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    anticipo = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    requerimientos_tecnicos = models.TextField(blank=True, null=True)
    estado = models.CharField(max_length=30, choices=ESTADOS, default='PROPUESTO')
    notas = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['evento', 'hora_inicio', 'nombre_artista']
        verbose_name = 'Entretenimiento del evento'
        verbose_name_plural = 'Entretenimiento del evento'

    def __str__(self):
        return f'{self.get_tipo_display()} - {self.nombre_artista}'

    @property
    def saldo_pendiente(self):
        saldo = self.costo - self.anticipo
        return saldo if saldo > 0 else 0


class CancionEvento(models.Model):
    TIPOS_MOMENTO = [
        ('ENTRADA', 'Entrada'),
        ('CEREMONIA', 'Ceremonia'),
        ('PRIMER_BAILE', 'Primer baile'),
        ('PADRES', 'Baile con padres'),
        ('CENA', 'Cena'),
        ('RAMO', 'Lanzamiento de ramo'),
        ('PASTEL', 'Pastel'),
        ('FIESTA', 'Fiesta'),
        ('PROHIBIDA', 'Cancion prohibida'),
        ('OTRO', 'Otro'),
    ]

    evento = models.ForeignKey(
        'invitaciones.EventoBoda',
        on_delete=models.CASCADE,
        related_name='canciones_evento',
    )
    entretenimiento = models.ForeignKey(
        EntretenimientoEvento,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='canciones',
    )
    tipo_momento = models.CharField(max_length=30, choices=TIPOS_MOMENTO, default='FIESTA')
    nombre_cancion = models.CharField(max_length=160)
    artista = models.CharField(max_length=140, blank=True, null=True)
    enlace = models.URLField(blank=True, null=True)
    orden = models.PositiveIntegerField(default=0)
    notas = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['evento', 'orden', 'tipo_momento', 'nombre_cancion']
        verbose_name = 'Cancion del evento'
        verbose_name_plural = 'Canciones del evento'

    def __str__(self):
        return self.nombre_cancion

# Create your models here.
