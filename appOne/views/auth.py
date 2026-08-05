# appOne/views/auth.py
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.db.models import Q
from django.views.decorators.http import require_POST
from appOne.forms import RegistroForm
from appOne.models import Usuario, BitacoraAuditoria, Notificacion
from .utils import registrar_auditoria

# Importación condicional de django-ratelimit para evitar fallos si no está instalado
try:
    from django_ratelimit.decorators import ratelimit
except ImportError:
    def ratelimit(*args, **kwargs):
        def decorator(func):
            return func
        return decorator


# ============================
# ----- LOGIN / LOGOUT -------
# ============================

@ratelimit(key='ip', rate='5/m', method='POST', block=True)
def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboardinicio')

    if request.method == "POST":
        correo = request.POST.get("username", "").strip()
        password = request.POST.get("password", "").strip()

        if not correo or not password:
            messages.error(request, "Por favor ingrese su correo institucional y contraseña.")
            return render(request, "appOne/login.html")

        user = authenticate(request, correo_institucional=correo, password=password)

        if user is not None:
            if not user.is_active:
                messages.error(
                    request, 
                    "Tu cuenta está registrada pero aún pendiente de aprobación por el administrador."
                )
                return render(request, "appOne/login.html")

            login(request, user)
            registrar_auditoria(
                request, 
                BitacoraAuditoria.ACCION_LOGIN, 
                "Autenticación", 
                user.id, 
                "Inicio de sesión exitoso"
            )
            messages.success(request, f"¡Bienvenido de nuevo, {user.nombre_completo}!")
            return redirect('dashboardinicio')
        else:
            messages.error(request, "Usuario o contraseña incorrectos.")

    return render(request, "appOne/login.html")


@require_POST
def logout_view(request):
    if request.user.is_authenticated:
        registrar_auditoria(
            request, 
            BitacoraAuditoria.ACCION_LOGOUT, 
            "Autenticación", 
            request.user.id, 
            "Cierre de sesión"
        )
    logout(request)
    return redirect('login')


# ============================
# -------- REGISTRO ----------
# ============================

def registro(request):
    if request.user.is_authenticated:
        return redirect('dashboardinicio')

    if request.method == 'POST':
        form = RegistroForm(request.POST)
        if form.is_valid():
            usuario = form.save(commit=False)
            usuario.is_active = False  # Requiere aprobación del administrador
            usuario.save()

            registrar_auditoria(
                request, 
                BitacoraAuditoria.ACCION_CREAR, 
                "Usuarios", 
                usuario.id, 
                f"Registro de usuario pendiente de aprobación: {usuario.correo_institucional}"
            )

            # Notificar a los administradores
            admins = Usuario.objects.filter(Q(rol="Admin") | Q(is_superuser=True), is_active=True)
            for admin in admins:
                Notificacion.objects.create(
                    usuario=admin,
                    titulo="Nuevo Registro de Usuario",
                    mensaje=f"El usuario {usuario.nombre_completo} ({usuario.correo_institucional}) se ha registrado y requiere aprobación.",
                    tipo=Notificacion.TIPO_ALERTA
                )

            messages.success(
                request, 
                "Solicitud de registro recibida. Se ha enviado una notificación al administrador para su aprobación."
            )
            return redirect('login')
        else:
            messages.error(request, "Error al registrar la cuenta. Por favor verifica los datos ingresados.")
    else:
        form = RegistroForm()

    return render(request, 'appOne/registro.html', {'form': form})