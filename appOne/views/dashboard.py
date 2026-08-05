from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.contrib import messages

from appOne.models import Usuario, Dispositivo, Prestamo
from .utils import es_administrador


@login_required
def dashboard(request):
    usuario = request.user

    if not usuario.is_active:
        messages.error(request, "Tu cuenta aún no ha sido aprobada.")
        logout(request)
        return redirect('login')

    return render(request, "appOne/dashboard.html", {
        "perfil": usuario,
    })


@login_required
def layaut_Principal(request):
    # Conteos generales para las tarjetas
    total_usuarios = Usuario.objects.filter(is_active=True).count()
    prestamos_activos = Prestamo.objects.filter(estado=Prestamo.ESTADO_APROBADO).count()
    dispositivos_disponibles = Dispositivo.objects.filter(estado=Dispositivo.ESTADO_DISPONIBLE).count()
    pendientes_count = Prestamo.objects.filter(estado=Prestamo.ESTADO_PENDIENTE).count()

    # Variables para el Topbar y Notificaciones
    prestamos_pendientes_admin = []
    usuarios_pendientes_admin = []
    prestamos_propios = []

    if es_administrador(request.user) or request.user.is_superuser:
        ultimos_prestamos = Prestamo.objects.select_related('usuario', 'dispositivo').order_by('-fecha_solicitud')[:5]
        prestamos_pendientes_admin = Prestamo.objects.select_related('usuario', 'dispositivo').filter(
            estado=Prestamo.ESTADO_PENDIENTE
        ).order_by('-fecha_solicitud')[:5]
        usuarios_pendientes_admin = Usuario.objects.filter(is_active=False).order_by('-id')[:5]
    else:
        ultimos_prestamos = Prestamo.objects.select_related('usuario', 'dispositivo').filter(
            usuario=request.user
        ).order_by('-fecha_solicitud')[:5]
        prestamos_propios = Prestamo.objects.select_related('dispositivo').filter(
            usuario=request.user
        ).order_by('-fecha_solicitud')[:5]

    context = {
        'estadisticas': {
            'usuarios': total_usuarios,
            'prestamos': prestamos_activos,
            'disponibles': dispositivos_disponibles,
        },
        'pendientes_count': pendientes_count,
        'ultimos_prestamos': ultimos_prestamos,
        'prestamos_pendientes_admin': prestamos_pendientes_admin,
        'usuarios_pendientes_admin': usuarios_pendientes_admin,
        'prestamos_propios': prestamos_propios,
    }

    return render(request, 'appOne/layaut_Principal.html', context)