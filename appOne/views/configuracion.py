from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib import messages
from django.http import JsonResponse
from appOne.models import Usuario, Dispositivo, Prestamo, BitacoraAuditoria
from .utils import es_administrador, registrar_auditoria

@login_required
def panel_config(request):
    if not es_administrador(request.user):
        messages.error(request, "No tienes permisos para acceder a este panel.")
        return redirect('dashboardinicio')

    return render(request, 'appOne/panel_config.html')

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
    if not es_administrador(request.user):
        return JsonResponse({"error": "No autorizado"}, status=403)
    return render(request, "appOne/configuracion/database.html")


@login_required
def config_perfil(request):
    if request.method == "POST":
        user = request.user
        first_name = request.POST.get("first_name", "").strip()
        last_name = request.POST.get("last_name", "").strip()
        email = request.POST.get("email", "").strip()

        if email and Usuario.objects.exclude(pk=user.pk).filter(correo_institucional=email).exists():
            if request.headers.get("x-requested-with") == "XMLHttpRequest":
                return JsonResponse({"success": False, "message": "El correo ingresado ya está en uso por otro usuario."}, status=400)
            messages.error(request, "El correo ya pertenece a otro usuario.")
            return render(request, "appOne/configuracion/perfil.html")

        user.first_name = first_name
        user.last_name = last_name
        if email:
            user.correo_institucional = email
            user.email = email
        user.nombre_completo = f"{first_name} {last_name}".strip() if (first_name or last_name) else user.nombre_completo
        user.save()

        registrar_auditoria(request, BitacoraAuditoria.ACCION_EDITAR, "Perfil", user.id, "Actualización de información de perfil")

        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({"success": True, "message": "Perfil actualizado correctamente."})

        messages.success(request, "Perfil actualizado correctamente.")

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

            messages.success(request, "Contraseña actualizada con éxito.")
        else:
            errors = "; ".join([f"{', '.join(v)}" for k, v in form.errors.items()])
            if request.headers.get("x-requested-with") == "XMLHttpRequest":
                return JsonResponse({"success": False, "message": errors}, status=400)
            messages.error(request, f"Error al cambiar contraseña: {errors}")

    return render(request, "appOne/configuracion/seguridad.html")
