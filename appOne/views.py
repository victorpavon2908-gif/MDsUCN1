from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .forms import RegistroForm , DispositivoForm
from .models import Usuario , Dispositivo
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

# ============================
# ----- LOGIN ----------------
# ============================
def login_view(request):
    if request.method == "POST":
        correo = request.POST.get("username")   # Login usando correo institucional
        password = request.POST.get("password")

        user = authenticate(request, correo_institucional=correo, password=password)

        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, "Usuario o contraseña incorrectos.")

    return render(request, "appOne/login.html")


# ============================
# ---------- LOGOUT ----------
# ============================
def logout_view(request):
    logout(request)
    return redirect('login')


# ============================
# -------- REGISTRO ----------
# ============================
def registro(request):
    if request.method == 'POST':
        form = RegistroForm(request.POST)
        if form.is_valid():
            usuario = form.save(commit=False)

            # Los usuarios nuevos NO están activos hasta aprobación
            usuario.is_active = False
            usuario.save()

            messages.success(request, "Registro enviado. Espera la aprobación del administrador.")
            return redirect('login')
    else:
        form = RegistroForm()

    return render(request, 'appOne/registro.html', {'form': form})


# ============================
# -------- DASHBOARD ---------
# ============================
@login_required
def dashboard(request):

    usuario = request.user  # YA NO SE USA PERFIL

    if not usuario.is_active:
        messages.error(request, "Tu cuenta aún no ha sido aprobada.")
        return redirect('login')

    return render(request, "appOne/dashboard.html", {"perfil": usuario})


# ============================
# ------ PANEL ADMIN ---------
# ============================
@login_required
def panel_usuarios(request):
    if request.user.rol != "Admin":   # <-- chequea rol
        messages.error(request, "No tienes permisos para ver esta sección.")
        return redirect('dashboard')

    usuarios = Usuario.objects.all()
    return render(request, 'appOne/panel_usuarios.html', {'usuarios': usuarios})


# ============================
# ---- APROBAR USUARIO -------
# ============================
@login_required
def aprobar_usuario(request, id):
    if request.user.rol != "Admin" and not request.user.is_superuser:
        return redirect('dashboard')

    usuario = get_object_or_404(Usuario, id=id)

    usuario.is_active = True
    usuario.save()

    messages.success(request, "Usuario aprobado correctamente.")
    return redirect('panel_usuarios')


# ============================
# ---- RECHAZAR USUARIO ------
# ============================
@login_required
def rechazar_usuario(request, id):
    if request.user.rol != "Admin" and not request.user.is_superuser:
        return redirect('dashboard')

    usuario = get_object_or_404(Usuario, id=id)

    usuario.is_active = False
    usuario.save()

    messages.warning(request, "Usuario rechazado.")
    return redirect('panel_usuarios')


@login_required
def eliminar_usuario(request, id):
    # Solo administradores pueden eliminar usuarios
    if request.user.rol != "Admin" and not request.user.is_superuser:
        messages.error(request, "No tienes permisos para eliminar usuarios.")
        return redirect('dashboard')

    usuario = get_object_or_404(Usuario, id=id)

    # Evitar que un Admin se elimine a sí mismo
    if usuario == request.user:
        messages.error(request, "No puedes eliminar tu propia cuenta.")
        return redirect('panel_usuarios')

    usuario.delete()
    messages.warning(request, "Usuario eliminado correctamente.")
    return redirect('panel_usuarios')


# ============================
#  Vista para prestar MEdios -
# ============================
# ============================
#  Vista para administar medios -
# ============================

@login_required
def listardispositivos(request):
    dispositivos = Dispositivo.objects.all()  # Trae todos los dispositivos
    return render(request, 'appOne/Dispositivos.html', {'dispositivo': dispositivos})

@login_required
def agregar_dispositivo(request):
    if request.method == "POST":
        form = DispositivoForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Dispositivo agregado correctamente.")
            return redirect('listardispositivos')
    else:
        form = DispositivoForm()
    return render(request, 'appOne/agregar_dispositivo.html', {'form': form})

@login_required
def editar_dispositivo(request, id):
    dispositivo = get_object_or_404(Dispositivo, id=id)

    if request.method == "POST":
        form = DispositivoForm(request.POST, request.FILES, instance=dispositivo)
        if form.is_valid():
            form.save()
            messages.success(request, "Dispositivo actualizado correctamente.")
            return redirect('listardispositivos')
    else:
        form = DispositivoForm(instance=dispositivo)

        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return render(request, 'appOne/form_editar_dispositivo.html', {
                'form': form,
                'dispositivo': dispositivo
            })

    return render(request, 'appOne/form_editar_dispositivo.html', {
        'form': form,
        'dispositivo': dispositivo
    })


@login_required
def eliminar_dispositivo(request, id):
    dispositivo = get_object_or_404(Dispositivo, id=id)
    dispositivo.delete()
    messages.warning(request, "Dispositivo eliminado.")
    return redirect('listardispositivos')


@csrf_exempt
@login_required
def aprobar_usuario_ajax(request, id):
    if request.method == "POST":
        usuario = get_object_or_404(Usuario, id=id)
        usuario.is_active = True
        usuario.save()
        return JsonResponse({'status': 'ok'})

@csrf_exempt
@login_required
def rechazar_usuario_ajax(request, id):
    if request.method == "POST":
        usuario = get_object_or_404(Usuario, id=id)
        usuario.is_active = False
        usuario.save()
        return JsonResponse({'status': 'ok'})
    
@login_required
def dashboard(request):
    usuario = request.user
    pendiente_aprobacion = None

    if usuario.rol == "Admin" or usuario.is_superuser:
        # Traer todos los usuarios pendientes
        usuarios_pendientes = Usuario.objects.filter(is_active=False)
        pendientes_count = usuarios_pendientes.count()
    else:
        usuarios_pendientes = None
        pendientes_count = 0


    return render(request, "appOne/dashboard.html", {
        "perfil": usuario,
        "usuarios_pendientes": usuarios_pendientes,
        "pendientes_count": pendientes_count
    })
