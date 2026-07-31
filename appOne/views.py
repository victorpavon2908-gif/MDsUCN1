from datetime import datetime, timedelta
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
from .models import Usuario, Dispositivo, Prestamo, BitacoraAuditoria


# ============================
# HELPER DE AUDITORÍA
# ============================
def registrar_auditoria(request, accion, tabla_afectada, registro_id=None, detalles=None):
    """Registra una acción realizada por el usuario en la bitácora."""
    ip = request.META.get('REMOTE_ADDR')
    user = request.user if request.user.is_authenticated else None
    
    BitacoraAuditoria.objects.create(
        usuario=user,
        accion=accion,
        tabla_afectada=tabla_afectada,
        registro_id=registro_id,
        detalles=detalles,
        ip_origen=ip
    )


# ============================
# ----- LOGIN / LOGOUT -------
# ============================
def login_view(request):
    if request.method == "POST":
        correo = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, correo_institucional=correo, password=password)

        if user is not None:
            if not user.is_active:
                messages.error(request, "Tu cuenta está registrada pero aún pendiente de aprobación por el administrador.")
                return render(request, "appOne/login.html")

            login(request, user)
            registrar_auditoria(request, BitacoraAuditoria.ACCION_LOGIN, "Autenticación", user.id, "Inicio de sesión exitoso")
            messages.success(request, f"¡Bienvenido de nuevo, {user.nombre_completo}!")
            return redirect('dashboardinicio')
        else:
            messages.error(request, "Usuario o contraseña incorrectos.")

    return render(request, "appOne/login.html")


def logout_view(request):
    if request.user.is_authenticated:
        registrar_auditoria(request, BitacoraAuditoria.ACCION_LOGOUT, "Autenticación", request.user.id, "Cierre de sesión")
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

            registrar_auditoria(request, BitacoraAuditoria.ACCION_CREAR, "Usuarios", usuario.id, f"Registro de nuevo usuario pendiente de aprobación: {usuario.correo_institucional}")

            messages.success(
                request, 
                "Solicitud de registro recibida. Se ha enviado una notificación al administrador para su aprobación."
            )
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

    return render(request, "appOne/dashboard.html", {
        "perfil": usuario,
    })


@login_required
def layaut_Principal(request):
    total_usuarios = Usuario.objects.filter(is_active=True).count()
    prestamos_activos = Prestamo.objects.filter(estado=Prestamo.ESTADO_APROBADO).count()
    dispositivos_disponibles = Dispositivo.objects.filter(estado=Dispositivo.ESTADO_DISPONIBLE).count()
    pendientes_count = Prestamo.objects.filter(estado=Prestamo.ESTADO_PENDIENTE).count()

    if request.user.rol == "Admin" or request.user.is_superuser:
        ultimos_prestamos = Prestamo.objects.select_related('usuario', 'dispositivo').order_by('-fecha_solicitud')[:5]
    else:
        ultimos_prestamos = Prestamo.objects.select_related('usuario', 'dispositivo').filter(usuario=request.user).order_by('-fecha_solicitud')[:5]

    context = {
        'estadisticas': {
            'usuarios': total_usuarios,
            'prestamos': prestamos_activos,
            'disponibles': dispositivos_disponibles,
        },
        'pendientes_count': pendientes_count,
        'ultimos_prestamos': ultimos_prestamos,
    }

    return render(request, 'appOne/layaut_Principal.html', context)


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


@login_required
def aprobar_usuario(request, id):
    if request.user.rol != "Admin" and not request.user.is_superuser:
        messages.error(request, "No tienes permiso para realizar esta acción.")
        return redirect('dashboard')

    usuario = get_object_or_404(Usuario, id=id)
    usuario.is_active = True
    usuario.save()

    registrar_auditoria(request, BitacoraAuditoria.ACCION_EDITAR, "Usuarios", usuario.id, f"Aprobación de usuario: {usuario.nombre_completo}")

    messages.success(request, f"Usuario '{usuario.nombre_completo}' aprobado exitosamente. Ya puede iniciar sesión.")
    return redirect('panel_usuarios')


@login_required
def rechazar_usuario(request, id):
    if request.user.rol != "Admin" and not request.user.is_superuser:
        messages.error(request, "No tienes permiso para realizar esta acción.")
        return redirect('dashboard')

    usuario = get_object_or_404(Usuario, id=id)
    usuario.is_active = False
    usuario.save()

    registrar_auditoria(request, BitacoraAuditoria.ACCION_EDITAR, "Usuarios", usuario.id, f"Rechazo de usuario: {usuario.nombre_completo}")

    messages.warning(request, f"La solicitud de {usuario.nombre_completo} ha sido rechazada.")
    return redirect('panel_usuarios')


@login_required
def eliminar_usuario(request, id):
    if request.user.rol != "Admin" and not request.user.is_superuser:
        messages.error(request, "No tienes permisos para eliminar usuarios.")
        return redirect('dashboard')

    usuario = get_object_or_404(Usuario, id=id)

    if usuario == request.user:
        messages.error(request, "No puedes eliminar tu propia cuenta.")
        return redirect('panel_usuarios')

    detalles = f"Eliminación de usuario: {usuario.nombre_completo} ({usuario.correo_institucional})"
    usuario_id = usuario.id
    usuario.delete()

    registrar_auditoria(request, BitacoraAuditoria.ACCION_ELIMINAR, "Usuarios", usuario_id, detalles)

    messages.warning(request, "Usuario eliminado correctamente.")
    return redirect('panel_usuarios')


# ============================
# --- DISPOSITIVOS (CRUD) ----
# ============================
@login_required
def listardispositivos(request):
    ids_ocupados = Prestamo.objects.filter(
        estado__in=[Prestamo.ESTADO_PENDIENTE, Prestamo.ESTADO_APROBADO]
    ).values_list('dispositivo_id', flat=True)

    dispositivos_disponibles = Dispositivo.objects.filter(
        estado=Dispositivo.ESTADO_DISPONIBLE
    ).exclude(id__in=ids_ocupados)

    dispositivos_ocupados = Dispositivo.objects.filter(
        id__in=ids_ocupados
    )

    dispositivos_mantenimiento = Dispositivo.objects.filter(
        estado=Dispositivo.ESTADO_MANTENIMIENTO
    )

    dispositivos_danados = Dispositivo.objects.filter(
        estado=Dispositivo.ESTADO_DANADO
    )

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
            dispositivo = form.save()
            registrar_auditoria(request, BitacoraAuditoria.ACCION_CREAR, "Dispositivos", dispositivo.id, f"Nuevo dispositivo creado: {dispositivo.nombre_dispositivo} ({dispositivo.codigo_inventario})")
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
            registrar_auditoria(request, BitacoraAuditoria.ACCION_EDITAR, "Dispositivos", dispositivo.id, f"Edición de dispositivo: {dispositivo.nombre_dispositivo}")
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
    detalles = f"Eliminación de dispositivo: {dispositivo.nombre_dispositivo} ({dispositivo.codigo_inventario})"
    disp_id = dispositivo.id
    dispositivo.delete()

    registrar_auditoria(request, BitacoraAuditoria.ACCION_ELIMINAR, "Dispositivos", disp_id, detalles)

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

        if dispositivo.estado != Dispositivo.ESTADO_DISPONIBLE:
            msg = f"No es posible solicitar este equipo. Estado actual: {dispositivo.get_estado_display()}."
            if is_ajax:
                return JsonResponse({"success": False, "message": msg}, status=400)
            messages.error(request, msg)
            return redirect("listardispositivos")

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

            registrar_auditoria(request, BitacoraAuditoria.ACCION_CREAR, "Préstamos", nuevo_prestamo.id, f"Solicitud de préstamo enviada para el dispositivo: {dispositivo.nombre_dispositivo}")

            messages.success(request, "Solicitud enviada correctamente. Notificación generada para el administrador.")
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

    prestamo.estado = Prestamo.ESTADO_APROBADO
    if hasattr(prestamo, 'fecha_aprobacion'):
        prestamo.fecha_aprobacion = timezone.now()
    prestamo.save()

    dispositivo = prestamo.dispositivo
    dispositivo.estado = Dispositivo.ESTADO_PRESTADO
    dispositivo.save()

    registrar_auditoria(request, BitacoraAuditoria.ACCION_EDITAR, "Préstamos", prestamo.id, f"Aprobación de préstamo de {dispositivo.nombre_dispositivo} a {prestamo.usuario.nombre_completo}")

    messages.success(
        request, 
        f"Préstamo del equipo '{dispositivo.nombre_dispositivo}' aprobado para {prestamo.usuario.nombre_completo}."
    )
    return redirect("solicitudes_prestamos")


@login_required
def rechazar_prestamo(request, id):
    if request.user.rol != "Admin" and not request.user.is_superuser:
        return redirect('dashboard')

    prestamo = get_object_or_404(Prestamo, id=id)
    prestamo.estado = Prestamo.ESTADO_RECHAZADO
    prestamo.save()

    registrar_auditoria(request, BitacoraAuditoria.ACCION_EDITAR, "Préstamos", prestamo.id, f"Rechazo de préstamo de {prestamo.dispositivo.nombre_dispositivo} a {prestamo.usuario.nombre_completo}")

    messages.error(request, f"La solicitud del equipo '{prestamo.dispositivo.nombre_dispositivo}' ha sido rechazada.")
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

        prestamo.estado = Prestamo.ESTADO_DEVUELTO
        prestamo.fecha_devolucion_real = timezone.now()
        prestamo.observaciones_devolucion = observaciones
        prestamo.save()

        dispositivo = prestamo.dispositivo
        dispositivo.estado = estado_dispositivo
        dispositivo.save()

        registrar_auditoria(request, BitacoraAuditoria.ACCION_EDITAR, "Préstamos", prestamo.id, f"Devolución registrada de {dispositivo.nombre_dispositivo}. Nuevo estado: {estado_dispositivo}")

        if estado_dispositivo == Dispositivo.ESTADO_DANADO:
            messages.warning(request, f"Devolución registrada. '{dispositivo.nombre_dispositivo}' marcado como 'Dañado'.")
        elif estado_dispositivo == Dispositivo.ESTADO_MANTENIMIENTO:
            messages.warning(request, f"Devolución registrada. '{dispositivo.nombre_dispositivo}' pasó a 'Mantenimiento'.")
        else:
            messages.success(request, f"Devolución completada. '{dispositivo.nombre_dispositivo}' reincorporado como 'Disponible'.")

        return redirect("solicitudes_prestamos")

    return redirect("solicitudes_prestamos")


# ============================
# --- GESTIÓN SOLICITUDES ----
# ============================
@login_required
def solicitudes_prestamos(request):
    estado = request.GET.get("estado")
    estado_actual = estado if estado else "todos"

    if estado_actual == "todos" and request.session.get("ocultar_todos", False):
        prestamos = Prestamo.objects.none()
    else:
        if request.user.rol == "Admin" or request.user.is_superuser:
            prestamos = Prestamo.objects.select_related('usuario', 'dispositivo').all()
        else:
            prestamos = Prestamo.objects.select_related('usuario', 'dispositivo').filter(usuario=request.user)

        if estado_actual != "todos":
            prestamos = prestamos.filter(estado=estado_actual)

        prestamos = prestamos.order_by("-fecha_solicitud")

    return render(request, "appOne/solicitudes.html", {
        "prestamos": prestamos,
        "estado_actual": estado_actual
    })


@login_required
def eliminar_historial_prestamos(request):
    if request.method == "POST" and (request.user.rol == "Admin" or request.user.is_superuser):
        request.session["ocultar_todos"] = True
        messages.success(request, "Vista limpia.")

    return redirect(request.META.get("HTTP_REFERER", "solicitudes_prestamos"))


@login_required
def restaurar_historial_todos(request):
    if "ocultar_todos" in request.session:
        del request.session["ocultar_todos"]
        messages.info(request, "Historial restaurado.")
    return redirect(request.META.get("HTTP_REFERER", "solicitudes_prestamos"))


# ============================
# --------- AUDITORÍA ---------
# ============================
@login_required
def bitacora_auditoria(request):
    """Muestra el historial completo de eventos y operaciones en el sistema."""
    if request.user.rol != "Admin" and not request.user.is_superuser:
        messages.error(request, "No tienes permisos para consultar la bitácora de auditoría.")
        return redirect('dashboardinicio')

    logs = BitacoraAuditoria.objects.all().select_related('usuario').order_by('-fecha_hora')[:200]
    return render(request, 'appOne/bitacora_auditoria.html', {'logs': logs})


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

    # CORRECCIÓN: Obtener los últimos 10 eventos de la bitácora para el template reportes.html
    logs = BitacoraAuditoria.objects.all().select_related('usuario').order_by('-fecha_hora')[:10]

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
        'logs': logs,  # Pasamos los registros al contexto
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
    if request.method == "POST":
        user = request.user
        user.first_name = request.POST.get("first_name", "").strip()
        user.last_name = request.POST.get("last_name", "").strip()
        user.email = request.POST.get("email", "").strip()
        user.save()

        registrar_auditoria(request, BitacoraAuditoria.ACCION_EDITAR, "Perfil", user.id, "Actualización de información de perfil")

        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({"success": True, "message": "Perfil actualizado correctamente."})

    return render(request, "appOne/configuracion/perfil.html")


@login_required
def config_seguridad(request):
    if request.method == "POST":
        form = PasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)

            registrar_auditoria(request, BitacoraAuditoria.ACCION_EDITAR, "Seguridad", user.id, "Cambio de contraseña exitoso")

            if request.headers.get("x-requested-with") == "XMLHttpRequest":
                return JsonResponse({"success": True, "message": "Contraseña actualizada con éxito."})
        else:
            errors = "; ".join([f"{', '.join(v)}" for k, v in form.errors.items()])
            if request.headers.get("x-requested-with") == "XMLHttpRequest":
                return JsonResponse({"success": False, "message": errors}, status=400)

    return render(request, "appOne/configuracion/seguridad.html")


# ============================
# ------- CALENDARIO ---------
# ============================
@login_required
def calendario_reservas(request):
    return render(request, 'appOne/calendario.html')


@login_required
def api_reservas_eventos(request):
    es_admin = getattr(request.user, 'rol', '') == 'Admin' or request.user.is_superuser
    
    if es_admin:
        prestamos = Prestamo.objects.select_related('dispositivo', 'usuario').all()
    else:
        prestamos = Prestamo.objects.select_related('dispositivo', 'usuario').filter(usuario=request.user)

    eventos = []
    
    color_map = {
        'Pendiente': '#f57c00',
        'Aprobado': '#2e7d32',
        'Rechazado': '#d32f2f',
        'Devuelto': '#616161',
        'Finalizado': '#616161'
    }

    for p in prestamos:
        nombre_usuario = getattr(p.usuario, 'nombre_completo', p.usuario.username)
        if es_admin:
            titulo = f"{p.dispositivo.nombre_dispositivo} - {nombre_usuario}"
        else:
            titulo = f"{p.dispositivo.nombre_dispositivo} ({p.get_estado_display()})"

        start_iso = None
        end_iso = None

        if hasattr(p, 'fecha_uso') and p.fecha_uso:
            if hasattr(p, 'hora_inicio') and p.hora_inicio:
                start_iso = f"{p.fecha_uso.isoformat()}T{p.hora_inicio.isoformat()}"
            else:
                start_iso = p.fecha_uso.isoformat()

            if hasattr(p, 'hora_entrega') and p.hora_entrega:
                end_iso = f"{p.fecha_uso.isoformat()}T{p.hora_entrega.isoformat()}"
        elif hasattr(p, 'fecha_solicitud') and p.fecha_solicitud:
            start_iso = p.fecha_solicitud.isoformat()

        eventos.append({
            'id': p.id,
            'title': titulo,
            'start': start_iso,
            'end': end_iso,
            'backgroundColor': color_map.get(p.estado, '#1976d2'),
            'borderColor': color_map.get(p.estado, '#1976d2'),
            'extendedProps': {
                'estado': p.get_estado_display(),
                'dispositivo': p.dispositivo.nombre_dispositivo,
                'usuario': nombre_usuario,
                'motivo': getattr(p, 'motivo', '')
            }
        })

    return JsonResponse(eventos, safe=False)