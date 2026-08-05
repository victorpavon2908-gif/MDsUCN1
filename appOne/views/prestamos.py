
from datetime import datetime, time
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.db.models import Q

from appOne.models import Usuario, Dispositivo, Prestamo, BitacoraAuditoria, Notificacion
from .utils import es_administrador, registrar_auditoria

# ============================
# -------- PRÉSTAMOS ---------
# ============================

@login_required
def modal_prestamo(request, id):
    dispositivo = get_object_or_404(Dispositivo, id=id)
    fecha_str = request.GET.get('fecha_uso', timezone.now().date().strftime('%Y-%m-%d'))
    
    try:
        fecha_dt = datetime.strptime(fecha_str, '%Y-%m-%d').date()
    except ValueError:
        fecha_dt = timezone.now().date()
        fecha_str = fecha_dt.strftime('%Y-%m-%d')

    reservas = Prestamo.objects.filter(
        dispositivo=dispositivo,
        fecha_uso=fecha_dt,
        estado__in=[Prestamo.ESTADO_PENDIENTE, Prestamo.ESTADO_APROBADO]
    ).select_related('usuario').order_by('hora_inicio')

    horarios_tabla = []
    
    for h in range(8, 17):
        h_inicio = time(h, 0)
        h_fin = time(h + 1, 0)
        
        reserva_coincidente = None
        for r in reservas:
            if r.hora_inicio < h_fin and r.hora_entrega > h_inicio:
                reserva_coincidente = r
                break
        
        horarios_tabla.append({
            'rango': f"{h:02d}:00 - {h+1:02d}:00",
            'hora_inicio': h_inicio,
            'hora_fin': h_fin,
            'ocupado': reserva_coincidente is not None,
            'reserva': reserva_coincidente
        })

    return render(request, "appOne/modal_prestamo.html", {
        "dispositivo": dispositivo,
        "reservas": reservas,
        "horarios_tabla": horarios_tabla,
        "fecha_seleccionada": fecha_str
    })


@login_required
def crear_prestamo(request):
    is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'

    if request.method == "POST":
        dispositivo_id = request.POST.get("dispositivo_id")
        
        if not dispositivo_id:
            msg = "Dispositivo no especificado."
            return JsonResponse({"success": False, "message": msg}, status=400) if is_ajax else redirect("listardispositivos")

        dispositivo = get_object_or_404(Dispositivo, id=dispositivo_id)

        if dispositivo.estado not in [Dispositivo.ESTADO_DISPONIBLE]:
            msg = f"No es posible solicitar este equipo. Estado actual: {dispositivo.get_estado_display()}."
            if is_ajax:
                return JsonResponse({"success": False, "message": msg}, status=400)
            messages.error(request, msg)
            return redirect("listardispositivos")

        motivo = request.POST.get("motivo", "").strip()
        fecha_uso = request.POST.get("fecha_uso")
        hora_inicio = request.POST.get("hora_inicio")
        hora_entrega = request.POST.get("hora_entrega")

        if not all([motivo, fecha_uso, hora_inicio, hora_entrega]):
            msg = "Todos los campos (motivo, fecha de uso, hora inicio y entrega) son obligatorios."
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

            registrar_auditoria(
                request, 
                BitacoraAuditoria.ACCION_CREAR, 
                "Préstamos", 
                nuevo_prestamo.id, 
                f"Solicitud de préstamo enviada para el dispositivo: {dispositivo.nombre_dispositivo}"
            )

            # Generar notificación a administradores
            admins = Usuario.objects.filter(Q(rol="Admin") | Q(is_superuser=True), is_active=True)
            for admin in admins:
                Notificacion.objects.create(
                    usuario=admin,
                    titulo="Nueva Solicitud de Préstamo",
                    mensaje=f"{request.user.nombre_completo} ha solicitado el equipo '{dispositivo.nombre_dispositivo}' para la fecha {fecha_uso}.",
                    tipo=Notificacion.TIPO_ALERTA
                )

            if is_ajax:
                return JsonResponse({"success": True, "message": "Solicitud enviada exitosamente."})

            messages.success(request, "Solicitud enviada correctamente. Notificación generada para el administrador.")
            return redirect("listardispositivos")

        except ValidationError as e:
            if hasattr(e, 'message_dict'):
                mensajes_limpios = []
                for field, msgs in e.message_dict.items():
                    mensajes_limpios.extend(msgs)
                error_msg = " ".join(mensajes_limpios)
            else:
                error_msg = ", ".join(e.messages)

            if is_ajax:
                return JsonResponse({"success": False, "message": error_msg}, status=400)

            messages.error(request, f"Error al procesar la solicitud: {error_msg}")
            return redirect("listardispositivos")

    return redirect("listardispositivos")


@login_required
def aprobar_prestamo(request, id):
    if not es_administrador(request.user):
        messages.error(request, "No tienes permiso para aprobar solicitudes.")
        return redirect("solicitudes_prestamos")

    prestamo = get_object_or_404(Prestamo, id=id)

    if prestamo.estado != Prestamo.ESTADO_PENDIENTE:
        messages.warning(request, f"La solicitud ya ha sido procesada previamente ({prestamo.get_estado_display()}).")
        return redirect("solicitudes_prestamos")

    prestamo.estado = Prestamo.ESTADO_APROBADO
    prestamo.save()

    registrar_auditoria(
        request, 
        BitacoraAuditoria.ACCION_EDITAR, 
        "Préstamos", 
        prestamo.id, 
        f"Aprobación de préstamo de {prestamo.dispositivo.nombre_dispositivo} para {prestamo.usuario.nombre_completo}"
    )

    Notificacion.objects.create(
        usuario=prestamo.usuario,
        titulo="Préstamo Aprobado",
        mensaje=f"Tu reserva de '{prestamo.dispositivo.nombre_dispositivo}' para el {prestamo.fecha_uso} ha sido APROBADA.",
        tipo=Notificacion.TIPO_INFO
    )

    messages.success(request, f"Préstamo para '{prestamo.usuario.nombre_completo}' aprobado con éxito.")
    return redirect("solicitudes_prestamos")


@login_required
def rechazar_prestamo(request, id):
    if not es_administrador(request.user):
        messages.error(request, "No tienes permiso para rechazar solicitudes.")
        return redirect('solicitudes_prestamos')

    prestamo = get_object_or_404(Prestamo, id=id)

    if prestamo.estado != Prestamo.ESTADO_PENDIENTE:
        messages.warning(request, f"Esta solicitud ya se encontraba en estado {prestamo.get_estado_display()}.")
        return redirect("solicitudes_prestamos")

    prestamo.estado = Prestamo.ESTADO_RECHAZADO
    prestamo.save()

    registrar_auditoria(
        request, 
        BitacoraAuditoria.ACCION_EDITAR, 
        "Préstamos", 
        prestamo.id, 
        f"Rechazo de préstamo de {prestamo.dispositivo.nombre_dispositivo} a {prestamo.usuario.nombre_completo}"
    )

    Notificacion.objects.create(
        usuario=prestamo.usuario,
        titulo="Préstamo Rechazado",
        mensaje=f"Tu solicitud del equipo '{prestamo.dispositivo.nombre_dispositivo}' programada para el {prestamo.fecha_uso} ha sido rechazada.",
        tipo=Notificacion.TIPO_ALERTA
    )

    messages.error(request, f"La solicitud del equipo '{prestamo.dispositivo.nombre_dispositivo}' ha sido rechazada.")
    return redirect('solicitudes_prestamos')


@login_required
def devolver_prestamo(request, id):
    if not es_administrador(request.user):
        messages.error(request, "No tienes permisos para registrar devoluciones.")
        return redirect("solicitudes_prestamos")

    prestamo = get_object_or_404(Prestamo, id=id)

    if prestamo.estado != Prestamo.ESTADO_APROBADO:
        messages.warning(request, "Este préstamo no está en estado 'Aprobado' para ser devuelto.")
        return redirect("solicitudes_prestamos")

    if request.method == "POST":
        observaciones = request.POST.get("observaciones_devolucion", "").strip()
        estado_dispositivo = request.POST.get("estado_dispositivo", Dispositivo.ESTADO_DISPONIBLE)

        prestamo.estado = Prestamo.ESTADO_DEVUELTO
        prestamo.fecha_devolucion_real = timezone.now()
        prestamo.observaciones_devolucion = observaciones
        prestamo.save()

        # Actualización explícita del estado del dispositivo
        dispositivo = prestamo.dispositivo
        dispositivo.estado = estado_dispositivo
        dispositivo.save()

        registrar_auditoria(
            request, 
            BitacoraAuditoria.ACCION_EDITAR, 
            "Préstamos", 
            prestamo.id, 
            f"Devolución registrada de {dispositivo.nombre_dispositivo}. Nuevo estado equipo: {estado_dispositivo}"
        )

        Notificacion.objects.create(
            usuario=prestamo.usuario,
            titulo="Devolución Confirmada",
            mensaje=f"Se ha completado la devolución del equipo '{dispositivo.nombre_dispositivo}'. ¡Gracias!",
            tipo=Notificacion.TIPO_INFO
        )

        messages.success(request, f"Devolución completada para '{dispositivo.nombre_dispositivo}'.")
        return redirect("solicitudes_prestamos")

    return redirect("solicitudes_prestamos")

# ============================
# --- GESTIÓN SOLICITUDES ----
# ============================

@login_required
def solicitudes_prestamos(request):
    estado = request.GET.get("estado", "todos").strip()

    if estado == "todos" and request.session.get("ocultar_todos", False):
        prestamos = Prestamo.objects.none()
    else:
        if es_administrador(request.user):
            prestamos = Prestamo.objects.select_related('usuario', 'dispositivo').all()
        else:
            prestamos = Prestamo.objects.select_related('usuario', 'dispositivo').filter(usuario=request.user)

        if estado != "todos":
            prestamos = prestamos.filter(estado=estado)

        prestamos = prestamos.order_by("-fecha_solicitud")

    return render(request, "appOne/solicitudes.html", {
        "prestamos": prestamos,
        "estado_actual": estado
    })


@login_required
def eliminar_historial_prestamos(request):
    if request.method == "POST" and es_administrador(request.user):
        request.session["ocultar_todos"] = True
        messages.success(request, "Vista despejada correctamente.")

    return redirect(request.META.get("HTTP_REFERER", "solicitudes_prestamos"))


@login_required
def restaurar_historial_todos(request):
    if "ocultar_todos" in request.session:
        del request.session["ocultar_todos"]
        messages.info(request, "Historial restaurado en la vista.")
    return redirect(request.META.get("HTTP_REFERER", "solicitudes_prestamos"))
