from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models


# ============================
#           ROLES
# ============================

ROLES = (
    ("Docente", "Horario"),
    ("Administrativo", "Planta"),
    ("Admin", "Admin del sistema"),
)


# ============================
#   MANAGER PERSONALIZADO
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
#       USUARIO PERSONALIZADO
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

    def __str__(self):
        return f"{self.nombre_completo} ({self.rol})"


# ============================
#         DISPOSITIVOS
# ============================

class Dispositivo(models.Model):
    nombre_dispositivo = models.CharField(max_length=100)
    marca = models.CharField(max_length=50)
    codigo_inventario = models.CharField(max_length=50, unique=True)
    imagen = models.ImageField(upload_to='dispositivos/', blank=True, null=True)
    descripcion = models.TextField(blank=True, null=True)
    accesorios = models.TextField(blank=True, null=True)
    observacion = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.nombre_dispositivo} ({self.codigo_inventario})"


# ============================
#           PRÉSTAMOS
# ============================

class Prestamo(models.Model):

    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('aprobado', 'Aprobado'),
        ('devuelto', 'Devuelto'),
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
    fecha_uso = models.DateField()
    hora_inicio = models.TimeField()
    hora_entrega = models.TimeField()

    estado = models.CharField(
        max_length=10,
        choices=ESTADO_CHOICES,
        default='pendiente'
    )

    fecha_solicitud = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.dispositivo.nombre_dispositivo} - {self.usuario.nombre_completo} ({self.estado})"
