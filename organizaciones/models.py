from django.conf import settings
from django.db import models


class EmpresaSuscriptora(models.Model):
    ESTADOS = [
        ('ACTIVA', 'Activa'),
        ('SUSPENDIDA', 'Suspendida'),
        ('BLOQUEADA', 'Bloqueada'),
        ('INACTIVA', 'Inactiva'),
    ]

    PLANES = [
        ('BASICO', 'Basico'),
        ('PROFESIONAL', 'Profesional'),
        ('ENTERPRISE', 'Enterprise'),
    ]

    nombre_comercial = models.CharField(max_length=160)
    razon_social = models.CharField(max_length=180, blank=True, null=True)
    slug = models.SlugField(max_length=180, unique=True)
    rfc = models.CharField(max_length=20, blank=True)
    contacto_nombre = models.CharField(max_length=120, blank=True, null=True)
    contacto_email = models.EmailField(blank=True, null=True)
    contacto_telefono = models.CharField(max_length=30, blank=True, null=True)
    direccion = models.TextField(blank=True)
    logotipo = models.FileField(upload_to='empresas/logotipos/', blank=True, null=True)
    colores_marca = models.JSONField(default=dict, blank=True)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='ACTIVA')
    plan = models.CharField(max_length=20, choices=PLANES, default='PROFESIONAL')
    activo = models.BooleanField(default=True)
    max_eventos_activos = models.PositiveIntegerField(default=20)
    max_usuarios = models.PositiveIntegerField(default=10)
    fecha_inicio = models.DateField(blank=True, null=True)
    fecha_fin = models.DateField(blank=True, null=True)
    notas = models.TextField(blank=True, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['nombre_comercial']
        verbose_name = 'Empresa suscriptora'
        verbose_name_plural = 'Empresas suscriptoras'

    def __str__(self):
        return self.nombre_comercial


class SedeEvento(models.Model):
    TIPOS = [
        ('SALON', 'Salon'),
        ('JARDIN', 'Jardin'),
        ('TERRAZA', 'Terraza'),
        ('HACIENDA', 'Hacienda'),
        ('OTRO', 'Otro'),
    ]

    empresa = models.ForeignKey(
        EmpresaSuscriptora,
        on_delete=models.CASCADE,
        related_name='sedes',
    )
    nombre = models.CharField(max_length=140)
    tipo = models.CharField(max_length=20, choices=TIPOS, default='SALON')
    capacidad_minima = models.PositiveIntegerField(default=0)
    capacidad_maxima = models.PositiveIntegerField(default=0)
    precio_base = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    direccion = models.CharField(max_length=255, blank=True, null=True)
    descripcion = models.TextField(blank=True, null=True)
    activa = models.BooleanField(default=True)

    class Meta:
        ordering = ['empresa', 'nombre']
        unique_together = ('empresa', 'nombre')
        verbose_name = 'Sede del evento'
        verbose_name_plural = 'Sedes del evento'

    def __str__(self):
        return f'{self.nombre} - {self.empresa}'


class MembresiaEmpresa(models.Model):
    ROLES = [
        ('ADMIN_EMPRESA', 'Administrador de empresa'),
        ('WEDDING_PLANNER', 'Wedding planner'),
        ('VENTAS', 'Ventas'),
        ('CLIENTE', 'Cliente'),
        ('PROVEEDOR', 'Proveedor'),
    ]

    empresa = models.ForeignKey(
        EmpresaSuscriptora,
        on_delete=models.CASCADE,
        related_name='membresias',
    )
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='membresias_empresa',
    )
    rol = models.CharField(max_length=30, choices=ROLES)
    activo = models.BooleanField(default=True)
    puede_gestionar_catalogos = models.BooleanField(default=False)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['empresa', 'rol', 'usuario__username']
        unique_together = ('empresa', 'usuario', 'rol')
        verbose_name = 'Membresia de empresa'
        verbose_name_plural = 'Membresias de empresa'

    def __str__(self):
        return f'{self.usuario} - {self.empresa} ({self.get_rol_display()})'
