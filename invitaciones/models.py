from django.db import models
import uuid

# Modelo que representa un grupo de invitados a una boda.
# Cada grupo tiene un UUID único para acceder a su invitación.
class Grupoinvitacion(models.Model):
    TIPO_INVITACION = [
        ('FAMILIAR', 'Familiar'),
        ('PERSONAL', 'Personal'),
    ]
    nombre_grupo= models.CharField(max_length=100)
    codigo = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    tipo = models.CharField(max_length=10, choices=TIPO_INVITACION)
    cantidad_maxima = models.IntegerField(default=1)
    confirmado = models.BooleanField(default=False)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    telefono_contacto = models.CharField(max_length=20, blank=True, null=True)
    estado_envio = models.CharField(
        max_length=30,
        choices=[
                ('PENDIENTE', 'Pendiente'),
                ('INVITACION_PREPARADA', 'Invitación preparada'),
                ('RECORDATORIO_PREPARADO', 'Recordatorio preparado'),
        ],
        default='PENDIENTE'
    )

    fecha_ultimo_envio = models.DateTimeField(blank=True, null=True)
    fecha_ultimo_recordatorio = models.DateTimeField(blank=True, null=True)
    def __str__(self):
        return self.nombre_grupo

# Modelo que representa a cada invitado dentro de un grupo.
class Invitado(models.Model):
    grupo = models.ForeignKey(Grupoinvitacion, on_delete=models.CASCADE, related_name='invitados')
    nombre = models.CharField(max_length=100)
    asistira = models.BooleanField(null=True, blank=True)
    comentario = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.nombre

# Modelo que contiene los datos generales del evento de boda.
class EventoBoda(models.Model):
    novio = models.CharField(max_length=100)
    novia = models.CharField(max_length=100)

    frase_portada = models.CharField(max_length=255)
    mensaje_general = models.TextField()

    fecha_misa = models.DateTimeField()
    lugar_misa = models.CharField(max_length=200)

    fecha_fiesta = models.DateTimeField()
    lugar_fiesta = models.CharField(max_length=200)

    dress_code = models.CharField(max_length=150, blank=True, null=True)

    link_mapa = models.URLField(blank=True, null=True)
    link_whatsapp = models.URLField(blank=True, null=True)

    imagen_portada = models.URLField(blank=True, null=True)

    def __str__(self):
        return f"Boda {self.novio} & {self.novia}"