from django.conf import settings
from django.db import models
from invitaciones.models import validar_documento


class Proveedor(models.Model):
    TIPOS = [
        ('SALON', 'Salon'),
        ('JARDIN', 'Jardin'),
        ('BANQUETE', 'Banquete'),
        ('BUFFET', 'Buffet'),
        ('FOTOGRAFIA', 'Fotografia'),
        ('VIDEO', 'Video'),
        ('BANDA', 'Banda'),
        ('DJ', 'DJ'),
        ('MUSICA_VIVO', 'Musica en vivo'),
        ('DECORACION', 'Decoracion'),
        ('FLORERIA', 'Floreria'),
        ('MANTELERIA', 'Manteleria'),
        ('MESEROS', 'Meseros'),
        ('BARRA', 'Barra de bebidas'),
        ('PASTEL', 'Pastel'),
        ('TRANSPORTE', 'Transporte'),
        ('MAQUILLAJE', 'Maquillaje'),
        ('PEINADO', 'Peinado'),
        ('VESTUARIO', 'Vestuario'),
        ('SEGURIDAD', 'Seguridad'),
        ('ILUMINACION', 'Iluminacion'),
        ('AUDIO', 'Audio'),
        ('MOBILIARIO', 'Renta de mobiliario'),
        ('INVITACIONES', 'Invitaciones'),
        ('RECUERDOS', 'Recuerdos'),
        ('OTROS', 'Otros'),
    ]

    empresa = models.ForeignKey(
        'organizaciones.EmpresaSuscriptora',
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        related_name='proveedores',
    )
    nombre_comercial = models.CharField(max_length=160)
    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='perfil_proveedor',
    )
    razon_social = models.CharField(max_length=180, blank=True, null=True)
    tipo_proveedor = models.CharField(max_length=30, choices=TIPOS, default='OTROS')
    nombre_contacto = models.CharField(max_length=120, blank=True, null=True)
    telefono = models.CharField(max_length=30, blank=True, null=True)
    correo = models.EmailField(blank=True, null=True)
    direccion = models.CharField(max_length=255, blank=True, null=True)
    sitio_web = models.URLField(blank=True, null=True)
    redes_sociales = models.TextField(blank=True, null=True)
    descripcion = models.TextField(blank=True, null=True)
    contacto_operativo = models.CharField(max_length=160, blank=True, null=True)
    telefono_operativo = models.CharField(max_length=30, blank=True, null=True)
    correo_operativo = models.EmailField(blank=True, null=True)
    visible_para_wedding_planners = models.BooleanField(default=True)
    rfc = models.CharField(max_length=20, blank=True, null=True)
    datos_bancarios = models.TextField(blank=True, null=True)
    notas_privadas = models.TextField(blank=True, null=True)
    calificacion = models.DecimalField(max_digits=3, decimal_places=2, default=0)
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['nombre_comercial']
        verbose_name = 'Proveedor'
        verbose_name_plural = 'Proveedores'

    def __str__(self):
        return self.nombre_comercial

    @property
    def contacto_visible(self):
        return self.contacto_operativo or self.nombre_contacto

    @property
    def telefono_visible(self):
        return self.telefono_operativo or self.telefono

    @property
    def correo_visible(self):
        return self.correo_operativo or self.correo


class EtiquetaProveedor(models.Model):
    empresa = models.ForeignKey(
        'organizaciones.EmpresaSuscriptora',
        on_delete=models.CASCADE,
        related_name='etiquetas_proveedor',
    )
    nombre = models.CharField(max_length=80)
    activa = models.BooleanField(default=True)

    class Meta:
        ordering = ['empresa', 'nombre']
        constraints = [
            models.UniqueConstraint(
                fields=['empresa', 'nombre'],
                name='proveedores_etiqueta_empresa_nombre_unico',
            ),
        ]

    def __str__(self):
        return self.nombre


class ServicioCatalogoProveedor(models.Model):
    empresa = models.ForeignKey(
        'organizaciones.EmpresaSuscriptora',
        on_delete=models.CASCADE,
        related_name='servicios_catalogo_proveedor',
    )
    proveedor = models.ForeignKey(
        Proveedor,
        on_delete=models.CASCADE,
        related_name='servicios_catalogo',
    )
    nombre = models.CharField(max_length=160)
    descripcion = models.TextField(blank=True, null=True)
    categoria = models.CharField(max_length=50, blank=True, null=True)
    costo_referencia = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    precio_referencia_cliente = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    activo = models.BooleanField(default=True)
    etiquetas = models.ManyToManyField(EtiquetaProveedor, blank=True, related_name='servicios_catalogo')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['proveedor', 'nombre']
        constraints = [
            models.UniqueConstraint(
                fields=['proveedor', 'nombre'],
                name='proveedores_servicio_catalogo_proveedor_nombre_unico',
            ),
        ]
        indexes = [
            models.Index(fields=['empresa', 'activo'], name='prov_cat_emp_act_idx'),
            models.Index(fields=['proveedor', 'activo'], name='prov_cat_prov_act_idx'),
        ]

    def __str__(self):
        return f'{self.nombre} - {self.proveedor}'

    def clean(self):
        super().clean()
        if self.proveedor_id and self.empresa_id and self.proveedor.empresa_id not in {None, self.empresa_id}:
            from django.core.exceptions import ValidationError
            raise ValidationError({'proveedor': 'El proveedor debe pertenecer a la misma empresa del catalogo.'})


class ServicioEvento(models.Model):
    ORIGENES = [
        ('MANUAL', 'Manual'),
        ('CATALOGO', 'Catalogo'),
        ('PAQUETE', 'Paquete'),
    ]
    MODALIDADES = [
        ('INCLUIDO', 'Incluido en paquete'),
        ('ADICIONAL', 'Servicio adicional'),
        ('UPGRADE', 'Upgrade / diferencia'),
    ]
    ESTADOS_COMERCIALES = [
        ('BORRADOR', 'Borrador'),
        ('COTIZANDO', 'Cotizando'),
        ('PROPUESTO', 'Propuesto al cliente'),
        ('APROBADO', 'Aprobado'),
        ('CONTRATADO', 'Contratado'),
        ('CANCELADO', 'Cancelado'),
    ]
    ESTADOS_OPERATIVOS = [
        ('PENDIENTE', 'Pendiente'),
        ('EN_DEFINICION', 'En definicion'),
        ('PROGRAMADO', 'Programado'),
        ('LISTO', 'Listo'),
        ('EN_EJECUCION', 'En ejecucion'),
        ('COMPLETADO', 'Completado'),
        ('INCIDENCIA', 'Incidencia'),
        ('CANCELADO', 'Cancelado'),
    ]
    ESTADOS = [
        ('SOLICITADO', 'Solicitado'),
        ('COTIZADO', 'Cotizado'),
        ('PENDIENTE_APROBACION', 'Pendiente de aprobacion'),
        ('APROBADO', 'Aprobado'),
        ('CONTRATADO', 'Contratado'),
        ('ANTICIPO_PAGADO', 'Anticipo pagado'),
        ('LIQUIDADO', 'Liquidado'),
        ('CANCELADO', 'Cancelado'),
        ('SERVICIO_COMPLETADO', 'Servicio completado'),
    ]

    evento = models.ForeignKey(
        'invitaciones.EventoBoda',
        on_delete=models.CASCADE,
        related_name='servicios_contratados',
    )
    proveedor = models.ForeignKey(
        Proveedor,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='servicios_evento',
    )
    servicio_catalogo = models.ForeignKey(
        ServicioCatalogoProveedor,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='instancias_evento',
    )
    paquete_evento = models.ForeignKey(
        'paquetes.PaqueteEvento',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='servicios_materializados',
    )
    servicio_paquete_origen = models.ForeignKey(
        'paquetes.ServicioPaquete',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='servicios_evento_materializados',
    )
    origen = models.CharField(max_length=15, choices=ORIGENES, default='MANUAL')
    modalidad = models.CharField(max_length=15, choices=MODALIDADES, default='ADICIONAL')
    categoria = models.CharField(max_length=50, blank=True, null=True)
    proveedor_nombre_snapshot = models.CharField(max_length=160, blank=True, null=True)
    catalogo_nombre_snapshot = models.CharField(max_length=160, blank=True, null=True)
    catalogo_descripcion_snapshot = models.TextField(blank=True, null=True)
    paquete_nombre_snapshot = models.CharField(max_length=160, blank=True, null=True)
    paquete_servicio_snapshot = models.JSONField(default=dict, blank=True)
    cantidad_paquete = models.PositiveIntegerField(default=1)
    nombre_servicio = models.CharField(max_length=160)
    descripcion = models.TextField(blank=True, null=True)
    fecha_servicio = models.DateField(blank=True, null=True)
    hora_inicio = models.TimeField(blank=True, null=True)
    hora_fin = models.TimeField(blank=True, null=True)
    lugar = models.CharField(max_length=180, blank=True, null=True)
    # Compatibilidad legacy: costo_total/precio_cliente/ajuste_cliente siguen
    # existiendo mientras las vistas antiguas migran al dominio financiero nuevo.
    costo_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    costo_proveedor = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    precio_cliente = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    ajuste_cliente = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    # K.8.3.1: semantica financiera explicita.
    # valor_contratado = valor comercial atribuible al componente dentro del
    # acuerdo/paquete; no implica un cobro extra.
    # cargo_adicional_cliente = importe que se suma al contrato base.
    valor_contratado = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    cargo_adicional_cliente = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    anticipo = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    fecha_limite_pago = models.DateField(blank=True, null=True)
    estado = models.CharField(max_length=30, choices=ESTADOS, default='SOLICITADO')
    estado_comercial = models.CharField(
        max_length=20, choices=ESTADOS_COMERCIALES, default='BORRADOR'
    )
    estado_operativo = models.CharField(
        max_length=20, choices=ESTADOS_OPERATIVOS, default='PENDIENTE'
    )
    ESTADOS_PROVEEDOR = [
        ('PENDIENTE', 'Pendiente de confirmar'),
        ('CONFIRMADO', 'Confirmado por proveedor'),
        ('INCIDENCIA', 'Requiere atencion'),
        ('COMPLETADO', 'Servicio realizado'),
    ]
    estado_proveedor = models.CharField(
        max_length=20,
        choices=ESTADOS_PROVEEDOR,
        default='PENDIENTE',
    )
    comentario_proveedor = models.TextField(blank=True, null=True)
    fecha_respuesta_proveedor = models.DateTimeField(blank=True, null=True)
    contrato = models.FileField(upload_to='proveedores/contratos/', validators=[validar_documento], blank=True, null=True)
    cotizacion = models.FileField(upload_to='proveedores/cotizaciones/', validators=[validar_documento], blank=True, null=True)
    comprobante_pago = models.FileField(upload_to='proveedores/comprobantes/', validators=[validar_documento], blank=True, null=True)
    notas = models.TextField(blank=True, null=True)
    notas_internas = models.TextField(blank=True, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['evento', 'fecha_servicio', 'hora_inicio', 'nombre_servicio']
        indexes = [
            models.Index(fields=['evento', 'estado_operativo'], name='prov_srv_evt_oper_idx'),
            models.Index(fields=['evento', 'estado_comercial'], name='prov_srv_evt_com_idx'),
            models.Index(fields=['evento', 'proveedor'], name='prov_srv_evt_prov_idx'),
            models.Index(fields=['paquete_evento', 'origen'], name='prov_srv_pkg_orig_idx'),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['paquete_evento', 'servicio_paquete_origen'],
                name='prov_srv_pkg_item_unico',
            ),
        ]
        verbose_name = 'Servicio contratado'
        verbose_name_plural = 'Servicios contratados'

    def clean(self):
        super().clean()
        from django.core.exceptions import ValidationError
        if self.evento_id and self.proveedor_id:
            evento_empresa_id = self.evento.empresa_id
            proveedor_empresa_id = self.proveedor.empresa_id
            if evento_empresa_id and proveedor_empresa_id and evento_empresa_id != proveedor_empresa_id:
                raise ValidationError({'proveedor': 'El proveedor debe pertenecer a la misma empresa del evento.'})
        if self.servicio_catalogo_id:
            if self.proveedor_id and self.servicio_catalogo.proveedor_id != self.proveedor_id:
                raise ValidationError({'servicio_catalogo': 'El servicio de catalogo no pertenece al proveedor seleccionado.'})
            if self.evento_id and self.evento.empresa_id and self.servicio_catalogo.empresa_id != self.evento.empresa_id:
                raise ValidationError({'servicio_catalogo': 'El servicio de catalogo debe pertenecer a la empresa del evento.'})
        if self.valor_contratado < 0:
            raise ValidationError({'valor_contratado': 'El valor contratado no puede ser negativo.'})
        if self.cargo_adicional_cliente < 0:
            raise ValidationError({'cargo_adicional_cliente': 'El cargo adicional al cliente no puede ser negativo.'})
        if self.modalidad == 'INCLUIDO' and self.cargo_adicional_cliente != 0:
            raise ValidationError({
                'cargo_adicional_cliente':
                    'Un servicio incluido en paquete no debe generar cargo adicional.'
            })

    def __str__(self):
        return f'{self.nombre_servicio} - {self.evento}'

    def capturar_snapshot_catalogo(self):
        if self.proveedor_id and not self.proveedor_nombre_snapshot:
            self.proveedor_nombre_snapshot = self.proveedor.nombre_comercial
        if self.servicio_catalogo_id:
            self.catalogo_nombre_snapshot = self.servicio_catalogo.nombre
            self.catalogo_descripcion_snapshot = self.servicio_catalogo.descripcion
            if not self.categoria:
                self.categoria = self.servicio_catalogo.categoria
        return self

    @property
    def importe_adicional_cliente(self):
        """Fuente de verdad nueva para extras/upgrades del contrato."""
        return self.cargo_adicional_cliente

    @property
    def incluido_en_paquete(self):
        return self.modalidad == 'INCLUIDO'

    @property
    def saldo_pendiente(self):
        saldo = self.costo_total - self.anticipo
        return saldo if saldo > 0 else 0


class PersonalEvento(models.Model):
    TIPOS = [
        ('CAPITAN', 'Capitan de meseros'),
        ('MESERO', 'Mesero'),
        ('BARTENDER', 'Bartender'),
        ('COCINA', 'Personal de cocina'),
        ('LIMPIEZA', 'Limpieza'),
        ('SEGURIDAD', 'Seguridad'),
        ('MONTAJE', 'Montaje'),
        ('COORDINACION', 'Coordinacion'),
        ('OTRO', 'Otro'),
    ]
    ESTADOS = [
        ('REQUERIDO', 'Requerido'),
        ('CONFIRMADO', 'Confirmado'),
        ('EN_SITIO', 'En sitio'),
        ('FINALIZADO', 'Finalizado'),
        ('CANCELADO', 'Cancelado'),
    ]

    evento = models.ForeignKey(
        'invitaciones.EventoBoda',
        on_delete=models.CASCADE,
        related_name='personal_evento',
    )
    proveedor = models.ForeignKey(
        Proveedor,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='personal_asignado',
    )
    nombre = models.CharField(max_length=120)
    tipo_personal = models.CharField(max_length=20, choices=TIPOS, default='MESERO')
    telefono = models.CharField(max_length=30, blank=True, null=True)
    hora_entrada = models.TimeField(blank=True, null=True)
    hora_salida = models.TimeField(blank=True, null=True)
    area_asignada = models.CharField(max_length=120, blank=True, null=True)
    mesas_asignadas = models.CharField(max_length=180, blank=True, null=True)
    costo = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    uniforme = models.CharField(max_length=180, blank=True, null=True)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='REQUERIDO')
    notas = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['evento', 'tipo_personal', 'nombre']
        verbose_name = 'Personal del evento'
        verbose_name_plural = 'Personal del evento'

    def __str__(self):
        return f'{self.nombre} ({self.get_tipo_personal_display()})'

# Create your models here.
