from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .forms import RegistroForm, DispositivoForm, PrestamoForm
from .models import Usuario, Dispositivo, Prestamo
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
            return redirect('dashboardinicio')
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
    usuario = request.user

    # Si NO está activo → mensaje y sacar al login
    if not usuario.is_active:
        messages.error(request, "Tu cuenta aún no ha sido aprobada.")
        logout(request)
        return redirect('login')

    # Si es admin → mostrar usuarios pendientes
    if usuario.rol == "Admin" or usuario.is_superuser:
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

@login_required
def layaut_Principal(request):
    return render(request, 'appOne/layaut_Principal.html')

# ============================
# ------ PANEL ADMIN ---------
# ============================
@login_required
def panel_usuarios(request):
    if request.user.rol != "Admin":
        messages.error(request, "No tienes permisos para ver esta sección.")
        return redirect('dashboard')

    usuarios = Usuario.objects.all()
    return render(request, 'appOne/panel_usuarios.html', {'usuarios': usuarios})


# ============================
# ---- APROBAR USUARIO -------
# ============================
@login_required
def rechazar_usuario(request, id):
    if request.user.rol != "Admin":
        messages.error(request, "No tienes permiso para realizar esta acción.")
        return redirect('dashboard')

    usuario = get_object_or_404(Usuario, id=id)
    usuario.is_active = False
    usuario.save()

    messages.warning(request, f"Usuario {usuario.nombre_completo} ha sido marcado como rechazado.")
    return redirect('panel_usuarios')

# ============================
# ---- RECHAZAR USUARIO ------
# ============================
@login_required
def aprobar_usuario(request, id):
    if request.user.rol != "Admin":
        messages.error(request, "No tienes permiso para realizar esta acción.")
        return redirect('dashboard')

    usuario = get_object_or_404(Usuario, id=id)
    usuario.is_active = True
    usuario.save()

    messages.success(request, f"Usuario {usuario.nombre_completo} aprobado.")
    return redirect('panel_usuarios')




# ============================
# ---- ELIMINAR USUARIO ------
# ============================
@login_required
def eliminar_usuario(request, id):
    if request.user.rol != "Admin" and not request.user.is_superuser:
        messages.error(request, "No tienes permisos para eliminar usuarios.")
        return redirect('dashboard')

    usuario = get_object_or_404(Usuario, id=id)

    # Evitar autoeliminarse
    if usuario == request.user:
        messages.error(request, "No puedes eliminar tu propia cuenta.")
        return redirect('panel_usuarios')

    usuario.delete()
    messages.warning(request, "Usuario eliminado correctamente.")
    return redirect('panel_usuarios')


# ============================
# --- DISPOSITIVOS (CRUD) ----
# ============================

@login_required
def listardispositivos(request):
    dispositivos = Dispositivo.objects.all()
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


# ============================
# --- AJAX APROBACIONES ------
# ============================

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
# ============================
# --- configuraciones------
# ============================

@login_required
def panel_config(request):

    # Solo admins
    if request.user.rol != "Admin" and not request.user.is_superuser:
        messages.error(request, "No tienes permisos para acceder a esta sección.")
        return redirect('dashboard')

    return render(request, 'appOne/panel_config.html')



@login_required
def solicitar_prestamo(request, id):
    dispositivo = get_object_or_404(Dispositivo, id=id)

    if request.method == "POST":
        form = PrestamoForm(request.POST)
        if form.is_valid():
            prestamo = form.save(commit=False)
            prestamo.usuario = request.user
            prestamo.dispositivo = dispositivo
            prestamo.estado = "Pendiente"
            prestamo.save()

            messages.success(request, "Solicitud enviada correctamente.")
            return redirect('listardispositivos')
    else:
        form = PrestamoForm()

    return render(request, "appOne/solicitar_prestamo.html", {
        "form": form,
        "dispositivo": dispositivo
    })

@login_required
def aprobar_prestamo(request, id):
    if request.user.rol != "Admin":
        return redirect("dashboard")

    prestamo = get_object_or_404(Prestamo, id=id)
    prestamo.estado = "aprobado"
    prestamo.save()

    messages.success(request, "Préstamo aprobado.")
    return redirect("solicitudes_prestamos")



@login_required
def rechazar_prestamo(request, id):
    if request.user.rol != "Admin":
        return redirect('dashboard')

    prestamo = get_object_or_404(Prestamo, id=id)
    prestamo.estado = "Rechazado"
    prestamo.save()

    messages.error(request, "Préstamo rechazado.")
    return redirect('solicitudes_prestamos')

@login_required
def crear_prestamo(request):
    if request.method == "POST":

        dispositivo_id = request.POST.get("dispositivo_id")

        dispositivo = get_object_or_404(Dispositivo, id=dispositivo_id)

        # ❌ evitar préstamos duplicados activos
        prestamo_activo = Prestamo.objects.filter(
            usuario=request.user,
            dispositivo=dispositivo,
            estado__in=["pendiente", "aprobado"]
        ).exists()

        if prestamo_activo:
            messages.warning(
                request,
                "Ya tienes una solicitud activa para este dispositivo."
            )
            return redirect("listardispositivos")

        Prestamo.objects.create(
            usuario=request.user,
            dispositivo=dispositivo,
            motivo=request.POST.get("motivo"),
            fecha_uso=request.POST.get("fecha_uso"),
            hora_inicio=request.POST.get("hora_inicio"),
            hora_entrega=request.POST.get("hora_entrega"),
            estado="pendiente"
        )

        messages.success(request, "Solicitud enviada correctamente.")
        return redirect("listardispositivos")

@login_required
def solicitudes_prestamos(request):

    if request.user.rol == "Admin":
        prestamos = Prestamo.objects.all().order_by("-fecha_solicitud")
    else:
        prestamos = Prestamo.objects.filter(
            usuario=request.user
        ).order_by("-fecha_solicitud")

    return render(request, "appOne/solicitudes.html", {
        "prestamos": prestamos
    })

@login_required
def devolver_prestamo(request, id):
    if request.user.rol != "Admin":
        return redirect("dashboard")

    prestamo = get_object_or_404(Prestamo, id=id)
    prestamo.estado = "devuelto"
    prestamo.save()

    messages.success(request, "Dispositivo devuelto correctamente.")
    return redirect("solicitudes_prestamos")


