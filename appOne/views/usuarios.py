from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from appOne.models import Usuario, BitacoraAuditoria, Notificacion
from .utils import es_administrador, registrar_auditoria

@login_required
def panel_usuarios(request):
    if not es_administrador(request.user):
        messages.error(request, "No tienes permisos para acceder a la gestión de usuarios.")
        return redirect('dashboardinicio')

    buscar = request.GET.get('buscar', '').strip()
    rol = request.GET.get('rol', '').strip()
    estado = request.GET.get('estado', '').strip()

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
    if not es_administrador(request.user):
        messages.error(request, "No tienes permiso para realizar esta acción.")
        return redirect('dashboardinicio')

    usuario = get_object_or_404(Usuario, id=id)

    if usuario.is_active:
        messages.info(request, f"El usuario '{usuario.nombre_completo}' ya se encuentra activo.")
        return redirect('panel_usuarios')

    usuario.is_active = True
    usuario.save()

    registrar_auditoria(
        request, 
        BitacoraAuditoria.ACCION_EDITAR, 
        "Usuarios", 
        usuario.id, 
        f"Aprobación de usuario: {usuario.nombre_completo}"
    )

    Notificacion.objects.create(
        usuario=usuario,
        titulo="Cuenta Aprobada",
        mensaje="Tu solicitud de acceso ha sido aprobada. Ya puedes utilizar todas las funciones del sistema.",
        tipo=Notificacion.TIPO_INFO
    )

    messages.success(request, f"Usuario '{usuario.nombre_completo}' aprobado exitosamente. Ya puede iniciar sesión.")
    return redirect('panel_usuarios')


@login_required
def rechazar_usuario(request, id):
    if not es_administrador(request.user):
        messages.error(request, "No tienes permiso para realizar esta acción.")
        return redirect('dashboardinicio')

    usuario = get_object_or_404(Usuario, id=id)

    if usuario == request.user:
        messages.error(request, "No puedes deshabilitar tu propia cuenta.")
        return redirect('panel_usuarios')

    usuario.is_active = False
    usuario.save()

    registrar_auditoria(
        request, 
        BitacoraAuditoria.ACCION_EDITAR, 
        "Usuarios", 
        usuario.id, 
        f"Rechazo/Desactivación de usuario: {usuario.nombre_completo}"
    )

    messages.warning(request, f"La solicitud/cuenta de {usuario.nombre_completo} ha sido inhabilitada.")
    return redirect('panel_usuarios')


@login_required
def eliminar_usuario(request, id):
    if not es_administrador(request.user):
        messages.error(request, "No tienes permisos para eliminar usuarios.")
        return redirect('dashboardinicio')

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