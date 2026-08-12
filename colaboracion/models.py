from django.conf import settings
from django.db import models
from django.utils import timezone

from invitaciones.models import validar_documento


class ExpedienteServicio(models.Model):
    CATEGORIAS = [
        ("DECORACION", "Decoracion"),
        ("MENU", "Menu / banquete"),
        ("MUSICA", "Musica / entretenimiento"),
        ("FOTOGRAFIA", "Fotografia / video"),
        ("MOBILIARIO", "Mobiliario / montaje"),
        ("TRANSPORTE", "Transporte"),
        ("INVITACION", "Invitacion / papeleria"),
        ("OTRO", "Otro"),
    ]

    ESTADOS = [
        ("NUEVO", "Nueva solicitud"),
        ("EN_ANALISIS", "En analisis"),
        ("CONSULTA_PROVEEDOR", "Consultando proveedor"),
        ("COTIZACION_RECIBIDA", "Cotizacion recibida"),
        ("COTIZACION_ACEPTADA", "Cotizacion aceptada por planner"),
        ("PROPUESTA_CLIENTE", "Propuesta enviada al cliente"),
        ("CAMBIOS_CLIENTE", "Cliente solicito cambios"),
        ("APROBADO_CLIENTE", "Aprobado por cliente"),
        ("CONTRATADO", "Contratado"),
        ("CERRADO", "Cerrado"),
        ("CANCELADO", "Cancelado"),
    ]

    evento = models.ForeignKey(
        "invitaciones.EventoBoda",
        on_delete=models.CASCADE,
        related_name="expedientes_servicio",
    )
    titulo = models.CharField(max_length=180)
    descripcion = models.TextField(blank=True, null=True)
    categoria = models.CharField(
        max_length=30,
        choices=CATEGORIAS,
        default="OTRO",
    )
    estado = models.CharField(
        max_length=30,
        choices=ESTADOS,
        default="NUEVO",
    )
    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="expedientes_servicio_creados",
    )
    cliente_solicitante = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="solicitudes_servicio_cliente",
    )
    proveedor = models.ForeignKey(
        "proveedores.Proveedor",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="expedientes_colaboracion",
    )
    servicio_evento = models.OneToOneField(
        "proveedores.ServicioEvento",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="expediente_colaboracion",
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-fecha_actualizacion", "-id"]
        verbose_name = "Expediente colaborativo de servicio"
        verbose_name_plural = "Expedientes colaborativos de servicio"

    def __str__(self):
        return f"{self.titulo} - {self.evento}"


class MensajeExpediente(models.Model):
    CANALES = [
        ("CLIENTE_PLANNER", "Cliente / Planner"),
        ("PLANNER_PROVEEDOR", "Planner / Proveedor"),
    ]
    TIPOS = [
        ("MENSAJE", "Mensaje"),
        ("SISTEMA", "Sistema"),
    ]

    expediente = models.ForeignKey(
        ExpedienteServicio,
        on_delete=models.CASCADE,
        related_name="mensajes",
    )
    canal = models.CharField(max_length=30, choices=CANALES)
    autor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="mensajes_colaboracion",
    )
    tipo = models.CharField(
        max_length=15,
        choices=TIPOS,
        default="MENSAJE",
    )
    mensaje = models.TextField(blank=True)
    archivo = models.FileField(
        upload_to="colaboracion/mensajes/",
        validators=[validar_documento],
        blank=True,
        null=True,
    )
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["fecha", "id"]
        verbose_name = "Mensaje de expediente"
        verbose_name_plural = "Mensajes de expediente"

    def __str__(self):
        return f"{self.get_canal_display()} - {self.expediente}"


class CotizacionProveedor(models.Model):
    ESTADOS = [
        ("ENVIADA", "Enviada"),
        ("CAMBIOS_SOLICITADOS", "Cambios solicitados"),
        ("ACEPTADA", "Aceptada por planner"),
        ("RECHAZADA", "Rechazada"),
    ]

    expediente = models.ForeignKey(
        ExpedienteServicio,
        on_delete=models.CASCADE,
        related_name="cotizaciones_proveedor",
    )
    proveedor = models.ForeignKey(
        "proveedores.Proveedor",
        on_delete=models.PROTECT,
        related_name="cotizaciones_colaboracion",
    )
    version = models.PositiveIntegerField()
    costo_proveedor = models.DecimalField(
        max_digits=12,
        decimal_places=2,
    )
    descripcion = models.TextField(blank=True, null=True)
    vigencia = models.DateField(blank=True, null=True)
    archivo = models.FileField(
        upload_to="colaboracion/cotizaciones/",
        validators=[validar_documento],
        blank=True,
        null=True,
    )
    estado = models.CharField(
        max_length=25,
        choices=ESTADOS,
        default="ENVIADA",
    )
    respuesta_planner = models.TextField(blank=True, null=True)
    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="cotizaciones_proveedor_creadas",
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-version", "-id"]
        constraints = [
            models.UniqueConstraint(
                fields=["expediente", "version"],
                name="colaboracion_cotizacion_version_unica",
            ),
        ]

    def __str__(self):
        return f"{self.expediente} v{self.version}"


class PropuestaCliente(models.Model):
    MODALIDADES = [
        ("ADICIONAL", "Servicio adicional"),
        ("INCLUIDO_PAQUETE", "Incluido en paquete"),
    ]
    ESTADOS = [
        ("BORRADOR", "Borrador"),
        ("ENVIADA", "Enviada al cliente"),
        ("CAMBIOS_SOLICITADOS", "Cambios solicitados"),
        ("APROBADA", "Aprobada"),
        ("RECHAZADA", "Rechazada"),
        ("REEMPLAZADA", "Reemplazada por nueva version"),
    ]

    expediente = models.ForeignKey(
        ExpedienteServicio,
        on_delete=models.CASCADE,
        related_name="propuestas_cliente",
    )
    cotizacion = models.ForeignKey(
        CotizacionProveedor,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="propuestas_cliente",
    )
    version = models.PositiveIntegerField()
    modalidad = models.CharField(
        max_length=25,
        choices=MODALIDADES,
        default="ADICIONAL",
    )
    descripcion = models.TextField(blank=True, null=True)
    costo_base_snapshot = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
    )
    margen = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
    )
    precio_cliente = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
    )
    referencia_paquete = models.CharField(
        max_length=180,
        blank=True,
        null=True,
    )
    estado = models.CharField(
        max_length=25,
        choices=ESTADOS,
        default="BORRADOR",
    )
    enviado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="propuestas_cliente_enviadas",
    )
    respondido_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="propuestas_cliente_respondidas",
    )
    comentario_cliente = models.TextField(blank=True, null=True)
    fecha_envio = models.DateTimeField(blank=True, null=True)
    fecha_respuesta = models.DateTimeField(blank=True, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-version", "-id"]
        constraints = [
            models.UniqueConstraint(
                fields=["expediente", "version"],
                name="colaboracion_propuesta_version_unica",
            ),
        ]

    def __str__(self):
        return f"Propuesta {self.expediente} v{self.version}"


class PartidaPresupuestoCliente(models.Model):
    ESTADOS = [
        ("ACTIVA", "Activa"),
        ("CANCELADA", "Cancelada"),
    ]

    evento = models.ForeignKey(
        "invitaciones.EventoBoda",
        on_delete=models.CASCADE,
        related_name="partidas_presupuesto_cliente",
    )
    expediente = models.ForeignKey(
        ExpedienteServicio,
        on_delete=models.CASCADE,
        related_name="partidas_presupuesto_cliente",
    )
    propuesta = models.OneToOneField(
        PropuestaCliente,
        on_delete=models.CASCADE,
        related_name="partida_presupuesto",
    )
    concepto = models.CharField(max_length=180)
    monto_cliente = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
    )
    incluido_en_paquete = models.BooleanField(default=False)
    estado = models.CharField(
        max_length=15,
        choices=ESTADOS,
        default="ACTIVA",
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["fecha_creacion", "id"]

    def __str__(self):
        return self.concepto


# K.8.4 ---------------------------------------------------------------------
# Workspace contextualizado directamente sobre ServicioEvento.
# Los modelos legacy ExpedienteServicio/MensajeExpediente se conservan durante
# la transición, pero el nuevo núcleo de comunicación NO depende de ellos.

class TemaServicio(models.Model):
    servicio_evento = models.ForeignKey(
        "proveedores.ServicioEvento",
        on_delete=models.CASCADE,
        related_name="temas_workspace",
    )
    nombre = models.CharField(max_length=120)
    descripcion = models.TextField(blank=True, null=True)
    activo = models.BooleanField(default=True)
    orden = models.PositiveIntegerField(default=0)
    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="temas_servicio_creados",
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["orden", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["servicio_evento", "nombre"],
                name="colab_tema_servicio_nombre_unico",
            )
        ]
        indexes = [
            models.Index(fields=["servicio_evento", "activo"], name="colab_tema_srv_act_idx"),
        ]

    def __str__(self):
        return f"{self.servicio_evento} · {self.nombre}"


class ConversacionServicio(models.Model):
    CANALES = [
        ("CLIENTE_PLANNER", "Cliente / Planner"),
        ("PLANNER_PROVEEDOR", "Planner / Proveedor"),
        ("INTERNO", "Interno empresa / Planner"),
    ]

    servicio_evento = models.ForeignKey(
        "proveedores.ServicioEvento",
        on_delete=models.CASCADE,
        related_name="conversaciones_workspace",
    )
    canal = models.CharField(max_length=30, choices=CANALES)
    activa = models.BooleanField(default=True)
    archivada_en = models.DateTimeField(blank=True, null=True)
    creada_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="conversaciones_servicio_creadas",
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["servicio_evento", "canal"]
        constraints = [
            models.UniqueConstraint(
                fields=["servicio_evento", "canal"],
                name="colab_conversacion_servicio_canal_unico",
            )
        ]
        indexes = [
            models.Index(fields=["servicio_evento", "canal", "activa"], name="colab_conv_srv_canal_idx"),
        ]

    def __str__(self):
        return f"{self.servicio_evento} · {self.get_canal_display()}"


class MensajeServicio(models.Model):
    TIPOS = [
        ("MENSAJE", "Mensaje"),
        ("SISTEMA", "Sistema"),
    ]

    conversacion = models.ForeignKey(
        ConversacionServicio,
        on_delete=models.CASCADE,
        related_name="mensajes",
    )
    tema = models.ForeignKey(
        TemaServicio,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="mensajes",
    )
    autor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="mensajes_servicio_workspace",
    )
    tipo = models.CharField(max_length=15, choices=TIPOS, default="MENSAJE")
    texto = models.TextField(blank=True)
    fecha = models.DateTimeField(auto_now_add=True)
    editado_en = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ["fecha", "id"]
        indexes = [
            models.Index(fields=["conversacion", "fecha"], name="colab_msg_conv_fecha_idx"),
            models.Index(fields=["tema", "fecha"], name="colab_msg_tema_fecha_idx"),
        ]

    def __str__(self):
        return f"Mensaje {self.id} · {self.conversacion}"


class AdjuntoMensajeServicio(models.Model):
    mensaje = models.ForeignKey(
        MensajeServicio,
        on_delete=models.CASCADE,
        related_name="adjuntos",
    )
    archivo = models.FileField(
        upload_to="colaboracion/workspace/adjuntos/",
        validators=[validar_documento],
    )
    nombre_original = models.CharField(max_length=255, blank=True)
    tipo_mime = models.CharField(max_length=120, blank=True)
    tamano_bytes = models.PositiveBigIntegerField(default=0)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return self.nombre_original or self.archivo.name


class ReferenciaServicio(models.Model):
    TIPOS = [
        ("REFERENCIA", "Referencia"),
        ("INSPIRACION", "Inspiracion"),
        ("DOCUMENTO", "Documento"),
        ("COMPROBANTE", "Comprobante"),
        ("OTRO", "Otro"),
    ]

    servicio_evento = models.ForeignKey(
        "proveedores.ServicioEvento",
        on_delete=models.CASCADE,
        related_name="referencias_workspace",
    )
    tema = models.ForeignKey(
        TemaServicio,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="referencias",
    )
    mensaje_origen = models.ForeignKey(
        MensajeServicio,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="referencias_generadas",
    )
    adjunto_origen = models.ForeignKey(
        AdjuntoMensajeServicio,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="referencias_generadas",
    )
    tipo = models.CharField(max_length=20, choices=TIPOS, default="REFERENCIA")
    titulo = models.CharField(max_length=180)
    descripcion = models.TextField(blank=True, null=True)
    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="referencias_servicio_creadas",
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-fecha_creacion", "-id"]
        indexes = [
            models.Index(fields=["servicio_evento", "tipo"], name="colab_ref_srv_tipo_idx"),
        ]

    def __str__(self):
        return self.titulo

# K.8.5 ---------------------------------------------------------------------
# Resultado estructurado del workspace: decisiones, cotizaciones, propuestas y
# aprobaciones directamente vinculadas a ServicioEvento. Los modelos legacy
# ligados a ExpedienteServicio se mantienen durante la transición.

class DecisionServicio(models.Model):
    ESTADOS = [
        ("VIGENTE", "Vigente"),
        ("REEMPLAZADA", "Reemplazada"),
        ("CANCELADA", "Cancelada"),
    ]
    servicio_evento = models.ForeignKey(
        "proveedores.ServicioEvento", on_delete=models.CASCADE,
        related_name="decisiones_workspace",
    )
    tema = models.ForeignKey(
        TemaServicio, on_delete=models.SET_NULL, blank=True, null=True,
        related_name="decisiones",
    )
    mensaje_origen = models.ForeignKey(
        MensajeServicio, on_delete=models.SET_NULL, blank=True, null=True,
        related_name="decisiones_generadas",
    )
    titulo = models.CharField(max_length=180)
    descripcion = models.TextField(blank=True, null=True)
    estado = models.CharField(max_length=20, choices=ESTADOS, default="VIGENTE")
    registrado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, blank=True, null=True,
        related_name="decisiones_servicio_registradas",
    )
    fecha_decision = models.DateTimeField(default=timezone.now)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-fecha_decision", "-id"]
        indexes = [models.Index(fields=["servicio_evento", "estado"], name="colab_dec_srv_est_idx")]

    def __str__(self):
        return self.titulo


class CotizacionServicio(models.Model):
    ESTADOS = [
        ("ENVIADA", "Enviada"),
        ("CAMBIOS_SOLICITADOS", "Cambios solicitados"),
        ("ACEPTADA", "Aceptada por planner"),
        ("RECHAZADA", "Rechazada"),
        ("REEMPLAZADA", "Reemplazada por nueva version"),
    ]
    servicio_evento = models.ForeignKey(
        "proveedores.ServicioEvento", on_delete=models.CASCADE,
        related_name="cotizaciones_workspace",
    )
    version = models.PositiveIntegerField()
    costo_proveedor = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    descripcion = models.TextField(blank=True, null=True)
    vigencia = models.DateField(blank=True, null=True)
    archivo = models.FileField(
        upload_to="colaboracion/workspace/cotizaciones/",
        validators=[validar_documento], blank=True, null=True,
    )
    estado = models.CharField(max_length=25, choices=ESTADOS, default="ENVIADA")
    respuesta_planner = models.TextField(blank=True, null=True)
    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, blank=True, null=True,
        related_name="cotizaciones_servicio_workspace_creadas",
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-version", "-id"]
        constraints = [models.UniqueConstraint(fields=["servicio_evento", "version"], name="colab_cot_srv_version_unica")]

    def __str__(self):
        return f"{self.servicio_evento} · cotizacion v{self.version}"


class PropuestaServicioCliente(models.Model):
    MODALIDADES = [
        ("INCLUIDO", "Incluido en paquete"),
        ("UPGRADE", "Upgrade / diferencia"),
        ("ADICIONAL", "Servicio adicional"),
    ]
    ESTADOS = [
        ("BORRADOR", "Borrador"),
        ("ENVIADA", "Enviada al cliente"),
        ("CAMBIOS_SOLICITADOS", "Cambios solicitados"),
        ("APROBADA", "Aprobada"),
        ("RECHAZADA", "Rechazada"),
        ("REEMPLAZADA", "Reemplazada por nueva version"),
    ]
    servicio_evento = models.ForeignKey(
        "proveedores.ServicioEvento", on_delete=models.CASCADE,
        related_name="propuestas_workspace",
    )
    cotizacion = models.ForeignKey(
        CotizacionServicio, on_delete=models.SET_NULL, blank=True, null=True,
        related_name="propuestas_cliente",
    )
    version = models.PositiveIntegerField()
    modalidad = models.CharField(max_length=20, choices=MODALIDADES, default="ADICIONAL")
    descripcion = models.TextField(blank=True, null=True)
    costo_proveedor_snapshot = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    valor_contratado_snapshot = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    cargo_adicional_cliente = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    estado = models.CharField(max_length=25, choices=ESTADOS, default="BORRADOR")
    enviado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, blank=True, null=True,
        related_name="propuestas_servicio_workspace_enviadas",
    )
    respondido_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, blank=True, null=True,
        related_name="propuestas_servicio_workspace_respondidas",
    )
    comentario_cliente = models.TextField(blank=True, null=True)
    fecha_envio = models.DateTimeField(blank=True, null=True)
    fecha_respuesta = models.DateTimeField(blank=True, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-version", "-id"]
        constraints = [models.UniqueConstraint(fields=["servicio_evento", "version"], name="colab_prop_srv_version_unica")]

    def __str__(self):
        return f"{self.servicio_evento} · propuesta v{self.version}"


class AprobacionServicio(models.Model):
    ESTADOS = [
        ("PENDIENTE", "Pendiente"),
        ("APROBADA", "Aprobada"),
        ("CAMBIOS", "Solicita cambios"),
        ("RECHAZADA", "Rechazada"),
    ]
    servicio_evento = models.ForeignKey(
        "proveedores.ServicioEvento", on_delete=models.CASCADE,
        related_name="aprobaciones_workspace",
    )
    tema = models.ForeignKey(
        TemaServicio, on_delete=models.SET_NULL, blank=True, null=True,
        related_name="aprobaciones",
    )
    decision = models.ForeignKey(
        DecisionServicio, on_delete=models.SET_NULL, blank=True, null=True,
        related_name="aprobaciones",
    )
    propuesta = models.ForeignKey(
        PropuestaServicioCliente, on_delete=models.SET_NULL, blank=True, null=True,
        related_name="aprobaciones",
    )
    titulo = models.CharField(max_length=180)
    descripcion = models.TextField(blank=True, null=True)
    estado = models.CharField(max_length=20, choices=ESTADOS, default="PENDIENTE")
    solicitado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, blank=True, null=True,
        related_name="aprobaciones_servicio_workspace_solicitadas",
    )
    respondido_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, blank=True, null=True,
        related_name="aprobaciones_servicio_workspace_respondidas",
    )
    comentario_respuesta = models.TextField(blank=True, null=True)
    fecha_solicitud = models.DateTimeField(default=timezone.now)
    fecha_respuesta = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ["estado", "-fecha_solicitud", "-id"]
        indexes = [models.Index(fields=["servicio_evento", "estado"], name="colab_apr_srv_est_idx")]

    def __str__(self):
        return self.titulo
