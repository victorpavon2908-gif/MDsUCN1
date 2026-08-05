from datetime import time, date
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.core.exceptions import ValidationError


# ============================
#         ROLES
# ============================

ROLES = (
    ("Docente", "Horario"),
    ("Administrativo", "Planta"),
    ("Admin", "Admin del sistema"),
)


# ============================
#    MANAGER PERSONALIZADO
# ============================

class UsuarioManager(BaseUserManager):

    def create_user(self, correo_institucional, password=None, **extra_fields):
        if not correo_institucional:
            raise ValueError("El usuario debe tener un correo institucional")

        correo_institucional = self.normalize_email(correo_institucional)

        usuario = self.model(
            correo_institucional=correo_institucional,
            **extra_fields
        )
        usuario.set_password(password)
        usuario.save(using=self._db)
        return usuario

    def create_superuser(self, correo_institucional, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("rol", "Admin")

        return self.create_user(correo_institucional, password, **extra_fields)


# ============================
#     USUARIO PERSONALIZADO
# ============================

class Usuario(AbstractUser):
    username = models.CharField(max_length=150, unique=True)
    nombre_completo = models.CharField(max_length=150)
    correo_institucional = models.EmailField(unique=True)
    codigo = models.CharField(max_length=20, unique=True)
    rol = models.CharField(max_length=20, choices=ROLES, default="Docente")

    USERNAME_FIELD = "correo_institucional"
    REQUIRED_FIELDS = ["username", "nombre_completo", "codigo"]

    objects = UsuarioManager()

    class Meta:
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'

    def __str__(self):
        return f"{self.nombre_completo} ({self.rol})"


# ============================
#        DISPOSITIVOS
# ============================

class Dispositivo(models.Model):

    ESTADO_DISPONIBLE = 'disponible'
    ESTADO_PRESTADO = 'prestado'
    ESTADO_MANTENIMIENTO = 'mantenimiento'
    ESTADO_DANADO = 'danado'

    ESTADO_CHOICES = [
        (ESTADO_DISPONIBLE, 'Disponible'),
        (ESTADO_PRESTADO, 'En Préstamo'),
        (ESTADO_MANTENIMIENTO, 'En Mantenimiento'),
        (ESTADO_DANADO, 'Dañado / Inoperativo'),
    ]

    nombre_dispositivo = models.CharField(max_length=100)
    marca = models.CharField(max_length=50)
    codigo_inventario = models.CharField(max_length=50, unique=True)
    imagen = models.ImageField(upload_to='dispositivos/', blank=True, null=True)
    descripcion = models.TextField(blank=True, null=True)
    accesorios = models.TextField(blank=True, null=True)
    observacion = models.TextField(blank=True, null=True)
    
    estado = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES,
        default=ESTADO_DISPONIBLE,
        db_index=True
    )

    class Meta:
        verbose_name = 'Dispositivo'
        verbose_name_plural = 'Dispositivos'

    def __str__(self):
        return f"{self.nombre_dispositivo} ({self.codigo_inventario}) - {self.get_estado_display()}"


# ============================
#          PRÉSTAMOS
# ============================

class Prestamo(models.Model):

    ESTADO_PENDIENTE = 'pendiente'
    ESTADO_APROBADO = 'aprobado'
    ESTADO_RECHAZADO = 'rechazado'
    ESTADO_DEVUELTO = 'devuelto'

    ESTADO_CHOICES = [
        (ESTADO_PENDIENTE, 'Pendiente'),
        (ESTADO_APROBADO, 'Aprobado'),
        (ESTADO_RECHAZADO, 'Rechazado'),
        (ESTADO_DEVUELTO, 'Devuelto'),
    ]

    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name="prestamos"
    )

    dispositivo = models.ForeignKey(
        Dispositivo,
        on_delete=models.CASCADE,
        related_name="prestamos"
    )

    motivo = models.TextField()
    fecha_uso = models.DateField(db_index=True)
    hora_inicio = models.TimeField()
    hora_entrega = models.TimeField()

    estado = models.CharField(
        max_length=10,
        choices=ESTADO_CHOICES,
        default=ESTADO_PENDIENTE,
        db_index=True
    )

    fecha_solicitud = models.DateTimeField(auto_now_add=True, db_index=True)

    fecha_devolucion_real = models.DateTimeField(
        blank=True, 
        null=True,
        help_text="Fecha y hora exacta en que se registró la devolución"
    )
    observaciones_devolucion = models.TextField(
        blank=True, 
        null=True,
        help_text="Estado físico en que se recibe el equipo (daños, accesorios faltantes, etc.)"
    )

    class Meta:
        verbose_name = 'Préstamo'
        verbose_name_plural = 'Préstamos'

    def clean(self):
        super().clean()

        # 1. Validar que la fecha de uso no sea pasada
        if self.fecha_uso and self.fecha_uso < date.today():
            raise ValidationError({'fecha_uso': "No es posible programar un préstamo para una fecha pasada."})

        # 2. Validar que la hora de entrega sea posterior a la de inicio
        if self.hora_entrega and self.hora_inicio and self.hora_entrega <= self.hora_inicio:
            raise ValidationError({'hora_entrega': "La hora de entrega debe ser posterior a la hora de inicio."})

        # 3. Validar horario permitido de servicio (08:00 AM a 17:00 PM)
        HORA_INICIO_PERMITIDA = time(8, 0)
        HORA_FIN_PERMITIDA = time(17, 0)

        if self.hora_inicio and self.hora_inicio < HORA_INICIO_PERMITIDA:
            raise ValidationError({'hora_inicio': "La hora de inicio debe ser a partir de las 08:00 AM."})

        if self.hora_entrega and self.hora_entrega > HORA_FIN_PERMITIDA:
            raise ValidationError({'hora_entrega': "La hora de entrega no puede superar las 05:00 PM (17:00)."})

        # 4. Validar disponibilidad del estado físico del dispositivo
        if self.dispositivo_id and self.dispositivo.estado in [Dispositivo.ESTADO_MANTENIMIENTO, Dispositivo.ESTADO_DANADO]:
            raise ValidationError({'dispositivo': f"El equipo no está disponible ({self.dispositivo.get_estado_display()})."})

        # 5. Validar traslape/solapamiento de horario
        if self.dispositivo_id and self.fecha_uso and self.hora_inicio and self.hora_entrega:
            prestamos_conflictivos = Prestamo.objects.filter(
                dispositivo=self.dispositivo,
                fecha_uso=self.fecha_uso,
                estado__in=[self.ESTADO_APROBADO, self.ESTADO_PENDIENTE],
                hora_inicio__lt=self.hora_entrega,
                hora_entrega__gt=self.hora_inicio
            ).exclude(pk=self.pk)

            if prestamos_conflictivos.exists():
                raise ValidationError("El equipo ya cuenta con una reserva o solicitud activa en el horario seleccionado.")

    def __str__(self):
        return f"{self.dispositivo.nombre_dispositivo} - {self.usuario.nombre_completo} ({self.estado})"


# ============================
#        NOTIFICACIONES
# ============================

class Notificacion(models.Model):

    TIPO_INFO = 'INFO'
    TIPO_ALERTA = 'ALERTA'
    TIPO_URGENTE = 'URGENTE'

    TIPO_CHOICES = [
        (TIPO_INFO, 'Información'),
        (TIPO_ALERTA, 'Alerta'),
        (TIPO_URGENTE, 'Urgente / Retraso'),
    ]

    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name="notificaciones"
    )
    titulo = models.CharField(max_length=100, default="Notificación del sistema")
    mensaje = models.TextField()
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES, default=TIPO_INFO)
    leida = models.BooleanField(default=False)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-fecha_creacion']
        verbose_name = 'Notificación'
        verbose_name_plural = 'Notificaciones'

    def __str__(self):
        return f"[{self.get_tipo_display()}] {self.usuario.nombre_completo} - {self.titulo}"


# ============================
#     BITÁCORA DE AUDITORÍA
# ============================

class BitacoraAuditoria(models.Model):

    ACCION_CREAR = 'CREAR'
    ACCION_EDITAR = 'EDITAR'
    ACCION_ELIMINAR = 'ELIMINAR'
    ACCION_LOGIN = 'LOGIN'
    ACCION_LOGOUT = 'LOGOUT'

    ACCION_CHOICES = [
        (ACCION_CREAR, 'Creación'),
        (ACCION_EDITAR, 'Modificación'),
        (ACCION_ELIMINAR, 'Eliminación'),
        (ACCION_LOGIN, 'Inicio de Sesión'),
        (ACCION_LOGOUT, 'Cierre de Sesión'),
    ]

    usuario = models.ForeignKey(
        Usuario, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name="auditorias"
    )
    accion = models.CharField(max_length=20, choices=ACCION_CHOICES)
    tabla_afectada = models.CharField(max_length=100)
    registro_id = models.IntegerField(null=True, blank=True)
    detalles = models.TextField(blank=True, null=True)
    ip_origen = models.GenericIPAddressField(null=True, blank=True)
    fecha_hora = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-fecha_hora']
        verbose_name = 'Registro de Auditoría'
        verbose_name_plural = 'Bitácora de Auditoría'

    def __str__(self):
        usr = self.usuario.username if self.usuario else "Sistema"
        return f"{self.fecha_hora.strftime('%Y-%m-%d %H:%M:%S')} - {usr} - {self.accion} ({self.tabla_afectada})"