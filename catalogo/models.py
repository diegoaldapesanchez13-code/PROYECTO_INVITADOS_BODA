from django.core.exceptions import ValidationError
from django.db import models

from invitaciones.models import validar_documento, validar_imagen

from .storage import private_catalogo_storage


class ServicioCatalogo(models.Model):
    CATEGORIAS = [
        ('BANQUETE', 'Banquete'),
        ('BEBIDAS', 'Bebidas'),
        ('DECORACION', 'Decoracion'),
        ('MOBILIARIO', 'Mobiliario'),
        ('MUSICA', 'Musica'),
        ('AUDIO_ILUMINACION', 'Audio e iluminacion'),
        ('FOTOGRAFIA_VIDEO', 'Fotografia y video'),
        ('PERSONAL', 'Personal'),
        ('LOGISTICA', 'Logistica'),
        ('INVITACIONES', 'Invitaciones'),
        ('OTRO', 'Otro'),
    ]
    UNIDADES = [
        ('EVENTO', 'Evento'),
        ('PERSONA', 'Persona'),
        ('ADULTO', 'Adulto'),
        ('NINO', 'Nino'),
        ('HORA', 'Hora'),
        ('UNIDAD', 'Unidad'),
        ('MESA', 'Mesa'),
        ('PAQUETE', 'Paquete'),
        ('OTRO', 'Otro'),
    ]

    empresa = models.ForeignKey(
        'organizaciones.EmpresaSuscriptora',
        on_delete=models.PROTECT,
        related_name='servicios_catalogo',
    )
    nombre = models.CharField(max_length=160)
    categoria = models.CharField(max_length=30, choices=CATEGORIAS, default='OTRO')
    descripcion = models.TextField(blank=True, null=True)
    unidad = models.CharField(max_length=20, choices=UNIDADES, default='EVENTO')
    activo = models.BooleanField(default=True)
    imagen_principal = models.FileField(
        storage=private_catalogo_storage,
        upload_to='catalogo/servicios/imagenes/',
        validators=[validar_imagen],
        blank=True,
        null=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['empresa', 'categoria', 'nombre']
        constraints = [
            models.UniqueConstraint(
                fields=['empresa', 'nombre'],
                name='catalogo_servicio_empresa_nombre_unico',
            ),
        ]
        indexes = [
            models.Index(fields=['empresa', 'activo'], name='cat_serv_emp_act_idx'),
            models.Index(fields=['empresa', 'categoria'], name='cat_serv_emp_cat_idx'),
        ]
        verbose_name = 'Servicio de catalogo'
        verbose_name_plural = 'Servicios de catalogo'

    def __str__(self):
        return f'{self.nombre} - {self.empresa}'

    def clean(self):
        super().clean()
        if not self.empresa_id:
            raise ValidationError({'empresa': 'El servicio debe pertenecer a una empresa.'})
        nombre = (self.nombre or '').strip()
        if not nombre:
            raise ValidationError({'nombre': 'El nombre del servicio es obligatorio.'})
        self.nombre = nombre
        duplicado = ServicioCatalogo.objects.filter(
            empresa_id=self.empresa_id,
            nombre__iexact=nombre,
        )
        if self.pk:
            duplicado = duplicado.exclude(pk=self.pk)
        if duplicado.exists():
            raise ValidationError({'nombre': 'Ya existe un servicio con este nombre en la empresa.'})

    def save(self, *args, **kwargs):
        if self.nombre:
            self.nombre = self.nombre.strip()
        super().save(*args, **kwargs)


class ServicioCatalogoArchivo(models.Model):
    TIPOS = [
        ('IMAGEN', 'Imagen'),
        ('PDF', 'PDF'),
    ]

    servicio = models.ForeignKey(
        ServicioCatalogo,
        on_delete=models.CASCADE,
        related_name='archivos',
    )
    tipo = models.CharField(max_length=10, choices=TIPOS)
    archivo = models.FileField(storage=private_catalogo_storage, upload_to='catalogo/servicios/archivos/')
    titulo = models.CharField(max_length=140, blank=True, null=True)
    orden = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['servicio', 'orden', 'id']
        indexes = [
            models.Index(fields=['servicio', 'tipo'], name='cat_arch_srv_tipo_idx'),
        ]
        verbose_name = 'Archivo de servicio de catalogo'
        verbose_name_plural = 'Archivos de servicios de catalogo'

    def __str__(self):
        return self.titulo or f'{self.get_tipo_display()} - {self.servicio}'

    def clean(self):
        super().clean()
        if self.tipo == 'IMAGEN':
            validar_imagen(self.archivo)
        elif self.tipo == 'PDF':
            validar_documento(self.archivo)
            nombre = getattr(self.archivo, 'name', '') or ''
            if not nombre.lower().endswith('.pdf'):
                raise ValidationError({'archivo': 'PDF: formato no permitido. Usa: pdf.'})


class ProveedorServicioCatalogo(models.Model):
    proveedor = models.ForeignKey(
        'proveedores.Proveedor',
        on_delete=models.PROTECT,
        related_name='servicios_catalogo_k9',
    )
    servicio_catalogo = models.ForeignKey(
        ServicioCatalogo,
        on_delete=models.PROTECT,
        related_name='proveedores_servicio_catalogo',
    )
    activo = models.BooleanField(default=True)
    notas = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['proveedor', 'servicio_catalogo__nombre']
        constraints = [
            models.UniqueConstraint(
                fields=['proveedor', 'servicio_catalogo'],
                name='cat_prov_servicio_catalogo_unico',
            ),
        ]
        indexes = [
            models.Index(fields=['proveedor', 'activo'], name='cat_prov_srv_prov_act_idx'),
            models.Index(fields=['servicio_catalogo', 'activo'], name='cat_prov_srv_cat_act_idx'),
        ]
        verbose_name = 'Servicio ofrecido por proveedor'
        verbose_name_plural = 'Servicios ofrecidos por proveedor'

    def __str__(self):
        return f'{self.proveedor} ofrece {self.servicio_catalogo}'

    @property
    def empresa(self):
        return self.servicio_catalogo.empresa if self.servicio_catalogo_id else None

    def clean(self):
        super().clean()
        if not self.proveedor_id:
            raise ValidationError({'proveedor': 'La relacion debe tener proveedor.'})
        if not self.servicio_catalogo_id:
            raise ValidationError({'servicio_catalogo': 'La relacion debe tener servicio de catalogo.'})
        if not self.proveedor.empresa_id:
            raise ValidationError({'proveedor': 'El proveedor debe pertenecer a una empresa para usar catalogo K9.'})
        if self.proveedor.empresa_id != self.servicio_catalogo.empresa_id:
            raise ValidationError({
                'servicio_catalogo': 'El servicio debe pertenecer a la misma empresa del proveedor.'
            })

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
