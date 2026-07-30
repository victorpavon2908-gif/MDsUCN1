from datetime import timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.contrib.auth.forms import PasswordChangeForm
from .forms import RegistroForm, DispositivoForm
from .models import Usuario, Dispositivo, Prestamo


# ============================
# ----- LOGIN ----------------
# ============================
def login_view(request):
    if request.method == "POST":
        correo = request.POST.get("username")  # Login usando correo institucional
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

    if not usuario.is_active:
        messages.error(request, "Tu cuenta aún no ha sido aprobada.")
        logout(request)
        return redirect('login')

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
    if request.user.rol != "Admin" and not request.user.is_superuser:
        messages.error(request, "No tienes permisos para ver esta sección.")
        return redirect('dashboard')

    buscar = request.GET.get('buscar')
    rol = request.GET.get('rol')
    estado = request.GET.get('estado')

    usuarios = Usuario.objects.all()

    if buscar:
        usuarios = usuarios.filter(
            Q(nombre_completo__icontains=buscar) |
            Q(correo_institucional__icontains=buscar) |
            Q(codigo__icontains=buscar)
        ).distinct()

    if rol:
        usuarios = usuarios.filter(rol=rol)

    if estado == "activo":
        usuarios = usuarios.filter(is_active=True)
    elif estado == "inactivo":
        usuarios = usuarios.filter(is_active=False)

    return render(request, 'appOne/panel_usuarios.html', {'usuarios': usuarios})


# ============================
# ---- APROBAR USUARIO -------
# ============================
@login_required
def aprobar_usuario(request, id):
    if request.user.rol != "Admin" and not request.user.is_superuser:
        messages.error(request, "No tienes permiso para realizar esta acción.")
        return redirect('dashboard')

    usuario = get_object_or_404(Usuario, id=id)
    usuario.is_active = True
    usuario.save()

    messages.success(request, f"Usuario {usuario.nombre_completo} aprobado.")
    return redirect('panel_usuarios')


# ============================
# ---- RECHAZAR USUARIO ------
# ============================
@login_required
def rechazar_usuario(request, id):
    if request.user.rol != "Admin" and not request.user.is_superuser:
        messages.error(request, "No tienes permiso para realizar esta acción.")
        return redirect('dashboard')

    usuario = get_object_or_404(Usuario, id=id)
    usuario.is_active = False
    usuario.save()

    messages.warning(request, f"Usuario {usuario.nombre_completo} ha sido rechazado.")
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
    # IDs de dispositivos con préstamos vigentes (Pendientes o Aprobados)
    ids_ocupados = Prestamo.objects.filter(
        estado__in=[Prestamo.ESTADO_PENDIENTE, Prestamo.ESTADO_APROBADO]
    ).values_list('dispositivo_id', flat=True)

    # 1. Equipos Disponibles (Físicamente disponibles y SIN préstamos activos)
    dispositivos_disponibles = Dispositivo.objects.filter(
        estado=Dispositivo.ESTADO_DISPONIBLE
    ).exclude(id__in=ids_ocupados)

    # 2. Equipos Ocupados / Prestados
    dispositivos_ocupados = Dispositivo.objects.filter(
        id__in=ids_ocupados
    )

    # 3. Equipos En Mantenimiento
    dispositivos_mantenimiento = Dispositivo.objects.filter(
        estado=Dispositivo.ESTADO_MANTENIMIENTO
    )

    # 4. Equipos Dañados
    dispositivos_danados = Dispositivo.objects.filter(
        estado=Dispositivo.ESTADO_DANADO
    )

    # Préstamos pertenecientes al usuario actual
    prestamos_usuario = Prestamo.objects.filter(usuario=request.user)

    context = {
        "disponibles": dispositivos_disponibles,
        "ocupados": dispositivos_ocupados,
        "mantenimiento": dispositivos_mantenimiento,
        "danados": dispositivos_danados,
        "prestamos_usuario": prestamos_usuario,
    }

    return render(request, "appOne/Dispositivos.html", context)


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
# ----- CONFIGURACIONES ------
# ============================
@login_required
def panel_config(request):
    if request.user.rol != "Admin" and not request.user.is_superuser:
        messages.error(request, "No tienes permisos para acceder a esta sección.")
        return redirect('dashboard')

    return render(request, 'appOne/panel_config.html')


# ============================
# -------- PRÉSTAMOS ---------
# ============================
@login_required
def modal_prestamo(request, id):
    dispositivo = get_object_or_404(Dispositivo, id=id)
    return render(request, "appOne/modal_prestamo.html", {"dispositivo": dispositivo})


@login_required
def crear_prestamo(request):
    is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'

    if request.method == "POST":
        dispositivo_id = request.POST.get("dispositivo_id")
        dispositivo = get_object_or_404(Dispositivo, id=dispositivo_id)

        # 1. Validar disponibilidad física inicial
        if dispositivo.estado != Dispositivo.ESTADO_DISPONIBLE:
            msg = f"No es posible solicitar este equipo. Estado actual: {dispositivo.get_estado_display()}."
            if is_ajax:
                return JsonResponse({"success": False, "message": msg}, status=400)
            messages.error(request, msg)
            return redirect("listardispositivos")

        # 2. Validar préstamos activos
        prestamo_activo = Prestamo.objects.filter(
            usuario=request.user,
            dispositivo=dispositivo,
            estado__in=[
                Prestamo.ESTADO_PENDIENTE,
                Prestamo.ESTADO_APROBADO
            ]
        ).exists()

        if prestamo_activo:
            msg = "Ya tienes una solicitud activa para este dispositivo."
            if is_ajax:
                return JsonResponse({"success": False, "message": msg}, status=400)
            messages.warning(request, msg)
            return redirect("listardispositivos")

        # 3. Extraer valores del POST
        motivo = request.POST.get("motivo", "").strip()
        fecha_uso = request.POST.get("fecha_uso")
        hora_inicio = request.POST.get("hora_inicio")
        hora_entrega = request.POST.get("hora_entrega")

        if not all([motivo, fecha_uso, hora_inicio, hora_entrega]):
            msg = "Todos los campos son obligatorios."
            if is_ajax:
                return JsonResponse({"success": False, "message": msg}, status=400)
            messages.error(request, msg)
            return redirect("listardispositivos")

        # 4. Crear instancia de Préstamo
        nuevo_prestamo = Prestamo(
            usuario=request.user,
            dispositivo=dispositivo,
            motivo=motivo,
            fecha_uso=fecha_uso,
            hora_inicio=hora_inicio,
            hora_entrega=hora_entrega,
            estado=Prestamo.ESTADO_PENDIENTE
        )

        try:
            nuevo_prestamo.full_clean()
            nuevo_prestamo.save()
            messages.success(request, "Solicitud enviada correctamente.")
            return redirect("listardispositivos")

        except ValidationError as e:
            if hasattr(e, 'message_dict'):
                error_msg = "; ".join([f"{k}: {', '.join(v)}" for k, v in e.message_dict.items()])
            else:
                error_msg = ", ".join(e.messages)

            if is_ajax:
                return JsonResponse({"success": False, "message": f"Error de validación: {error_msg}"}, status=400)

            messages.error(request, f"Error al procesar la solicitud: {error_msg}")
            return redirect("listardispositivos")

    return redirect("listardispositivos")


@login_required
def aprobar_prestamo(request, id):
    if request.user.rol != "Admin" and not request.user.is_superuser:
        return redirect("dashboard")

    prestamo = get_object_or_404(Prestamo, id=id)

    # 1. Cambiar estado del préstamo y registrar timestamp de aprobación
    prestamo.estado = Prestamo.ESTADO_APROBADO
    if hasattr(prestamo, 'fecha_aprobacion'):
        prestamo.fecha_aprobacion = timezone.now()
    prestamo.save()

    # 2. Marcar el dispositivo como 'prestado'
    dispositivo = prestamo.dispositivo
    dispositivo.estado = Dispositivo.ESTADO_PRESTADO
    dispositivo.save()

    messages.success(request, f"Préstamo aprobado. {dispositivo.nombre_dispositivo} marcado como 'En Préstamo'.")
    return redirect("solicitudes_prestamos")


@login_required
def rechazar_prestamo(request, id):
    if request.user.rol != "Admin" and not request.user.is_superuser:
        return redirect('dashboard')

    prestamo = get_object_or_404(Prestamo, id=id)
    prestamo.estado = Prestamo.ESTADO_RECHAZADO
    prestamo.save()

    messages.error(request, "Préstamo rechazado.")
    return redirect('solicitudes_prestamos')


@login_required
def devolver_prestamo(request, id):
    if request.user.rol != "Admin" and not request.user.is_superuser:
        messages.error(request, "No tienes permisos para esta acción.")
        return redirect("dashboard")

    prestamo = get_object_or_404(Prestamo, id=id)

    if prestamo.estado != Prestamo.ESTADO_APROBADO:
        messages.warning(request, "Este préstamo no está activo para ser devuelto.")
        return redirect("solicitudes_prestamos")

    if request.method == "POST":
        observaciones = request.POST.get("observaciones_devolucion", "").strip()
        estado_dispositivo = request.POST.get("estado_dispositivo", Dispositivo.ESTADO_DISPONIBLE)

        # 1. Registrar fecha/hora de devolución real y guardar notas
        prestamo.estado = Prestamo.ESTADO_DEVUELTO
        prestamo.fecha_devolucion_real = timezone.now()
        prestamo.observaciones_devolucion = observaciones
        prestamo.save()

        # 2. Actualizar estado del dispositivo según la recepción
        dispositivo = prestamo.dispositivo
        dispositivo.estado = estado_dispositivo
        dispositivo.save()

        if estado_dispositivo == Dispositivo.ESTADO_DANADO:
            messages.warning(request, f"Devolución registrada. {dispositivo.nombre_dispositivo} fue marcado como 'Dañado'.")
        elif estado_dispositivo == Dispositivo.ESTADO_MANTENIMIENTO:
            messages.warning(request, f"Devolución registrada. {dispositivo.nombre_dispositivo} pasó a 'Mantenimiento'.")
        else:
            messages.success(request, f"Dispositivo {dispositivo.nombre_dispositivo} devuelto y marcado como 'Disponible'.")

        return redirect("solicitudes_prestamos")

    return redirect("solicitudes_prestamos")


# ============================
# --- GESTIÓN SOLICITUDES ----
# ============================
@login_required
def solicitudes_prestamos(request):
    estado = request.GET.get("estado")
    estado_actual = estado if estado else "todos"

    # Si se selecciona "todos" y la sesión tiene activa la bandera de limpiado:
    if estado_actual == "todos" and request.session.get("ocultar_todos", False):
        prestamos = Prestamo.objects.none()
    else:
        # Consulta base respetando el rol del usuario optimizada con select_related
        if request.user.rol == "Admin" or request.user.is_superuser:
            prestamos = Prestamo.objects.select_related('usuario', 'dispositivo').all()
        else:
            prestamos = Prestamo.objects.select_related('usuario', 'dispositivo').filter(usuario=request.user)

        # Filtrar por el estado exacto si la pestaña no es "todos"
        if estado_actual != "todos":
            prestamos = prestamos.filter(estado=estado_actual)

        prestamos = prestamos.order_by("-fecha_solicitud")

    return render(request, "appOne/solicitudes.html", {
        "prestamos": prestamos,
        "estado_actual": estado_actual
    })


@login_required
def eliminar_historial_prestamos(request):
    """Limpia la pestaña 'Todos' sin eliminar físicamente los registros de la base de datos."""
    if request.method == "POST" and (request.user.rol == "Admin" or request.user.is_superuser):
        request.session["ocultar_todos"] = True
        messages.success(request, "La vista 'Todos' se ha limpiado. Las solicitudes siguen accesibles en sus respectivas pestañas.")

    return redirect(request.META.get("HTTP_REFERER", "solicitudes_prestamos"))


@login_required
def restaurar_historial_todos(request):
    """Permite volver a mostrar los registros en la pestaña 'Todos'."""
    if "ocultar_todos" in request.session:
        del request.session["ocultar_todos"]
        messages.info(request, "Se ha restaurado la vista general de la pestaña 'Todos'.")
    return redirect(request.META.get("HTTP_REFERER", "solicitudes_prestamos"))


# ============================
# --------- REPORTES ---------
# ============================
@login_required
def reportes(request):
    total_dispositivos = Dispositivo.objects.count()
    total_usuarios = Usuario.objects.filter(is_active=True).count()
    total_prestamos = Prestamo.objects.count()

    estados = Prestamo.objects.values('estado').annotate(total=Count('id'))
    estados_labels = [e['estado'] for e in estados]
    estados_data = [e['total'] for e in estados]

    hoy = timezone.now().date()
    dias = []
    prestamos_por_dia = []

    for i in range(6, -1, -1):
        dia = hoy - timedelta(days=i)
        cantidad = Prestamo.objects.filter(fecha_uso=dia).count()
        dias.append(dia.strftime("%d/%m"))
        prestamos_por_dia.append(cantidad)

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


# ============================
# - VISTAS AJAX CONFIGURACIÓN -
# ============================
@login_required
def config_inicio(request):
    if not request.headers.get("x-requested-with") == "XMLHttpRequest":
        return render(request, "appOne/panel_config.html")

    context = {
        "total_usuarios": Usuario.objects.count(),
        "total_dispositivos": Dispositivo.objects.count(),
        "total_prestamos": Prestamo.objects.count(),
        "prestamos_aprobados": Prestamo.objects.filter(estado=Prestamo.ESTADO_APROBADO).count(),
        "prestamos_pendientes": Prestamo.objects.filter(estado=Prestamo.ESTADO_PENDIENTE).count(),
        "prestamos_rechazados": Prestamo.objects.filter(estado=Prestamo.ESTADO_RECHAZADO).count(),
    }

    return render(request, "appOne/configuracion/inicio.html", context)


@login_required
def config_database(request):
    return render(request, "appOne/configuracion/database.html")


@login_required
def config_perfil(request):
    """Actualiza la información personal básica del usuario."""
    if request.method == "POST":
        user = request.user
        user.first_name = request.POST.get("first_name", "").strip()
        user.last_name = request.POST.get("last_name", "").strip()
        user.email = request.POST.get("email", "").strip()
        user.save()

        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({"success": True, "message": "Perfil actualizado correctamente."})

    return render(request, "appOne/configuracion/perfil.html")


@login_required
def config_seguridad(request):
    """Cambia la contraseña utilizando PasswordChangeForm nativo de Django."""
    if request.method == "POST":
        form = PasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            user = form.save()
            # Mantiene al usuario con la sesión iniciada tras cambiar la clave
            update_session_auth_hash(request, user)

            if request.headers.get("x-requested-with") == "XMLHttpRequest":
                return JsonResponse({"success": True, "message": "Contraseña actualizada con éxito."})
        else:
            errors = "; ".join([f"{', '.join(v)}" for k, v in form.errors.items()])
            if request.headers.get("x-requested-with") == "XMLHttpRequest":
                return JsonResponse({"success": False, "message": errors}, status=400)

    return render(request, "appOne/configuracion/seguridad.html")