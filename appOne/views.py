from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .forms import RegistroForm, DispositivoForm, PrestamoForm
from .models import Usuario, Dispositivo, Prestamo
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Count
from django.utils import timezone
from datetime import timedelta
from django.db.models import Q


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

    buscar = request.GET.get('buscar')
    rol = request.GET.get('rol')
    estado = request.GET.get('estado')

    usuarios = Usuario.objects.all()

    # 🔎 BUSCADOR
    if buscar:
        usuarios = usuarios.filter(
            Q(nombre_completo__icontains=buscar) |
            Q(correo_institucional__icontains=buscar) |
            Q(codigo__icontains=buscar) |
            Q(dispositivos__nombre_dispositivo__icontains=buscar)  # <-- magia
        ).distinct()

    # 🎭 FILTRO POR ROL
    if rol:
        usuarios = usuarios.filter(rol=rol)

    # 🟢 FILTRO POR ESTADO
    if estado == "activo":
        usuarios = usuarios.filter(is_active=True)
    elif estado == "inactivo":
        usuarios = usuarios.filter(is_active=False)

    context = {
        'usuarios': usuarios,
    }
    return render(request, 'appOne/panel_usuarios.html', context)


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

        form = DispositivoForm(
            request.POST,
            request.FILES,
            instance=dispositivo
        )

        if form.is_valid():
            form.save()

            messages.success(
                request,
                "Dispositivo actualizado correctamente."
            )

            return redirect('listardispositivos')

    else:

        form = DispositivoForm(instance=dispositivo)

    # AJAX
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":

        return render(
            request,
            'appOne/form_editar_dispositivo.html',
            {
                'form': form,
                'dispositivo': dispositivo
            }
        )

    return render(
        request,
        'appOne/form_editar_dispositivo.html',
        {
            'form': form,
            'dispositivo': dispositivo
        }
    )


@login_required
def eliminar_dispositivo(request, id):
    dispositivo = get_object_or_404(Dispositivo, id=id)
    dispositivo.delete()
    messages.warning(request, "Dispositivo eliminado.")
    return redirect('listardispositivos')

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
            prestamo.estado = Prestamo.ESTADO_PENDIENTE
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
def crear_prestamo(request):
    if request.method == "POST":

        dispositivo_id = request.POST.get("dispositivo_id")
        dispositivo = get_object_or_404(Dispositivo, id=dispositivo_id)

        prestamo_activo = Prestamo.objects.filter(
            usuario=request.user,
            dispositivo=dispositivo,
            estado__in=[
                Prestamo.ESTADO_PENDIENTE,
                Prestamo.ESTADO_APROBADO
            ]
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
            estado=Prestamo.ESTADO_PENDIENTE
        )

        messages.success(request, "Solicitud enviada correctamente.")
        return redirect("listardispositivos")
    
@login_required
def aprobar_prestamo(request, id):
    if request.user.rol != "Admin":
        return redirect("dashboard")

    prestamo = get_object_or_404(Prestamo, id=id)
    prestamo.estado = Prestamo.ESTADO_APROBADO
    prestamo.save()

    messages.success(request, "Préstamo aprobado.")
    return redirect("solicitudes_prestamos")



@login_required
def rechazar_prestamo(request, id):
    if request.user.rol != "Admin":
        return redirect('dashboard')

    prestamo = get_object_or_404(Prestamo, id=id)
    prestamo.estado = Prestamo.ESTADO_RECHAZADO
    prestamo.save()

    messages.error(request, "Préstamo rechazado.")
    return redirect('solicitudes_prestamos')


@login_required
def devolver_prestamo(request, id):
    if request.user.rol != "Admin":
        return redirect("dashboard")

    prestamo = get_object_or_404(Prestamo, id=id)

    # Solo se puede devolver si está aprobado
    if prestamo.estado == Prestamo.ESTADO_APROBADO:
        prestamo.estado = Prestamo.ESTADO_DEVUELTO
        prestamo.save()
        messages.success(request, "Dispositivo devuelto correctamente.")
    else:
        messages.warning(request, "Este préstamo no puede ser devuelto.")

    return redirect("solicitudes_prestamos")

@login_required
def solicitudes_prestamos(request):

    estado = request.GET.get("estado")

    if request.user.rol == "Admin":
        prestamos = Prestamo.objects.all()
    else:
        prestamos = Prestamo.objects.filter(usuario=request.user)

    # ===== FILTRO POR ESTADO =====
    if estado and estado != "todos":
        prestamos = prestamos.filter(estado=estado)

    prestamos = prestamos.order_by("-fecha_solicitud")

    return render(request, "appOne/solicitudes.html", {
        "prestamos": prestamos,
        "estado_actual": estado or "todos"
    })


@login_required
def reportes(request):
    # ===== Métricas generales =====
    total_dispositivos = Dispositivo.objects.count()
    total_usuarios = Usuario.objects.filter(is_active=True).count()
    total_prestamos = Prestamo.objects.count()

    # ===== Préstamos por estado =====
    estados = Prestamo.objects.values('estado').annotate(total=Count('id'))

    estados_labels = [e['estado'] for e in estados]
    estados_data = [e['total'] for e in estados]

    # ===== Préstamos últimos 7 días =====
    hoy = timezone.now().date()
    dias = []
    prestamos_por_dia = []

    for i in range(6, -1, -1):
        dia = hoy - timedelta(days=i)
        cantidad = Prestamo.objects.filter(fecha_uso=dia).count()
        dias.append(dia.strftime("%d/%m"))
        prestamos_por_dia.append(cantidad)

    # ===== Dispositivos más solicitados =====
    dispositivos = (
        Prestamo.objects.values('dispositivo__nombre_dispositivo')
        .annotate(total=Count('id'))
        .order_by('-total')[:5]
    )

    dispositivos_labels = [d['dispositivo__nombre_dispositivo'] for d in dispositivos]
    dispositivos_data = [d['total'] for d in dispositivos]

    context = {
        'total_dispositivos': total_dispositivos,
        'total_usuarios': total_usuarios,
        'total_prestamos': total_prestamos,
        'estados_labels': estados_labels,
        'estados_data': estados_data,
        'dias': dias,
        'prestamos_por_dia': prestamos_por_dia,
        'dispositivos_labels': dispositivos_labels,
        'dispositivos_data': dispositivos_data,
    }

    return render(request, 'appOne/reportes.html', context)


